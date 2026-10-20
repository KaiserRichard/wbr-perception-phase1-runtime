"""Compare the learner function with compiled original C; TODO is BLOCKED."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import inspect
import json
import math
from pathlib import Path
import subprocess

from . import student
from .build_reference import sha256
from .reference import CReference
from .source import FIXTURES, load_coefficients, load_vectors

# Declared before exercise evaluation; accommodates host float32 vs Python double.
ABS_TOL = 2e-5
REL_TOL = 2e-6


def _validate_result(matrix) -> list[float]:
    if len(matrix) != 2 or any(len(row) != 6 for row in matrix):
        raise ValueError("Return shape must be 2x6: wheel row, then hip row")
    values = [float(x) for row in matrix for x in row]
    if not all(map(math.isfinite, values)):
        raise ValueError("Return values must all be finite")
    return values


def evaluate(build_dir: Path, function=None) -> dict:
    function = student.gain_schedule if function is None else function
    reference = CReference(build_dir)
    coefficients = load_coefficients()
    vectors = load_vectors()
    cases = [(c["id"], coefficients, c["length_m"], reference.schedule(c["length_m"]))
             for c in vectors["schedule_cases"]]
    for case in vectors["polynomial_cases"]:
        row = tuple(case["coefficients"])
        expected = reference.scalar_gain(row, case["length_m"])
        cases.append((case["id"], (row,) * 12, case["length_m"], [expected] * 12))
    rows = []
    status = "PASS"
    for case_id, coeffs, length, expected in cases:
        try:
            actual = _validate_result(function(coeffs, length))
            passed = all(math.isclose(a, b, abs_tol=ABS_TOL, rel_tol=REL_TOL)
                         for a, b in zip(actual, expected, strict=True))
            rows.append({"id": case_id, "status": "PASS" if passed else "FAIL",
                         "max_abs_error": max(abs(a-b) for a, b in zip(actual, expected)),
                         "expected_c": expected, "actual_python": actual})
            if not passed:
                status = "FAIL"
        except NotImplementedError as error:
            status = "BLOCKED" if status != "FAIL" else "FAIL"
            rows.append({"id": case_id, "status": "BLOCKED", "reason": str(error)})
            break
        except Exception as error:
            status = "FAIL"
            rows.append({"id": case_id, "status": "FAIL",
                         "reason": f"{type(error).__name__}: {error}"})
    root = Path(__file__).resolve().parents[2]
    def git(*args):
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"
    try:
        function_source = inspect.getsource(function)
    except (OSError, TypeError):
        function_source = "UNKNOWN"
    return {"check": "python_gain_schedule_vs_pinned_host_c", "status": status,
            "label": "HOST PARITY ONLY; not firmware, dynamics or hardware validation",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "upstream_commit": reference.metadata["source_commit"],
            "abs_tol": ABS_TOL, "rel_tol": REL_TOL,
            "case_count_planned": len(cases), "cases": rows,
            "fixtures_sha256": sha256(FIXTURES),
            "student_file_sha256": sha256(Path(student.__file__)),
            "function_source_sha256": hashlib.sha256(function_source.encode()).hexdigest(),
            "build_metadata_sha256": sha256(Path(build_dir) / "build_metadata.json"),
            "repository_commit": git("rev-parse", "HEAD"),
            "repository_status": git("status", "--porcelain"),
            "python_vmc_parity": "NOT IMPLEMENTED; native VMC checks are separate"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path, help="New JSON report; never overwritten")
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"Report already exists: {args.out}")
    report = evaluate(args.build_dir)
    with args.out.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(f"gain parity: {report['status']} ({args.out})")
    for case in report["cases"]:
        if case["status"] != "PASS":
            print(f"{case['id']}: {case.get('reason', 'numeric mismatch')}")
    return {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
