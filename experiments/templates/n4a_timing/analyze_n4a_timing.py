#!/usr/bin/env python3
"""Evaluate accuracy and profiling artifacts from one n4a_timing experiment."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys


VERSION = "1.0.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def run_tool(command: list[str], log: Path) -> int:
    process = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             check=False)
    log.write_text(process.stdout, encoding="utf-8")
    return process.returncode


def engine_run(run_dir: Path) -> Path | None:
    candidates = sorted((run_dir / "accuracy").glob("run[0-9][0-9]"))
    return candidates[0] if len(candidates) == 1 else None


def latency_input(run_dir: Path, engine: Path | None) -> Path | None:
    candidates = [run_dir / "profile" / "events.csv", run_dir / "profile" / "run_tracking.csv",
                  run_dir / "events.csv", run_dir / "run_tracking.csv"]
    if engine:
        candidates.extend([engine / "events.csv", engine / "run_tracking.csv"])
    found = [path for path in candidates if path.is_file()]
    return found[0] if len(found) == 1 else None


def metric(result: dict | None) -> float | None:
    try:
        return float(result["runs"][0]["ate_rpe_1m"]["se3"]["ate_translation_m"]["rmse"])
    except (KeyError, IndexError, TypeError, ValueError):
        return None


def latency_values(latency: dict | None) -> tuple[float | None, float | None, float | None, int | None]:
    if not latency:
        return None, None, None, None
    block = latency.get("tracking_latency_ns")
    if block is None:
        sessions = latency.get("sessions", {})
        blocks = [item.get("tracking_latency_ns") for item in sessions.values()
                  if isinstance(item, dict) and item.get("tracking_latency_ns")]
        if len(blocks) != 1:
            return None, None, None, None
        block = blocks[0]
    try:
        return (float(block["p50"]) / 1e6, float(block["p95"]) / 1e6,
                float(block["p99"]) / 1e6, int(latency["frame_count"]))
    except (KeyError, TypeError, ValueError):
        return None, None, None, None


def profile_temperature(profile_result: dict | None, profile_dir: Path) -> float | None:
    if profile_result:
        for criterion in profile_result.get("criteria", []):
            if criterion.get("id") == "max_temperature":
                value = criterion.get("measured")
                return float(value) if isinstance(value, (int, float)) else None
    return None


def run_one(args, run_dir: Path, index: int, accuracy_tool: Path, profile_tool: Path) -> dict:
    engine = engine_run(run_dir)
    evaluation_dir = run_dir / "evaluation"
    profile_dir = run_dir / "profile"
    reasons: list[str] = []
    if engine is None:
        reasons.append("missing_or_ambiguous_accuracy_run")

    accuracy_result = None
    accuracy_rc = None
    if engine is not None and args.ground_truth and args.times:
        accuracy_cmd = [sys.executable, str(accuracy_tool), "--sequence", args.sequence,
                        "--runs", str(engine), "--ground-truth", str(args.ground_truth.resolve()),
                        "--times", str(args.times.resolve()), "--out", str(evaluation_dir)]
        accuracy_rc = run_tool(accuracy_cmd, run_dir / "accuracy_analysis.log")
        accuracy_result = read_json(evaluation_dir / "summary.json")
        if accuracy_rc != 0 or not accuracy_result:
            reasons.append("accuracy_analysis_" + ("failed" if accuracy_rc else "missing_result"))
    else:
        reasons.append("accuracy_inputs_missing")

    profile_result = None
    profile_rc = run_tool([sys.executable, str(profile_tool), "validity", "--analyze-only", str(profile_dir)],
                          run_dir / "profile_validity.log")
    profile_result = read_json(profile_dir / "result.json")
    if not profile_result:
        reasons.append("profile_validity_analysis_failed")
    elif profile_result.get("status") != "PASS":
        reasons.append("profile_validity_" + str(profile_result.get("status", "UNKNOWN")).lower())
    elif profile_rc not in (0, None):
        reasons.append("profile_validity_analysis_failed")

    source = latency_input(run_dir, engine)
    latency_result = None
    latency_rc = None
    if source is None:
        reasons.append("latency_input_missing_or_ambiguous")
    else:
        latency_cmd = [sys.executable, str(profile_tool), "latency",
                       "--events" if source.name == "events.csv" else "--tracking", str(source),
                       "--out", str(profile_dir)]
        latency_rc = run_tool(latency_cmd, run_dir / "profile_latency.log")
        latency_result = read_json(profile_dir / "latency.json")
        if latency_rc != 0 or not latency_result:
            reasons.append("latency_analysis_failed")

    preflight = read_json(args.experiment / "preflight.json", {}) or {}
    prior_bits = []
    for criterion in preflight.get("criteria", []):
        if criterion.get("id") == "no_prior_throttle_bits":
            measured = criterion.get("measured", {})
            if isinstance(measured, dict):
                prior_bits = measured.get("invalid_bits_set", []) or []
    if prior_bits:
        reasons.append("prior_throttle_allowed" if preflight.get("prior_throttle_allowed") else "prior_throttle_refused")

    p50, p95, p99, frame_count = latency_values(latency_result)
    accuracy_status = accuracy_result.get("status") if accuracy_result else "BLOCKED"
    profile_status = profile_result.get("status") if profile_result else "BLOCKED"
    valid = (not reasons and accuracy_status == "PASS" and profile_status == "PASS" and
             latency_result is not None)
    run_status = "VALID" if valid else "INVALID"
    return {"run": run_dir.name, "status": run_status, "reasons": reasons,
            "accuracy_status": accuracy_status, "accuracy_ate_rmse_se3_m": metric(accuracy_result),
            "accuracy_summary": str(evaluation_dir / "summary.json") if accuracy_result else None,
            "profile_validity_status": profile_status,
            "profile_validity": str(profile_dir / "result.json") if profile_result else None,
            "max_temperature_c": profile_temperature(profile_result, profile_dir),
            "throttle_status": ("PASS" if profile_status == "PASS" else profile_status),
            "latency_status": "PASS" if latency_result else "BLOCKED",
            "latency_source": str(source) if source else None,
            "latency_frame_count": frame_count, "latency_p50_ms": p50,
            "latency_p95_ms": p95, "latency_p99_ms": p99,
            "accuracy_exit_code": accuracy_rc, "profile_exit_code": profile_rc,
            "latency_exit_code": latency_rc}


def aggregate(runs: list[dict]) -> dict:
    valid = [run for run in runs if run["status"] == "VALID"]
    def stats(key: str) -> dict:
        values = [run[key] for run in valid if isinstance(run.get(key), (int, float))]
        if not values:
            return {"n": 0, "mean": None, "min": None, "max": None}
        return {"n": len(values), "mean": statistics.fmean(values), "min": min(values), "max": max(values)}
    return {"valid_run_count": len(valid), "accuracy_ate_rmse_se3_m": stats("accuracy_ate_rmse_se3_m"),
            "latency_p50_ms": stats("latency_p50_ms"), "latency_p95_ms": stats("latency_p95_ms"),
            "latency_p99_ms": stats("latency_p99_ms"), "max_temperature_c": stats("max_temperature_c")}


def write_report(path: Path, result: dict) -> None:
    rows = ["# N4A timing analysis", "", f"Overall status: **{result['status']}**", "",
            f"Valid runs: {result['aggregate']['valid_run_count']}; excluded runs: {result['excluded_run_count']}", "",
            "| Run | Accuracy ATE RMSE SE3 (m) | Latency P50 (ms) | P95 (ms) | P99 (ms) | Max temp (°C) | Throttle | Result | Why excluded |",
            "|---|---:|---:|---:|---:|---:|---|---|---|"]
    for run in result["runs"]:
        def fmt(key):
            value = run.get(key)
            return "—" if value is None else f"{value:.6f}" if isinstance(value, float) else str(value)
        rows.append(f"| {run['run']} | {fmt('accuracy_ate_rmse_se3_m')} | {fmt('latency_p50_ms')} | "
                    f"{fmt('latency_p95_ms')} | {fmt('latency_p99_ms')} | {fmt('max_temperature_c')} | "
                    f"{run['throttle_status']} | **{run['status']}** | {', '.join(run['reasons']) or '—'} |")
    rows += ["", "Aggregate metrics are calculated from VALID runs only; excluded runs are not averaged.",
             "A VALID result requires accuracy PASS, profile validity PASS, a usable latency trace, and no prior throttle bits.",
             "The analysis is evidence from saved files. It does not prove D435i accuracy, calibration, power quality between polls, or a project gate PASS."]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--experiment", type=Path, required=True)
    p.add_argument("--sequence", required=True)
    p.add_argument("--ground-truth", type=Path, required=True)
    p.add_argument("--times", type=Path, required=True)
    p.add_argument("--accuracy-tool", type=Path)
    p.add_argument("--profile-tool", type=Path)
    args = p.parse_args(argv)
    args.experiment = args.experiment.resolve()
    root = Path(__file__).resolve().parents[2]
    accuracy_tool = (args.accuracy_tool or root / "tools/eval_pipeline/accuracy/evaluate.py").resolve()
    profile_tool = (args.profile_tool or root / "tools/eval_pipeline/profile/profile.py").resolve()
    run_dirs = sorted(args.experiment.glob("run[0-9][0-9]"))
    if not run_dirs:
        print("no run directories found", file=sys.stderr)
        return 2
    runs = [run_one(args, run_dir, index, accuracy_tool, profile_tool)
            for index, run_dir in enumerate(run_dirs, 1)]
    excluded = [run for run in runs if run["status"] != "VALID"]
    aggregate_result = aggregate(runs)
    if aggregate_result["valid_run_count"]:
        status = "PASS"
    elif any(run.get("accuracy_status") != "BLOCKED" for run in runs):
        status = "FAIL"
    else:
        status = "BLOCKED"
    result = {"check": "n4a_timing_analysis", "tool_version": VERSION, "status": status,
              "generated_utc": utc_now(), "sequence": args.sequence,
              "experiment": str(args.experiment), "runs": runs,
              "valid_run_count": aggregate_result["valid_run_count"],
              "excluded_run_count": len(excluded), "excluded_runs": [
                  {"run": run["run"], "reasons": run["reasons"]} for run in excluded],
              "aggregate": aggregate_result,
              "threshold_sources": {"accuracy": "tools/eval_pipeline/accuracy/thresholds.json",
                                    "profile": "tools/eval_pipeline/profile/config.json"}}
    write_json(args.experiment / "summary.json", result)
    write_report(args.experiment / "report.md", result)
    print(f"status={status}; valid_runs={aggregate_result['valid_run_count']}; excluded_runs={len(excluded)}")
    return {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[status]


if __name__ == "__main__":
    raise SystemExit(main())
