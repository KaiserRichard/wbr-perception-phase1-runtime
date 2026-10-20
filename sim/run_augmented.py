"""Run the predeclared fixed-first actuator/noise experiment, retaining failures."""

import argparse
from concurrent.futures import ProcessPoolExecutor
from contextlib import nullcontext
from dataclasses import replace
import multiprocessing
from pathlib import Path
import sys
import traceback

import numpy as np

from sim.augmented import AugmentedRuntime, gain_hash, load_experiment
from sim.augmented_eval import evaluate
from sim.lqr import synthesize
from sim.planar import Plant
from sim.run_planar import ROOT, provenance, sha256, write_json


def verify_frozen(base, cfg):
    """Verify baseline synthesis, but always return the committed frozen bytes."""
    computed, record = synthesize(Plant(base))
    frozen = np.asarray(cfg["frozen_nominal"]["K"], float)
    f = cfg["frozen_nominal"]
    if not np.allclose(computed, frozen, rtol=f["portable_verification_rtol"],
                       atol=f["portable_verification_atol"]):
        raise ValueError("Nominal synthesis no longer matches frozen K")
    record["K_used"] = frozen.tolist()
    record["frozen_verification"] = {
        "max_abs_difference": float(np.max(abs(computed-frozen))),
        "bitwise_identical": bool(np.array_equal(computed, frozen)),
        "computed_sha256": gain_hash(computed), "used_sha256": gain_hash(frozen),
        "used_gain_source": "committed frozen matrix, NOT augmented re-synthesis",
    }
    return frozen.copy(), record


def run_case(task):
    """Process entry point: own runtime/RNG/files, with only metrics returned."""
    base, config, out, name, label, K, seed, scenario = task
    runtime = AugmentedRuntime(base, config)
    controller = ((lambda obs: -K @ obs.measurement) if name == "frozen_nominal"
                  else (lambda obs: -K @ obs.vector()))
    case_out = out/name/label/f"seed_{seed}"/scenario
    metrics = evaluate(runtime, controller, scenario, seed, case_out)
    metrics["artifact_directory"] = str(case_out.relative_to(out))
    return metrics


def run_phase(base, cfg, runtime_cfg, out, name, gains, jobs=1):
    """Finish one phase before returning; aggregate in declared case order."""
    if jobs < 1:
        raise ValueError("jobs must be positive")
    phase = {"controller": name, "regimes": {}}
    # Spawn avoids inheriting MuJoCo/BLAS mutable state across platforms.
    pool = (ProcessPoolExecutor(max_workers=jobs,
                                mp_context=multiprocessing.get_context("spawn"))
            if jobs > 1 else nullcontext(None))
    with pool as executor:
        for delay in cfg["experiment"]["delays_s"]:
            label = f"delay_{round(delay*1000)}ms"
            config = replace(runtime_cfg, delay_s=delay)
            K = gains[delay]
            tasks = [(base, config, out, name, label, K, seed, scenario)
                     for seed in cfg["experiment"]["seeds"]
                     for scenario in cfg["experiment"]["scenarios"]]
            results = executor.map(run_case, tasks) if executor else map(run_case, tasks)
            cases = []
            for metrics in results:
                cases.append(metrics)
                seed, scenario = metrics["seed"], metrics["scenario"]
                print(f"{name} {label} seed={seed} {scenario}: {metrics['status']} "
                      f"recovery={metrics['recovery_time_after_event_s']} "
                      f"failed={metrics['failed_checks']}", flush=True)
            phase["regimes"][label] = {
                "delay_s": delay, "K_sha256": gain_hash(K),
                "status": "PASS" if all(c["status"] == "PASS" for c in cases) else "FAIL",
                "cases": cases,
            }
            write_json(out/f"{name}_partial.json", phase)
    phase["status"] = "PASS" if all(v["status"] == "PASS" for v in phase["regimes"].values()) else "FAIL"
    write_json(out/f"{name}.json", phase)
    return phase


def write_report(out, result):
    lines = ["# ASSUMED actuator/noise experiment", "",
             "Completion is separate from individual regime acceptance. Failed CSV/JSON retained.",
             "Control period 2 ms; original mechanics, protocol, Q/R and torque caps unchanged.", "",
             "| Controller | Delay | Controlled passes / 10 | Zero-control passes / 5 |",
             "| --- | ---: | ---: | ---: |"]
    for name, phase in result.get("phases", {}).items():
        for label, regime in phase["regimes"].items():
            controlled = sum(c["status"] == "PASS" for c in regime["cases"] if c["scenario"] != "open_loop")
            negative = sum(c["status"] == "PASS" for c in regime["cases"] if c["scenario"] == "open_loop")
            lines.append(f"| {name} | {label} | {controlled} | {negative} |")
    lines += ["", f"Conditional augmented design: {result.get('augmented_design_decision', 'not reached')}.",
              "", "No hardware validation, RL implementation, or owner gain-exercise completion is claimed."]
    (out/"report.md").write_text("\n".join(lines)+"\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=4,
                        help="maximum case processes per phase (default: 4; 1 is serial)")
    args = parser.parse_args(argv)
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    out = args.out.resolve()
    if out == ROOT or ROOT in out.parents:
        parser.error("--out must be outside the repository")
    out.mkdir(parents=True, exist_ok=False)
    result = {"status": "ERROR", "phases": {}}
    try:
        base, cfg, runtime_cfg = load_experiment(args.config)
        result["provenance"] = provenance(args.config)
        result["provenance"]["command"] = [sys.executable, "-m", "sim.run_augmented",
                                           *(sys.argv[1:] if argv is None else argv)]
        write_json(out/"config.json", cfg)
        write_json(out/"base_config.json", base)
        (out/"model.xml").write_text(Plant(base).xml)
        K, design = verify_frozen(base, cfg)
        write_json(out/"nominal_linearization.json", design)
        fixed = run_phase(base, cfg, runtime_cfg, out, "frozen_nominal",
                          {d: K for d in cfg["experiment"]["delays_s"]}, jobs=args.jobs)
        result["phases"]["frozen_nominal"] = fixed
        # Persist the complete failed baseline BEFORE any conditional synthesis.
        write_json(out/"result.json", result)
        if fixed["status"] == "FAIL":
            from sim.augmented_lqr import synthesize_augmented
            result["augmented_design_decision"] = "triggered by observed fixed-gain FAIL"
            gains = {}
            for delay in cfg["experiment"]["delays_s"]:
                gain, record = synthesize_augmented(base, replace(runtime_cfg, delay_s=delay), K)
                gains[delay] = gain
                write_json(out/f"augmented_linearization_{round(delay*1000)}ms.json", record)
            result["phases"]["augmented_lqr"] = run_phase(
                base, cfg, runtime_cfg, out, "augmented_lqr", gains, jobs=args.jobs)
        else:
            result["augmented_design_decision"] = "not permitted/needed: all fixed-gain cases passed"
        result["status"] = "COMPLETE"
        result["acceptance"] = {name: phase["status"] for name, phase in result["phases"].items()}
        write_report(out, result)
        result["artifact_sha256"] = {str(p.relative_to(out)): sha256(p.read_bytes())
                                    for p in sorted(out.rglob("*")) if p.is_file() and p.name != "result.json"}
    except Exception:
        result["error"] = traceback.format_exc()
        (out/"error.txt").write_text(result["error"])
        print(result["error"], file=sys.stderr)
    write_json(out/"result.json", result)
    print(f"Artifacts: {out}; completion={result['status']}", flush=True)
    return 0 if result["status"].startswith("COMPLETE") else 1


if __name__ == "__main__":
    raise SystemExit(main())
