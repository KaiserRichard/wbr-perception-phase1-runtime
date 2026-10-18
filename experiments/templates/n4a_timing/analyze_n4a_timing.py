#!/usr/bin/env python3
"""Evaluate accuracy and profiling artifacts from one n4a_timing experiment."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import statistics
import subprocess
import sys


VERSION = "1.1.0"


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(3, f"{self.prog}: {message}\n")


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
        result = json.loads(path.read_text(encoding="utf-8"))
        return result if isinstance(result, dict) else default
    except (OSError, json.JSONDecodeError):
        return default


def run_tool(command: list[str], log: Path) -> int:
    if not Path(command[1]).is_file():
        log.write_text(f"BLOCKED: tool missing: {command[1]}\n", encoding="utf-8")
        return 2
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
        value = float(result["runs"][0]["ate_rpe_1m"]["se3"]["ate_translation_m"]["rmse"])
        return value if math.isfinite(value) and value >= 0 else None
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
        if len(sessions) != 1:
            return None, None, None, None
        latency = next(iter(sessions.values()))
    try:
        values = [float(block[key]) / 1e6 for key in ("p50", "p95", "p99")]
        count = int(latency["frame_count"])
        if count <= 0 or not all(math.isfinite(v) and v >= 0 for v in values) or values != sorted(values):
            return None, None, None, None
        return (*values, count)
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
    checks: list[dict] = []
    def check(name, status):
        checks.append({"id": name, "status": status})
        if status != "PASS":
            reasons.append(name + "_" + status.lower())
    if engine is None:
        reasons.append("missing_or_ambiguous_accuracy_run")

    accuracy_result = None
    accuracy_rc = None
    if engine is not None and args.ground_truth.is_file() and args.times.is_file():
        accuracy_cmd = [sys.executable, str(accuracy_tool), "--sequence", args.sequence,
                        "--runs", str(engine), "--ground-truth", str(args.ground_truth.resolve()),
                        "--times", str(args.times.resolve()), "--out", str(evaluation_dir), "--overwrite"]
        (evaluation_dir / "summary.json").unlink(missing_ok=True)
        accuracy_rc = run_tool(accuracy_cmd, run_dir / "accuracy_analysis.log")
        accuracy_result = read_json(evaluation_dir / "summary.json")
        if accuracy_rc != 0 or not accuracy_result:
            reasons.append("accuracy_analysis_" + ("failed" if accuracy_rc else "missing_result"))
    else:
        reasons.append("accuracy_inputs_missing")

    profile_result = None
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "result.json").unlink(missing_ok=True)
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
        (profile_dir / "latency.json").unlink(missing_ok=True)
        latency_cmd = [sys.executable, str(profile_tool), "latency",
                       "--events" if source.name == "events.csv" else "--tracking", str(source),
                       "--out", str(profile_dir)]
        latency_rc = run_tool(latency_cmd, run_dir / "profile_latency.log")
        latency_result = read_json(profile_dir / "latency.json")
        if latency_rc != 0 or not latency_result:
            reasons.append("latency_analysis_failed")
        if source.name == "events.csv" and latency_rc == 0:
            # Reuse the observer's loss and lifecycle accounting; a percentile
            # from a few surviving pairs cannot establish a complete trace.
            root = Path(__file__).resolve().parents[3]
            if str(root) not in sys.path:
                sys.path.insert(0, str(root))
            from tools.runtime_observer import aggregate as observer
            try:
                events, losses = observer.read_csv(source.read_text())
                trace = observer.summarize(events, losses=losses)
                complete = trace["trace_completeness"] == "COMPLETE" and all(
                    report["stage_durations_ns"]["track_duration_ns"]["count"] ==
                    report["event_counts"].get("track_start", 0) == report["event_counts"].get("track_end", 0)
                    for report in trace["sessions"].values())
            except (OSError, ValueError):
                complete = False
            check("observer_trace_complete", "PASS" if complete else "BLOCKED")

    preflight = read_json(args.experiment / "preflight.json", {}) or {}
    prior_bits = []
    for criterion in preflight.get("criteria", []):
        if criterion.get("id") == "no_prior_throttle_bits":
            measured = criterion.get("measured", {})
            if isinstance(measured, dict):
                prior_bits = measured.get("invalid_bits_set", []) or []
    if prior_bits:
        reasons.append("prior_throttle_allowed" if preflight.get("prior_throttle_allowed") else "prior_throttle_refused")

    config = read_json(args.experiment / "config.json")
    check("saved_config", "PASS" if config else "BLOCKED")
    invalid_bits = (config or {}).get("preflight", {}).get("invalid_throttle_bits", {}).get("value", [])
    for name in ("throttled_before.txt", "throttled_after.txt"):
        raw = (engine / name).read_text().strip() if engine and (engine / name).is_file() else ""
        match = re.fullmatch(r"throttled=(0x[0-9a-fA-F]{1,8})", raw)
        state = "BLOCKED" if match is None or not invalid_bits else (
            "FAIL" if any(int(match[1], 16) & (1 << bit) for bit in invalid_bits) else "PASS")
        check(name.removesuffix(".txt"), state)

    p50, p95, p99, frame_count = latency_values(latency_result)
    def tool_status(result, rc):
        status = result.get("status") if result else None
        if status in ("FAIL", "BLOCKED"):
            return status
        return "PASS" if status == "PASS" and rc == 0 else "BLOCKED"
    accuracy_status = tool_status(accuracy_result, accuracy_rc)
    profile_status = tool_status(profile_result, profile_rc)
    check("accuracy", accuracy_status)
    check("profile_validity", profile_status)
    check("latency", "PASS" if latency_rc == 0 and frame_count is not None else "BLOCKED")
    ate = metric(accuracy_result)
    check("accuracy_metric", "PASS" if ate is not None and math.isfinite(ate) and ate >= 0 else "BLOCKED")
    check("preflight", preflight.get("status") if preflight.get("status") in ("PASS", "FAIL") else "BLOCKED")
    check("prior_throttle", "FAIL" if prior_bits else "PASS")
    capture = read_json(run_dir / "capture.json", {}) or {}
    capture_status = capture.get("check_status", "BLOCKED")
    check("capture", capture_status if capture_status in ("PASS", "FAIL") else "BLOCKED")
    metadata = read_json(profile_dir / "metadata.json", {}) or {}
    count = metadata.get("sample_count")
    try:
        with (profile_dir / "samples.csv").open(newline="") as stream:
            actual_samples = sum(1 for _ in csv.DictReader(stream))
    except (OSError, csv.Error):
        actual_samples = None
    check("sampler_metadata", "PASS" if isinstance(count, int) and count > 0 and count == actual_samples else "BLOCKED")
    temperature = profile_temperature(profile_result, profile_dir)
    check("temperature_evidence", "PASS" if temperature is not None and math.isfinite(temperature) else "BLOCKED")
    sampled_throttle = next((c.get("status", "BLOCKED") for c in
        (profile_result or {}).get("criteria", []) if c.get("id") == "no_throttle_or_undervoltage"), "BLOCKED")
    throttle_states = [c["status"] for c in checks if c["id"] in
                       ("prior_throttle", "throttled_before", "throttled_after")] + [sampled_throttle]
    throttle_status = "FAIL" if "FAIL" in throttle_states else "BLOCKED" if "BLOCKED" in throttle_states else "PASS"
    check("throttle_evidence", throttle_status)
    if (run_dir / "start_preflight/preflight.json").exists():
        start_check = read_json(run_dir / "start_preflight/preflight.json", {}) or {}
        check("run_start_preflight", start_check.get("status", "BLOCKED"))
    status = "FAIL" if any(c["status"] == "FAIL" for c in checks) else (
        "BLOCKED" if reasons else "PASS")
    valid = status == "PASS"
    run_status = "VALID" if valid else "INVALID"
    return {"run": run_dir.name, "status": run_status, "check_status": status, "reasons": reasons,
            "accuracy_status": accuracy_status, "accuracy_ate_rmse_se3_m": metric(accuracy_result),
            "accuracy_summary": str(evaluation_dir / "summary.json") if accuracy_result else None,
            "profile_validity_status": profile_status,
            "profile_validity": str(profile_dir / "result.json") if profile_result else None,
            "max_temperature_c": temperature,
            "throttle_status": throttle_status,
            "latency_status": "PASS" if latency_rc == 0 and frame_count is not None else "BLOCKED",
            "latency_source": str(source) if source else None,
            "realtime_status": "UNKNOWN",
            "latency_definition": "tracking-call duration in host monotonic time; not camera-to-pose latency",
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
            f"Declared runs: {result['declared_run_count']}; missing runs: {', '.join(result['missing_runs']) or 'none'}", "",
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
             "Real-time performance remains UNKNOWN: VALID qualifies the saved timing evidence, not sustained dataset-rate execution.",
             "The analysis is evidence from saved files. It does not prove D435i accuracy, calibration, power quality between polls, or a project gate PASS."]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    started = utc_now()
    p = ArgumentParser(description=__doc__)
    p.add_argument("--experiment", "--analyze-only", dest="experiment", type=Path, required=True)
    p.add_argument("--sequence", required=True)
    p.add_argument("--ground-truth", type=Path, required=True)
    p.add_argument("--times", type=Path, required=True)
    p.add_argument("--accuracy-tool", type=Path)
    p.add_argument("--profile-tool", type=Path)
    args = p.parse_args(argv)
    args.experiment = args.experiment.resolve()
    root = Path(__file__).resolve().parents[3]
    accuracy_tool = (args.accuracy_tool or root / "tools/eval_pipeline/accuracy/evaluate.py").resolve()
    profile_tool = (args.profile_tool or root / "tools/eval_pipeline/profile/profile.py").resolve()
    args.experiment.mkdir(parents=True, exist_ok=True)
    run_dirs = sorted(path for path in args.experiment.glob("run[0-9]*")
                      if path.is_dir() and re.fullmatch(r"run[0-9]+", path.name))
    runs = [run_one(args, run_dir, index, accuracy_tool, profile_tool)
            for index, run_dir in enumerate(run_dirs, 1)]
    excluded = [run for run in runs if run["status"] != "VALID"]
    aggregate_result = aggregate(runs)
    provenance = read_json(args.experiment / "provenance.json", {}) or {}
    expected = provenance.get("runs")
    complete = (isinstance(expected, int) and expected > 0 and
                {path.name for path in run_dirs} == {f"run{i:02d}" for i in range(1, expected + 1)})
    missing_runs = sorted({f"run{i:02d}" for i in range(1, expected + 1)} - {path.name for path in run_dirs}) if isinstance(expected, int) and expected > 0 else []
    criteria = [{"id": run["run"], "description": "Accuracy, capture, preflight and latency evidence complete and valid",
                 "measured": run["reasons"], "unit": "run", "threshold": "all required checks PASS",
                 "status": run["check_status"], "evidence": "summary.json",
                 "threshold_source": "PROPOSED: T15 controlled timing evidence requirements"} for run in runs]
    criteria.append({"id": "declared_runs_present", "description": "All declared repetitions are present",
                     "measured": len(runs), "unit": "runs", "threshold": f"{expected} declared runs",
                     "status": "PASS" if complete else "BLOCKED", "evidence": "provenance.json",
                     "threshold_source": "SOURCE-SUPPORTED: operator invocation saved in provenance.json"})
    status = "FAIL" if any(c["status"] == "FAIL" for c in criteria) else (
        "BLOCKED" if any(c["status"] == "BLOCKED" for c in criteria) else "PASS")
    result = {"check": "n4a_timing_analysis", "tool_version": VERSION, "status": status,
              "generated_utc": utc_now(), "sequence": args.sequence,
              "started_utc": started, "ended_utc": utc_now(),
              "host": {"system": platform.system(), "machine": platform.machine(), "python": platform.python_version()},
              "criteria": criteria, "notes": ["CALCULATED from saved evidence; fixture PASS is not a hardware gate PASS."],
              "raw_files": [{"path": str(path.relative_to(args.experiment)), "sha256": sha256(path)}
                            for path in sorted(args.experiment.rglob("*")) if path.is_file()
                            and path.name not in ("result.json", "summary.json", "report.md")],
              "experiment": str(args.experiment), "runs": runs,
              "valid_run_count": aggregate_result["valid_run_count"],
              "declared_run_count": expected, "missing_runs": missing_runs,
              "excluded_run_count": len(excluded), "excluded_runs": [
                  {"run": run["run"], "reasons": run["reasons"]} for run in excluded],
              "aggregate": aggregate_result,
              "threshold_sources": {"accuracy": "tools/eval_pipeline/accuracy/thresholds.json",
                                    "profile": "tools/eval_pipeline/profile/config.json"}}
    write_json(args.experiment / "summary.json", result)
    write_json(args.experiment / "result.json", result)
    write_report(args.experiment / "report.md", result)
    print("run\tstatus\tvalidity\texclusion reasons")
    for run in runs:
        print(f"{run['run']}\t{run['check_status']}\t{run['status']}\t{', '.join(run['reasons'])}")
    print(f"status={status}; valid_runs={aggregate_result['valid_run_count']}; excluded_runs={len(excluded)}")
    return {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[status]


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"analyze_n4a_timing: {exc}", file=sys.stderr)
        raise SystemExit(3)
