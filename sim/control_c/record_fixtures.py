"""Extract 64 archived ticks/delay; record 14 synthetic ticks/delay for resets.

Run explicitly with the existing MuJoCo backend, from the repository root.
Reads the archive only. Does not synthesize gains or run a scored experiment.
Normal unit tests consume the committed fixtures and do not import MuJoCo.
"""

import argparse
import csv
from dataclasses import replace
import hashlib
import itertools
import json
import os
from pathlib import Path
import struct

for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
                 "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[variable] = "1"

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gain_digest(gain):
    return hashlib.sha256(b"".join(struct.pack("<d", x) for row in gain for x in row)).hexdigest()


def archive_case(archive, delay, state_order):
    relative = f"augmented_lqr/delay_{delay}ms/seed_0/balance/control.csv"
    with (archive / relative).open(newline="") as stream:
        rows = list(itertools.islice(csv.DictReader(stream), 65))
    if len(rows) != 65:
        raise ValueError("Need 65 consecutive samples (64 complete ticks)")
    state_keys = ["wheel_torque_estimate_Nm", "hip_torque_estimate_Nm"] + [
        f"previous_{i}_{a}_command_Nm"
        for i in range(1, (delay + 1) // 2 + 1) for a in ("wheel", "hip")
    ]
    records = []
    for row, after in zip(rows, rows[1:]):
        records.append({
            "op": "S", "time_s": float(row["time_s"]),
            "input": [float(row[f"measured_{key}"]) for key in state_order],
            "before": [float(row[key]) for key in state_keys],
            "requested": [float(row[f"{a}_requested_Nm"]) for a in ("wheel", "hip")],
            "clipped": [float(row[f"{a}_clipped_Nm"]) for a in ("wheel", "hip")],
            "after": [float(after[key]) for key in state_keys],
        })
    return {"source": relative, "source_rows": "data rows 0..64", "records": records}


def synthetic_case(base, effects, delay, gain):
    import numpy as np
    from sim.augmented import AugmentedRuntime

    runtime = AugmentedRuntime(base, replace(effects, delay_s=delay / 1000))
    runtime.reset(np.zeros(6), seed=42)
    # Both signs/channels saturate. Resets at 2 ticks and 5 ticks exercise
    # pending commands and nonzero reconstructed torque, including 5 ms delay.
    operations = [
        ("S", [10, 0, 0, 0, 0, 0]),
        ("S", [-10, 0, 0, 0, 0, 0]),
        ("R", []),
        ("S", [0, 0, 0, 0, 0, 0]),
        ("A", [20, -40]),
        ("A", [-20, 40]),
        ("S", [0, 0, .02, 0, 0, -.01]),
        ("S", [0, 0, 0, 0, 0, 0]),
        ("R", []),
        *[("S", [0, 0, 0, 0, 0, 0]) for _ in range(7)],
    ]
    records = []
    for op, values in operations:
        before = runtime.observation().vector()[6:].tolist()
        if op == "R":
            runtime.reset(np.zeros(6), seed=42)
            raw = clipped = np.zeros(2)
        else:
            # Same -K@Observation.vector() feedback law as the Python runner,
            # with deliberate, externally supplied sensor stimuli for saturation.
            raw = (-np.asarray(gain) @ np.r_[values, before]
                   if op == "S" else np.asarray(values, dtype=float))
            result = runtime.step(raw)
            clipped = result.clipped
        records.append({
            "op": op, "input": values, "before": before,
            "requested": raw.tolist(), "clipped": clipped.tolist(),
            "after": runtime.observation().vector()[6:].tolist(),
        })
    return {
        "source": "Current Python -K@z and AugmentedRuntime.step/reset; synthetic sensor/actions",
        "plant_ticks": sum(op != "R" for op, _ in operations),
        "records": records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    from sim.augmented import load_experiment

    base, _, effects = load_experiment(ROOT / "sim/configs/assumed_actuator_noise.json")
    fixture = {
        "schema_version": 1,
        "archive": args.archive.name,
        "description": "Recorded controller parity only; no new full rollout or hardware validation",
        "source_sha256": {
            relative: digest(ROOT / relative) for relative in (
                "sim/augmented.py", "sim/augmented_lqr.py", "sim/augmented_eval.py",
                "sim/configs/assumed_planar.json", "sim/configs/assumed_actuator_noise.json",
            )
        },
        "dt_s": base["simulation"]["dt_s"],
        "motor_time_constant_s": list(effects.motor_time_constant_s),
        "torque_limits_Nm": [base["physics"][a + "_torque_limit"]["value"]
                            for a in ("wheel", "hip")],
        "profiles": [],
    }
    header = [
        "/* Extracted by record_fixtures.py from archived K_used; no synthesis.",
        " * See fixtures/recorded.json for source and gain hashes. */",
        "static const double gains[4][2][WBR_LQR_MAX_STATE] = {",
    ]
    for delay in (2, 3, 4, 5):
        source = args.archive / f"augmented_linearization_{delay}ms.json"
        design = json.loads(source.read_text())
        gain = design["K_used"]
        n = (delay + 1) // 2
        assert len(gain) == 2 and all(len(row) == 8 + 2 * n for row in gain)
        assert gain_digest(gain) == design["K_sha256"]
        assert design["delay_s"] == delay / 1000
        assert design["dt_s"] == fixture["dt_s"] == .002
        assert design["motor_time_constant_s"] == fixture["motor_time_constant_s"] == [.005, .005]
        profile = {
            "delay_ms": delay, "history_steps": n,
            "gain_source": source.name, "gain_source_sha256": digest(source),
            "K_sha256": design["K_sha256"], "K": gain,
            "archive_case": archive_case(args.archive, delay, base["controller"]["state_order"]),
            "synthetic_case": synthetic_case(base, effects, delay, gain),
        }
        fixture["profiles"].append(profile)
        header.append(f"    {{ /* {delay} ms; {design['K_sha256']} */")
        for row in gain:
            header.append("        {" + ", ".join(format(x, ".17g") for x in row) + "},")
        header.append("    },")
    header.append("};")
    (HERE / "gains.inc").write_text("\n".join(header) + "\n")
    (HERE / "fixtures").mkdir(exist_ok=True)
    # Keep each recorded vector on one line; avoid many thousands of scalar lines.
    text = json.dumps(fixture, indent=2, allow_nan=False)
    for profile in fixture["profiles"]:
        for name in ("archive_case", "synthetic_case"):
            for record in profile[name]["records"]:
                pretty = json.dumps(record, indent=2)
                indented = "\n".join("          " + line for line in pretty.splitlines())
                text = text.replace(indented, "          " + json.dumps(record, allow_nan=False))
    (HERE / "fixtures/recorded.json").write_text(text + "\n")
    print(f"Recorded {len(fixture['profiles'])} profiles, 256 archived ticks, "
          f"{sum(p['synthetic_case']['plant_ticks'] for p in fixture['profiles'])} synthetic ticks.")


if __name__ == "__main__":
    main()
