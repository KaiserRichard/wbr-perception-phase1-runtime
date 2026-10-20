"""Bounded host-only checks; no physics, synthesis, training or numpy import."""

import hashlib
import json
import math
import os
from pathlib import Path
import shlex
import struct
import subprocess
import tempfile
import time
import unittest


HERE = Path(__file__).resolve().parents[1]
TOLERANCE = 1e-6  # Absolute, zero relative tolerance, for every scalar compared.


class HostParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.started = time.monotonic()
        cls.fixture = json.loads((HERE / "fixtures/recorded.json").read_text())
        (HERE / ".build").mkdir(exist_ok=True)
        cls.build = Path(tempfile.mkdtemp(prefix="parity-", dir=HERE / ".build"))
        cls.host = cls.build / "host"
        command = [
            *shlex.split(os.environ.get("CC", "cc")), "-std=c99", "-O2",
            "-Wall", "-Wextra", "-Werror", "-pedantic", "-ffp-contract=off",
            str(HERE / "wbr_lqr.c"), str(HERE / "tests/host.c"), "-lm",
            "-o", str(cls.host),
        ]
        built = subprocess.run(command, capture_output=True, text=True, timeout=10)
        (cls.build / "compile.log").write_text(
            shlex.join(command) + "\n" + built.stdout + built.stderr)
        if built.returncode:
            raise RuntimeError(f"C build failed; see {cls.build / 'compile.log'}")
        cls.errors = {}

    @classmethod
    def tearDownClass(cls):
        report = {
            "max_absolute_errors": cls.errors,
            "tolerance": TOLERANCE,
            "elapsed_s": time.monotonic() - cls.started,
            "note": "Recorded controller replay; no new plant rollout or STM32 test",
        }
        (cls.build / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(f"\nHost artifacts: {cls.build}")
        print(f"Parity max absolute errors: {cls.errors}; "
              f"elapsed {report['elapsed_s']:.3f}s")

    def run_host(self, lines):
        run = subprocess.run([str(self.host)], input="\n".join(lines) + "\n",
                             capture_output=True, text=True, timeout=3)
        self.assertEqual(run.returncode, 0, run.stderr)
        rows = [[float(x) for x in line.split()] for line in run.stdout.splitlines()]
        self.assertEqual(len(rows), len(lines))
        return rows

    def assert_vector(self, actual, expected, label, tolerance=TOLERANCE):
        self.assertEqual(len(actual), len(expected), label)
        for index, (value, oracle) in enumerate(zip(actual, expected)):
            self.assertTrue(math.isfinite(value) and math.isfinite(oracle),
                            f"{label}[{index}] nonfinite")
            error = abs(value - oracle)
            self.errors[label.split("/")[0]] = max(
                self.errors.get(label.split("/")[0], 0), error)
            self.assertLessEqual(error, tolerance,
                                 f"{label}[{index}]: {value} vs {oracle}")

    def replay(self, profile, name):
        records = profile[name]["records"]
        lines = [f"I {profile['delay_ms']}"]
        for row in records:
            measurement = row["input"] if row["op"] == "S" else [0] * 6
            # Read before every operation; command() must not advance history.
            lines.append("C " + " ".join(map(repr, measurement)))
            lines.append(row["op"] + " " + " ".join(map(repr, row["input"])))
        actual = self.run_host(lines)
        for index, row in enumerate(records):
            label = f"{name}_{profile['delay_ms']}ms/{index}"
            before, after = actual[1 + 2 * index:3 + 2 * index]
            self.assert_vector(before[4:], row["before"], label + "/before")
            if row["op"] == "S":
                self.assert_vector(before[:2], row["requested"], label + "/read")
            expected = row["requested"] + row["clipped"] + row["after"]
            self.assert_vector(after, expected, label + "/after")

    def test_archived_python_controller_trajectories(self):
        """64 consecutive measured samples per delay; C owns its full history."""
        for profile in self.fixture["profiles"]:
            with self.subTest(delay_ms=profile["delay_ms"]):
                self.assertEqual(len(profile["archive_case"]["records"]), 64)
                self.replay(profile, "archive_case")

    def test_recorded_saturation_and_reset(self):
        """Both clipping signs/channels, pending reset, loaded-torque reset."""
        for profile in self.fixture["profiles"]:
            with self.subTest(delay_ms=profile["delay_ms"]):
                records = profile["synthetic_case"]["records"]
                self.assertEqual(records[0]["clipped"], [2, -4])
                self.assertEqual(records[1]["clipped"], [-2, 4])
                self.assertTrue(any(records[8]["before"][:2]))
                # Seven zero ticks after reset expose any stale pending arrival.
                for row in records[8:]:
                    self.assertEqual(row["after"], [0] * len(row["after"]))
                self.replay(profile, "synthetic_case")

    def test_exact_arrival_and_lag_step_response(self):
        """Independent analytic oracle catches 5 ms rounded to 4 or 6 ms."""
        for delay in (2, 3, 4, 5):
            rows = self.run_host([f"I {delay}"] + ["A 20 -40"] * 9)[1:]
            for tick, row in enumerate(rows, 1):
                active_time = max(0., tick * .002 - delay / 1000)
                response = -math.expm1(-active_time / .005)
                self.assert_vector(row[4:6], [2 * response, -4 * response],
                                   f"analytic_{delay}ms/{tick}", tolerance=1e-14)
                self.assertEqual(row[2:4], [2, -4])
                if tick * 2 <= delay:
                    self.assertEqual(row[4:6], [0, 0])

    def test_reset_discards_every_pending_command(self):
        for delay in (2, 3, 4, 5):
            for ticks in (1, 2, 6):
                lines = [f"I {delay}"] + ["A 1 -2"] * ticks + ["R"] + ["A 0 0"] * 8
                rows = self.run_host(lines)
                for row in rows[ticks + 2:]:
                    self.assertEqual(row, [0] * len(row), (delay, ticks))

    def test_host_api_invalid_inputs_and_separate_instances(self):
        run = subprocess.run([str(self.host), "--unit"], capture_output=True,
                             text=True, timeout=3)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("host unit checks passed", run.stdout)

    def test_frozen_gain_identity_and_fixture_contract(self):
        self.assertEqual(self.fixture["dt_s"], .002)
        self.assertEqual(self.fixture["motor_time_constant_s"], [.005, .005])
        self.assertEqual(self.fixture["torque_limits_Nm"], [2, 4])
        self.assertEqual([p["delay_ms"] for p in self.fixture["profiles"]], [2, 3, 4, 5])
        for profile in self.fixture["profiles"]:
            packed = b"".join(struct.pack("<d", x) for row in profile["K"] for x in row)
            self.assertEqual(hashlib.sha256(packed).hexdigest(), profile["K_sha256"])
            for row in profile["K"]:
                self.assertEqual(len(row), 8 + 2 * profile["history_steps"])


if __name__ == "__main__":
    unittest.main()
