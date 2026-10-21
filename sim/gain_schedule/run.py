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
from sim.gain_schedule.geometry import geometry_evidence
from sim.gain_schedule.model import (
    DEFAULT_DELAYS, DEFAULT_LENGTHS, DOMAIN_M, EVALUATION_LENGTHS, FAMILY, STUDY,
    check_length, config_at_length, training_midpoints,
)
from sim.gain_schedule.poles import check_fitted_poles


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "sim/configs/assumed_actuator_noise.json"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def read_json(path):
    return json.loads(Path(path).read_text())


def code_source():
    """Lean source receipt, also usable by the NumPy-only fitter."""
    return {
        "git_commit": subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
        "git_dirty": bool(subprocess.check_output(
            ["git", "-C", str(ROOT), "status", "--porcelain"], text=True).strip()),
    }


def source_info():
    """Small run receipt; no account/environment or evidence-tree mutation."""
    return {
        **code_source(),
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
        raise ValueError(f"Sweep must span the full {DOMAIN_M} m domain")
    delays = sorted(args.delays)
    if not delays or len(set(delays)) != len(delays) or any(d not in DEFAULT_DELAYS for d in delays):
        raise ValueError("Use unique delays from 0.002, 0.003, 0.004, 0.005 s")
    reference, experiment, effects = load_experiment(args.config)
    result = {
        "schema_version": 1, "kind": "assumed_leg_sweep", "family": FAMILY, "study": STUDY,
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
    write_json(out / "geometry.json", geometry_evidence(
        reference, [*lengths, *training_midpoints(lengths), *EVALUATION_LENGTHS]))
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
        "schema_version": 1, "kind": "assumed_leg_schedule", "family": FAMILY, "study": STUDY,
        "status": "COMPLETE", "physics_acceptance": "NOT_EVALUATED",
        "sweep_sha256": hashlib.sha256(args.sweep.read_bytes()).hexdigest(),
        "reference_config": source["reference_config"],
        "experiment_config": source["experiment_config"],
        "source": source.get("source"), "fit_source": code_source(), "regimes": [],
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


def load_schedule(path):
    """Refuse legacy wide-domain schedules before importing/executing physics.

    Their saved coefficients retain their original meaning and can still be
    read by the general polynomial helper; they are not valid for this runner.
    """
    schedule = read_json(path)
    if (schedule.get("schema_version") != 1 or
            schedule.get("kind") != "assumed_leg_schedule" or
            schedule.get("family") != FAMILY or schedule.get("status") != "COMPLETE" or
            not schedule.get("regimes")):
        raise ValueError("Expected a complete assumed-model polynomial schedule")
    delays = set()
    for regime in schedule["regimes"]:
        fit = regime["fit"]
        if fit.get("domain_m") != list(DOMAIN_M):
            raise ValueError("Legacy or incompatible schedule domain; regenerate the restricted "
                             "sweep and fit without reinterpreting old coefficients")
        training_midpoints(fit["diagnostics"]["sample_lengths_m"])
        delay = regime["runtime"]["delay_s"]
        if delay not in DEFAULT_DELAYS or delay in delays:
            raise ValueError("Unsupported or duplicate delay regime")
        delays.add(delay)
        order, inputs = regime["state_order"], regime["input_order"]
        gains = evaluate_polynomial(fit, DOMAIN_M)
        if (len(set(order)) != len(order) or len(set(inputs)) != 2 or
                gains.shape != (2, 2, len(order))):
            raise ValueError("Schedule dimensions do not match state/input order")
    return schedule


def linear_check(args, out):
    """Fresh actual augmented A/B at every training midpoint; no rollouts."""
    schedule = load_schedule(args.schedule)
    from sim.augmented import RuntimeConfig
    from sim.augmented_lqr import synthesize_augmented
    from sim.lqr import synthesize
    from sim.planar import Plant

    write_json(out / "schedule.json", schedule)
    grids = [training_midpoints(r["fit"]["diagnostics"]["sample_lengths_m"])
             for r in schedule["regimes"]]
    result = {
        "status": "INCOMPLETE", "family": FAMILY, "study": STUDY, "source": source_info(),
        "domain_m": list(DOMAIN_M), "expected_checks": sum(map(len, grids)),
        "cases": [], "errors": [], "nonlinear_cases_run": 0,
        "claim": "Sampled local poles only; no continuous-domain, varying-length, "
                 "nonlinear, five-bar dynamics or hardware stability claim",
    }
    write_json(out / "linear_checks.json", result)
    for regime_index, (regime, lengths) in enumerate(zip(schedule["regimes"], grids)):
        for index, length in enumerate(lengths):
            case_out = out / f"delay_{regime_index:02d}" / f"midpoint_{index:02d}"
            case_out.mkdir(parents=True)
            identity = {"length_m": length, "delay_s": regime["runtime"]["delay_s"],
                        "artifact_directory": str(case_out.relative_to(out))}
            try:
                cfg = config_at_length(schedule["reference_config"], length)
                effects = RuntimeConfig(**regime["runtime"])
                write_json(case_out / "config.json", cfg)
                nominal, nominal_record = synthesize(Plant(cfg))
                write_json(case_out / "nominal_design.json", nominal_record)
                exact, design = synthesize_augmented(cfg, effects, nominal)
                write_json(case_out / "exact_design.json", design)
                check = check_fitted_poles(regime, length, exact, design, cfg)
                check["actual_matrices_file"] = "exact_design.json"
                write_json(case_out / "polynomial_check.json", check)
                result["cases"].append({**identity, **{key: check[key] for key in (
                    "polynomial_pole_radius", "margin_to_one", "slowest_time_constant_s",
                    "polynomial_local_status", "exact_pole_radius")}})
                print(f"L={length:g} delay={effects.delay_s:g}: "
                      f"{check['polynomial_local_status']} rho={check['polynomial_pole_radius']:.12g}",
                      flush=True)
            except Exception:
                error = traceback.format_exc()
                (case_out / "error.txt").write_text(error)
                result["errors"].append({**identity, "error": error})
            write_json(out / "linear_checks.json", result)
    result["status"] = "COMPLETE" if not result["errors"] else "INCOMPLETE"
    result["polynomial_local_acceptance"] = (
        "PASS" if result["status"] == "COMPLETE" and len(result["cases"]) == result["expected_checks"]
        and all(c["polynomial_local_status"] == "PASS" for c in result["cases"]) else "FAIL")
    write_json(out / "linear_checks.json", result)
    return {**{key: result[key] for key in (
        "status", "polynomial_local_acceptance", "expected_checks", "errors", "claim")},
        "checks_completed": len(result["cases"]), "nonlinear_cases_run": 0}


def evaluate(args, out):
    schedule = load_schedule(args.schedule)
    lengths = _lengths(args.lengths)
    from sim.augmented import AugmentedRuntime, RuntimeConfig
    from sim.augmented_eval import evaluate as evaluate_case
    from sim.augmented_lqr import synthesize_augmented
    from sim.lqr import synthesize
    from sim.planar import Plant

    if (not args.seeds or any(s < 0 for s in args.seeds) or
            len(set(args.seeds)) != len(args.seeds)):
        raise ValueError("Seeds must be unique nonnegative integers")
    write_json(out / "schedule.json", schedule)
    result = {
        "status": "INCOMPLETE", "family": FAMILY, "study": STUDY, "source": source_info(),
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
            check = check_fitted_poles(regime, length, exact, design, cfg)
            fitted = np.asarray(check["Kfit"])
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
    linear_parser = sub.add_parser("linear-check", help="Fresh midpoint A/B and fitted poles; no rollouts")
    linear_parser.add_argument("--schedule", type=Path, required=True)
    linear_parser.set_defaults(run=linear_check)
    eval_parser = sub.add_parser("evaluate", help="HEAVY: matched fresh-DARE/polynomial rollouts")
    eval_parser.add_argument("--schedule", type=Path, required=True)
    eval_parser.add_argument("--lengths", type=float, nargs="+", default=EVALUATION_LENGTHS)
    eval_parser.add_argument("--seeds", type=int, nargs="+", default=list(range(5)))
    eval_parser.set_defaults(run=evaluate)
    for subparser in (sweep_parser, fit_parser, linear_parser, eval_parser):
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
