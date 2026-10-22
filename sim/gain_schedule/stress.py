"""Bounded reduced-model stress study with a fixed, nominal-only observer.

Simulation only. One fresh nominal augmented DARE, no gain scheduling, training,
or uncertainty-aware redesign. Existing evaluation owns every strict check.
"""

import argparse
from copy import deepcopy
import csv
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET

# Set before NumPy/SciPy imports, including when invoked directly as a module.
THREAD_VARIABLES = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
                    "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")
for _name in THREAD_VARIABLES:
    os.environ[_name] = "1"

import mujoco
import numpy as np

from sim.augmented import AugmentedRuntime, lag_interval, load_experiment
from sim.augmented_eval import evaluate
from sim.augmented_lqr import synthesize_augmented
from sim.planar import Plant, make_mjcf


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "sim/configs/assumed_actuator_noise.json"
MAX_CASES = 60
LIMITATION = ("Conditional sampled reduced-model candidate stress baseline; not a "
              "PPO v2 result, hardware uncertainty range, five-bar validation, "
              "monotonicity proof or universal robustness radius.")
OBSERVER = {
    "design_length_m": .16, "design_delay_s": .002, "dt_s": .002,
    "motor_time_constant_s": [.005, .005], "zero_initial_torque_and_history": True,
    "feedback": "measurement[6], own estimated torque[2], own previous clipped command[2]",
    "update": "raw=-K@[measurement,tau_hat,u_prev]; tau_hat_next=lag_interval(tau_hat,u_prev,T,dt).endpoint; u_prev_next=clip(raw)",
    "hidden": "actual delay, mass, wheel map, physical torque/truth and runtime estimate/history",
    "runtime_csv_note": "control.csv runtime observation extras are diagnostics, NOT controller inputs; observer.csv records actual feedback",
}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class DesignObserverController:
    """One call per control tick; a new instance per reset/rollout.

    At t_k the filter has evolved through [t_(k-1),t_k] under u_(k-2).
    The next interval uses u_(k-1), since assumed delay equals one period.
    Only obs.measurement is read; no runtime state or timing metadata is used.
    """

    def __init__(self, gain, limits, audit=None):
        self.gain = np.array(gain, dtype=float, copy=True)
        self.limits = np.array(limits, dtype=float, copy=True)
        if self.gain.shape != (2, 10) or not np.all(np.isfinite(self.gain)):
            raise ValueError("The fixed design must be finite 2x10 (2 ms assumption)")
        if self.limits.shape != (2,) or np.any(self.limits <= 0):
            raise ValueError("Two positive nominal torque limits required")
        self.gain.setflags(write=False)
        self.estimated_tau = np.zeros(2)
        self.previous_clipped = np.zeros(2)
        self.tick = 0
        self.audit = audit

    def __call__(self, obs):
        measured = np.asarray(obs.measurement, dtype=float)
        if measured.shape != (6,) or not np.all(np.isfinite(measured)):
            raise ValueError("Finite six-state measurement required")
        z = np.r_[measured, self.estimated_tau, self.previous_clipped]
        raw = -self.gain @ z
        clipped = np.clip(raw, -self.limits, self.limits)
        if self.audit is not None:
            self.audit.writerow([self.tick, *z, *raw, *clipped])
        self.estimated_tau = lag_interval(
            self.estimated_tau, self.previous_clipped, (.005, .005), .002)[0]
        self.previous_clipped = clipped.copy()
        self.tick += 1
        # Let the unchanged evaluator see the raw request for saturation metrics.
        return raw


@dataclass(frozen=True)
class Condition:
    push_N: float = 6.
    delay_s: float = .002
    mass_scale: float = 1.
    wheel_delta: float = 0.
    seed: int = 0

    def __post_init__(self):
        values = (self.push_N, self.delay_s, self.mass_scale, self.wheel_delta)
        if (not all(np.isfinite(v) for v in values) or self.push_N <= 0 or
                self.delay_s < 0 or self.mass_scale <= 0 or self.seed not in range(5)):
            raise ValueError("Invalid stress condition")


def actual_config(nominal, condition):
    cfg = deepcopy(nominal)
    cfg["protocol"]["push_force_N"] = condition.push_N
    for name in ("body_mass", "body_inertia"):
        cfg["physics"][name]["value"] *= condition.mass_scale
        cfg["physics"][name]["source"] += f"; synthetic stress scale {condition.mass_scale:g}"
    return cfg


