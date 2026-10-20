"""Serial assumed-model sweep, polynomial fit, and held-length evaluation."""

import argparse
from dataclasses import asdict, replace
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import traceback

import numpy as np

from sim.gain_schedule.fitting import evaluate_polynomial, fit_polynomial
from sim.gain_schedule.model import (
    DEFAULT_DELAYS, DEFAULT_LENGTHS, DOMAIN_M, EVALUATION_LENGTHS, FAMILY,
    check_length, config_at_length,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "sim/configs/assumed_actuator_noise.json"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def read_json(path):
    return json.loads(Path(path).read_text())


def source_info():
    """Small run receipt; no account/environment or evidence-tree mutation."""
    return {
        "git_commit": subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
        "python": sys.version,
        "packages": {name: importlib.metadata.version(name)
                     for name in ("numpy", "scipy", "mujoco")},
    }


def _lengths(values):
    values = [check_length(v) for v in values]
    if not values or len(set(values)) != len(values):
        raise ValueError("Need nonempty, unique lengths")
    return sorted(values)


def sweep(args, out):
    # Deliberately lazy: fit/help/tests need no MuJoCo import or execution.
    from sim.augmented import load_experiment
    from sim.augmented_lqr import synthesize_augmented
    from sim.lqr import synthesize
    from sim.planar import Plant

    lengths = _lengths(args.lengths)
    if lengths[0] != DOMAIN_M[0] or lengths[-1] != DOMAIN_M[1]:
        raise ValueError("Sweep must span the full 0.12–0.30 m domain")
    delays = sorted(args.delays)
    if not delays or len(set(delays)) != len(delays) or any(d not in DEFAULT_DELAYS for d in delays):
        raise ValueError("Use unique delays from 0.002, 0.003, 0.004, 0.005 s")
    reference, experiment, effects = load_experiment(args.config)
    result = {
        "schema_version": 1, "kind": "assumed_leg_sweep", "family": FAMILY,
        "status": "INCOMPLETE", "physics_acceptance": "NOT_EVALUATED",
        "domain_m": list(DOMAIN_M), "lengths_m": lengths,
        "reference_config": reference,
        "experiment_config": experiment,
        "source": source_info(),
        "regimes": [{"runtime": asdict(replace(effects, delay_s=d)), "samples": []}
                    for d in delays],
        "errors": [],
    }
    write_json(out / "sweep.json", result)
    for index, length in enumerate(lengths):
        cfg = config_at_length(reference, length)
        length_out = out / f"length_{index:02d}"
        length_out.mkdir()
        write_json(length_out / "config.json", cfg)
        try:
            plant = Plant(cfg)
            (length_out / "model.xml").write_text(plant.xml)
            nominal, nominal_record = synthesize(plant)
            write_json(length_out / "nominal_design.json", nominal_record)
        except Exception:
            error = traceback.format_exc()
            (length_out / "error.txt").write_text(error)
            result["errors"].append({"length_m": length, "error": error})
            write_json(out / "sweep.json", result)
            continue
        for regime_index, regime in enumerate(result["regimes"]):
            design_path = length_out / f"delay_{regime_index:02d}.json"
            try:
                runtime_config = replace(effects, delay_s=regime["runtime"]["delay_s"])
                K, record = synthesize_augmented(cfg, runtime_config, nominal)
                record["study"] = (
                    "Separate assumed-model length sweep. Fresh nominal K is only a "
                    "diagnostic reference; controller uses fresh delay-state DARE K.")
                write_json(design_path, record)
                regime["samples"].append({
                    "length_m": length, "K": K.tolist(),
                    "state_order": record["state_order"],
                    "input_order": cfg["controller"]["input_order"],
                    "design_path": str(design_path.relative_to(out)),
                    "local_pole_radius": record["max_closed_loop_pole_magnitude"],
                    "DARE_relative_residual": record["DARE_relative_residual"],
                })
                print(f"L={length:g} delay={runtime_config.delay_s:g}: synthesized", flush=True)
            except Exception:
                error = traceback.format_exc()
                design_path.with_suffix(".error.txt").write_text(error)
                result["errors"].append({
                    "length_m": length, "delay_s": regime["runtime"]["delay_s"], "error": error,
                })
            write_json(out / "sweep.json", result)
    result["status"] = "COMPLETE" if not result["errors"] else "INCOMPLETE"
    write_json(out / "sweep.json", result)
    return {"status": result["status"], "physics_acceptance": "NOT_EVALUATED",
            "designs_completed": sum(len(r["samples"]) for r in result["regimes"]),
            "errors": result["errors"]}


def fit_sweep(args, out):
    source = read_json(args.sweep)
    if (source.get("schema_version") != 1 or source.get("kind") != "assumed_leg_sweep" or
            source.get("family") != FAMILY or source.get("status") != "COMPLETE" or
            source.get("domain_m") != list(DOMAIN_M) or not source.get("regimes")):
        raise ValueError("Fit requires a complete matching assumed-model sweep")
    fitted = {
        "schema_version": 1, "kind": "assumed_leg_schedule", "family": FAMILY,
        "status": "COMPLETE", "physics_acceptance": "NOT_EVALUATED",
        "sweep_sha256": hashlib.sha256(args.sweep.read_bytes()).hexdigest(),
        "reference_config": source["reference_config"],
        "experiment_config": source["experiment_config"],
        "source": source.get("source"), "regimes": [],
    }
    seen_delays = set()
    for regime in source["regimes"]:
        samples = regime["samples"]
        delay = regime["runtime"]["delay_s"]
        if delay in seen_delays:
            raise ValueError("Duplicate delay regime")
        seen_delays.add(delay)
        if not samples or sorted(s["length_m"] for s in samples) != sorted(source["lengths_m"]):
            raise ValueError("Incomplete regime sample grid")
        order, inputs = samples[0]["state_order"], samples[0]["input_order"]
        gains = np.asarray([s["K"] for s in samples], float)
        if any(s["state_order"] != order or s["input_order"] != inputs for s in samples):
            raise ValueError("State/input order differs within a delay regime")
        if gains.shape != (len(samples), 2, len(order)) or len(inputs) != 2:
            raise ValueError("Gain dimensions do not match state/input order")
        fit = fit_polynomial([s["length_m"] for s in samples], gains,
                             degree=args.degree, max_condition=args.max_condition)
        fitted["regimes"].append({
            "runtime": regime["runtime"], "state_order": order, "input_order": inputs,
            "fit": fit,
        })
    write_json(out / "schedule.json", fitted)
    return {"status": "COMPLETE", "physics_acceptance": "NOT_EVALUATED",
            "fits_completed": len(fitted["regimes"])}


def controller(gain):
    """Capture a constant length's matrix; feedback uses causal observation only."""
    gain = np.asarray(gain, float).copy()
    return lambda observation: -gain @ observation.vector()


def evaluate(args, out):
    from sim.augmented import AugmentedRuntime, RuntimeConfig
    from sim.augmented_eval import evaluate as evaluate_case
    from sim.augmented_lqr import synthesize_augmented
    from sim.lqr import synthesize
    from sim.planar import Plant

    schedule = read_json(args.schedule)
    if (schedule.get("schema_version") != 1 or
            schedule.get("kind") != "assumed_leg_schedule" or
            schedule.get("family") != FAMILY or schedule.get("status") != "COMPLETE" or
            not schedule.get("regimes")):
        raise ValueError("Expected a complete assumed-model polynomial schedule")
    lengths = _lengths(args.lengths)
    if (not args.seeds or any(s < 0 for s in args.seeds) or
            len(set(args.seeds)) != len(args.seeds)):
        raise ValueError("Seeds must be unique nonnegative integers")
    write_json(out / "schedule.json", schedule)
    result = {
        "status": "INCOMPLETE", "family": FAMILY, "source": source_info(),
        "schedule_sha256": hashlib.sha256(args.schedule.read_bytes()).hexdigest(),
        "lengths_m": lengths, "seeds": args.seeds, "scenarios": ["balance", "push"],
        "cases": [], "local_linear_checks": [],
        "claim": "Fixed-length cases only; no varying-length or hardware stability claim",
    }
    write_json(out / "evaluation.json", result)
    for index, length in enumerate(lengths):
        cfg = config_at_length(schedule["reference_config"], length)
        length_out = out / f"length_{index:02d}"
        length_out.mkdir()
        write_json(length_out / "config.json", cfg)
        nominal, nominal_record = synthesize(Plant(cfg))
        write_json(length_out / "nominal_design.json", nominal_record)
        for regime_index, regime in enumerate(schedule["regimes"]):
            effects = RuntimeConfig(**regime["runtime"])
            case_root = length_out / f"delay_{regime_index:02d}"
            case_root.mkdir()
            exact, design = synthesize_augmented(cfg, effects, nominal)
            write_json(case_root / "exact_design.json", design)
            fitted = evaluate_polynomial(regime["fit"], length)
            if (fitted.shape != exact.shape or regime["state_order"] != design["state_order"] or
                    regime["input_order"] != cfg["controller"]["input_order"]):
                raise ValueError("Schedule incompatible with runtime state/input order")
            A, B = np.asarray(design["A_discrete_actual"]), np.asarray(design["B_discrete_actual"])
            radius = float(max(abs(np.linalg.eigvals(A - B @ fitted))))
            check = {
                "length_m": length, "delay_s": effects.delay_s,
                "exact_pole_radius": design["max_closed_loop_pole_magnitude"],
                "polynomial_pole_radius": radius,
                "polynomial_local_status": "PASS" if radius < 1 else "FAIL",
                "max_abs_gain_error": float(np.max(abs(fitted - exact))),
                "relative_frobenius_gain_error": float(np.linalg.norm(fitted - exact) /
                                                       np.linalg.norm(exact)),
            }
            write_json(case_root / "polynomial_check.json", {**check, "K": fitted.tolist()})
            result["local_linear_checks"].append(check)
            write_json(out / "evaluation.json", result)
            # Retain nonlinear failures even if the fitted local poles fail.
            for name, gain in (("fresh_dare", exact), ("polynomial", fitted)):
                for seed in args.seeds:
                    for scenario in ("balance", "push"):
                        case_out = case_root / name / f"seed_{seed}" / scenario
                        metrics = evaluate_case(AugmentedRuntime(cfg, effects),
                                                controller(gain), scenario, seed, case_out)
                        result["cases"].append({
                            "length_m": length, "delay_s": effects.delay_s,
                            "controller": name, "seed": seed, "scenario": scenario,
                            "status": metrics["status"], "failed_checks": metrics["failed_checks"],
                            "artifact_directory": str(case_out.relative_to(out)),
                        })
                        write_json(out / "evaluation.json", result)
                        print(f"L={length:g} delay={effects.delay_s:g} {name} "
                              f"seed={seed} {scenario}: {metrics['status']}", flush=True)
    result["status"] = "COMPLETE"
    result["acceptance"] = {
        name: "PASS" if all(c["status"] == "PASS" for c in result["cases"]
                            if c["controller"] == name) else "FAIL"
        for name in ("fresh_dare", "polynomial")
    }
    result["polynomial_local_acceptance"] = (
        "PASS" if all(c["polynomial_local_status"] == "PASS"
                      for c in result["local_linear_checks"]) else "FAIL")
    write_json(out / "evaluation.json", result)
    return {key: result[key] for key in (
        "status", "acceptance", "polynomial_local_acceptance", "claim")}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sweep_parser = sub.add_parser("sweep", help="HEAVY: recompute model gains across lengths")
    sweep_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    sweep_parser.add_argument("--lengths", type=float, nargs="+", default=DEFAULT_LENGTHS)
    sweep_parser.add_argument("--delays", type=float, nargs="+", default=DEFAULT_DELAYS)
    sweep_parser.set_defaults(run=sweep)
    fit_parser = sub.add_parser("fit", help="Small least-squares fit of a completed sweep")
    fit_parser.add_argument("--sweep", type=Path, required=True)
    fit_parser.add_argument("--degree", type=int, default=3)
    fit_parser.add_argument("--max-condition", type=float, default=1e8)
    fit_parser.set_defaults(run=fit_sweep)
    eval_parser = sub.add_parser("evaluate", help="HEAVY: matched fresh-DARE/polynomial rollouts")
    eval_parser.add_argument("--schedule", type=Path, required=True)
    eval_parser.add_argument("--lengths", type=float, nargs="+", default=EVALUATION_LENGTHS)
    eval_parser.add_argument("--seeds", type=int, nargs="+", default=list(range(5)))
    eval_parser.set_defaults(run=evaluate)
    for subparser in (sweep_parser, fit_parser, eval_parser):
        subparser.add_argument("--out", type=Path, required=True,
                               help="NEW output directory outside the repository")
    args = parser.parse_args(argv)
    out = args.out.expanduser().resolve()
    if out == ROOT or ROOT in out.parents:
        parser.error("--out must be outside the repository")
    # Refuse reuse before writing anything; preserve all prior/active evidence.
    out.mkdir(parents=True, exist_ok=False)
    try:
        result = args.run(args, out)
    except Exception:
        error = traceback.format_exc()
        (out / "error.txt").write_text(error)
        result = {"status": "ERROR", "error": error}
        print(error, file=sys.stderr)
    result["command"] = [sys.executable, "-m", "sim.gain_schedule",
                         *(sys.argv[1:] if argv is None else argv)]
    write_json(out / "result.json", result)
    print(f"Artifacts: {out}; completion={result['status']}", flush=True)
    # Experiment completion is distinct from the per-case PASS/FAIL judgments.
    return 0 if result["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