class PerturbedPlant(Plant):
    """Instance-local wheel reaction redistribution in existing MJCF.

    q_joint = [x, theta, phi-theta]. Joint wheel force [1/r,-1,-delta]
    maps by TO_JOINT.T to [1/r,-1+delta,-delta]. Hip stays [0,-1,1].
    """

    def __init__(self, cfg, delta):
        self.cfg = deepcopy(cfg)
        tree = ET.fromstring(make_mjcf(self.cfg))
        tendon = tree.find("./tendon/fixed[@name='wheel_relative_rotation']")
        ET.SubElement(tendon, "joint", joint="hip_pitch", coef=str(-delta))
        self.xml = ET.tostring(tree, encoding="unicode")
        self.model = mujoco.MjModel.from_xml_string(self.xml)
        self.body_id = self.model.body("body").id
        self.limits = self.model.actuator_ctrlrange[:, 1].copy()


def make_runtime(nominal, effects, condition):
    cfg = actual_config(nominal, condition)
    runtime = AugmentedRuntime(cfg, replace(effects, delay_s=condition.delay_s))
    # Replace only this runtime's plant; reset creates matching MjData immediately.
    runtime.plant = PerturbedPlant(cfg, condition.wheel_delta)
    runtime.reset(seed=condition.seed)
    return runtime


def bounded_plan(run):
    """At most 57 unique cases, including all seed confirmations and bisections.

    run caches identical physical conditions, reusing nominal and seed-0 records.
    Only the push search stops at first FAIL. Other axes cover their declared
    finite grids; optional mass 4/8 is used only if smaller factors all PASS.
    """
    axes = {}
    nominal = run(Condition())  # Required first measured case.

    def axis(name, field, values):
        rows = [run(replace(Condition(), **{field: value})) for value in values]
        axes[name] = {"field": field, "seed0": rows, "confirmations": []}
        return axes[name]

    push = {"field": "push_N", "seed0": [nominal], "confirmations": []}
    axes["push"] = push
    if nominal["status"] == "PASS":
        for value in (12., 24., 48., 96.):
            row = run(Condition(push_N=value))
            push["seed0"].append(row)
            if row["status"] != "PASS":
                break
    if len(push["seed0"]) > 1 and push["seed0"][-1]["status"] == "FAIL":
        lo, hi = push["seed0"][-2:]
        for _ in range(3):
            midpoint = (lo["condition"]["push_N"] + hi["condition"]["push_N"]) / 2
            row = run(Condition(push_N=midpoint))
            push["seed0"].append(row)
            if row["status"] == "PASS":
                lo = row
            elif row["status"] == "FAIL":
                hi = row
            else:
                break

    def confirm(panel):
        field = panel["field"]
        rows = sorted(panel["seed0"], key=lambda r: r["condition"][field])
        pair = next(([left, right] for left, right in zip(rows, rows[1:])
                     if {left["status"], right["status"]} == {"PASS", "FAIL"}), None)
        if pair is None:
            pair = rows[-2:]
        panel["confirmation_basis"] = (
            "first adjacent sampled PASS/FAIL pair in increasing axis order" if
            len(pair) == 2 and {r["status"] for r in pair} == {"PASS", "FAIL"} else
            "largest sampled endpoint(s); no adjacent PASS/FAIL pair")
        for row in pair:
            if row["status"] not in ("PASS", "FAIL"):
                continue
            condition = Condition(**row["condition"])
            panel["confirmations"].append({
                "value": row["condition"][field],
                "cases": [row, *[run(replace(condition, seed=seed)) for seed in range(1, 5)]],
            })
        panel["first_tested_failure"] = next(
            (r for r in panel["seed0"] if r["status"] == "FAIL"), None)
        panel["result"] = ("FAILURE_OBSERVED" if any(r["status"] == "FAIL" for r in panel["seed0"])
                           else "INCOMPLETE" if any(r["status"] == "ERROR" for r in panel["seed0"])
                           else "NO_FAILURE_OBSERVED")
        panel["confirmation_failures"] = sum(r["status"] == "FAIL"
            for group in panel["confirmations"] for r in group["cases"])
        if panel["confirmation_failures"]:
            panel["result"] = "FAILURE_OBSERVED"
        if any(r["status"] == "ERROR" for g in panel["confirmations"] for r in g["cases"]):
            panel["result"] = "INCOMPLETE"

    confirm(push)
    delay = axis("delay", "delay_s", (.002, .005, .006, .007, .008, .009, .010))
    confirm(delay)
    mass = axis("mass", "mass_scale", (.5, 1., 1.5, 2., 3.))
    if all(r["status"] == "PASS" for r in mass["seed0"]):
        for value in (4., 8.):
            row = run(Condition(mass_scale=value))
            mass["seed0"].append(row)
            if row["status"] != "PASS":
                break
    confirm(mass)
    wheel = axis("wheel_map", "wheel_delta", (-.5, 0., .167, .5, 1., 2.))
    confirm(wheel)
    return axes


class Study:
    def __init__(self, out, nominal, effects, gain, source):
        self.out, self.nominal, self.effects = out, nominal, effects
        self.gain = np.array(gain, copy=True)
        self.gain.setflags(write=False)
        self.source = source
        self.cache = {}
        self.cases = []
        self.limits = np.array([nominal["physics"][key]["value"]
                                for key in ("wheel_torque_limit", "hip_torque_limit")])
        (out / "cases").mkdir()

    def run(self, condition):
        if condition in self.cache:
            return self.cache[condition]
        if len(self.cases) >= MAX_CASES:
            raise RuntimeError("Hard 60-case budget reached")
        case_id = f"case_{len(self.cases):03d}"
        path = self.out / "cases" / case_id
        path.mkdir(exist_ok=False)
        row = {"id": case_id, "condition": asdict(condition), "status": "RUNNING",
               "artifact_directory": str(path.relative_to(self.out)), "started_utc": utc_now()}
        self.cases.append(row)
        self.cache[condition] = row
        self.save()
        write_json(path / "condition.json", {
            **row, "actual_config": actual_config(self.nominal, condition),
            "actual_runtime": asdict(replace(self.effects, delay_s=condition.delay_s)),
            "controller_design": "../../design.json", "observer": OBSERVER,
            "actual_generalized_wheel_map": [1/self.nominal["physics"]["wheel_radius"]["value"],
                                             -1+condition.wheel_delta, -condition.wheel_delta],
            "actual_generalized_hip_map": [0, -1, 1], "source": self.source,
        })
        start = time.monotonic()
        print(f"{case_id} RUNNING {asdict(condition)}", flush=True)
        try:
            runtime = make_runtime(self.nominal, self.effects, condition)
            (path / "actual_model.xml").write_text(runtime.plant.xml)
            with (path / "observer.csv").open("x", newline="") as stream:
                audit = csv.writer(stream)
                audit.writerow(["tick", *self.nominal["controller"]["state_order"],
                                "own_wheel_tau_hat", "own_hip_tau_hat", "own_previous_wheel",
                                "own_previous_hip", "raw_wheel", "raw_hip", "clipped_wheel", "clipped_hip"])
                controller = DesignObserverController(self.gain, self.limits, audit)
                metrics = evaluate(runtime, controller, "push", condition.seed, path / "rollout")
            row.update(status=metrics["status"], failed_checks=metrics["failed_checks"], metrics=metrics)
        except Exception:
            error = traceback.format_exc()
            (path / "error.txt").write_text(error)
            row.update(status="ERROR", failed_checks=None, error=error)
        row.update(elapsed_wall_s=time.monotonic()-start, ended_utc=utc_now())
        write_json(path / "result.json", row)
        self.save()
        print(f"{case_id} {row['status']} checks={row.get('failed_checks')} wall={row['elapsed_wall_s']:.3f}s", flush=True)
        return row

    def save(self):
        write_json(self.out / "cases.json", self.cases)
        # Append-only progress survives later manifest interruption.
        with (self.out / "events.jsonl").open("a") as stream:
            stream.write(json.dumps({"utc": utc_now(), "cases": len(self.cases),
                                    "latest": self.cases[-1]}, allow_nan=False) + "\n")


def report(summary):
    lines = ["# Reduced-model stress results", "", LIMITATION, "",
             f"Source `{summary['source']['git_commit']}`; {summary['status']}; "
             f"{summary['case_count']} unique cases; {summary['counts']}. "
             "Completed execution does not imply acceptance.", "",
             "One nominal L=0.16 m / 2 ms augmented DARE, fixed Q/R and gain. "
             "Every case uses its own 2 ms / 5 ms command-only observer. "
             "10 s protocol or declared early physical/numerical failure; "
             "initial +8/-6 degrees, 0.15 s push at 3 s, 2/4 Nm caps, unchanged IMU noise.", "",
             "| Axis | Seed-0 tested value:status | First tested FAIL | Five-seed confirmation PASS/5 |",
             "|---|---|---|---|"]
    for name, panel in summary["axes"].items():
        field = panel["field"]
        values = ", ".join(f"{r['condition'][field]:g}:{r['status']}" for r in panel["seed0"])
        fail = panel["first_tested_failure"]
        first = f"{fail['condition'][field]:g} ({', '.join(fail['failed_checks'])})" if fail else "none on seed 0"
        confirms = "; ".join(f"{g['value']:g}: {sum(r['status']=='PASS' for r in g['cases'])}/5"
                             for g in panel["confirmations"])
        lines.append(f"| {name} ({field}) | {values} | {first} | {confirms} |")
    lines += ["", "Push bisection is conditional on the sampled seed-0 PASS/FAIL bracket; "
              "no monotonicity assumption proves untested values. Other axes cover only their declared grids. "
              "Mass scales body mass and COM inertia together at fixed COM/shape. "
              "Wheel reaction [1/r,-1+delta,-delta] preserves total -1; hip [0,-1,1] is unchanged. "
              "Delta .167 supplies generalized-reaction context, not 17% of the full B matrix or a plausible hardware range.", "",
              "`summary.json` and `cases.json` retain all identities, strict checks, peaks, recovery, effort, "
              "saturation and full evaluator metrics. Each case keeps actual config/MJCF, observer feedback, "
              "control/interval CSVs and errors/partial runs. `run.json` records command, source, versions and exit. "
              "The external supervisor receipt records the process exit independently."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="Fresh, exclusive study directory")
    parser.add_argument("--case", type=Path, help="Independently reproduce one saved condition.json")
    args = parser.parse_args(argv)
    out = args.out.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "RUNNING", "started_utc": utc_now(), "pid": os.getpid(),
               "command": [sys.executable, "-m", "sim.gain_schedule.stress", *(sys.argv[1:] if argv is None else argv)],
               "cwd": str(Path.cwd()), "thread_limits": {name: os.environ[name] for name in THREAD_VARIABLES}}
    start = time.monotonic()
    write_json(out / "run.json", receipt)
    exit_code = 1
    try:
        source = {"git_commit": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
                  "git_status": subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain"], text=True),
                  "python": sys.version, "platform": platform.platform(),
                  "packages": {p: importlib.metadata.version(p) for p in ("numpy", "scipy", "mujoco")}}
        receipt["source"] = source
        write_json(out / "run.json", receipt)
        nominal, experiment, effects = load_experiment(CONFIG)
        if nominal["physics"]["leg_length"]["value"] != .16 or effects.delay_s != .002:
            raise ValueError("Expected frozen 0.16 m / 2 ms nominal design")
        # Exactly one new augmented DARE. Existing nominal six-state K is diagnostic only.
        gain, design = synthesize_augmented(nominal, effects, experiment["frozen_nominal"]["K"])
        design.update(candidate="fresh fixed nominal stress baseline; NOT PPO v2", observer=OBSERVER,
                      nominal_config=nominal, experiment_config=experiment, source=source)
        write_json(out / "design.json", design)
        study = Study(out, nominal, effects, gain, source)
        if args.case is None:
            axes = bounded_plan(study.run)
        else:
            saved = json.loads(args.case.read_text())
            study.run(Condition(**saved["condition"]))
            axes = {}
        counts = {s: sum(c["status"] == s for c in study.cases) for s in ("PASS", "FAIL", "ERROR")}
        status = "COMPLETE" if counts["ERROR"] == 0 else "INCOMPLETE"
        summary = {"status": status, "source": source, "limitation": LIMITATION,
                   "observer": OBSERVER, "case_count": len(study.cases), "max_cases": MAX_CASES,
                   "counts": counts, "axes": axes, "cases": study.cases}
        write_json(out / "summary.json", summary)
        (out / "report.md").write_text(report(summary))
        exit_code = 0 if status == "COMPLETE" else 1
    except Exception:
        (out / "error.txt").write_text(traceback.format_exc())
        traceback.print_exc()
    finally:
        receipt.update(status="EXITED", exit_code=exit_code, ended_utc=utc_now(),
                       elapsed_wall_s=time.monotonic()-start)
        write_json(out / "run.json", receipt)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
