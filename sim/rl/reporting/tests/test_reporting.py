"""Small analytic fixtures; never import the simulator or training stack."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

from sim.rl.reporting.report import METRICS, Reader, load_report, write_report


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def summary(n, value):
    return {"mean": value, "available_only_mean": value,
            "available_episodes": n, "total_episodes": n}


def v1_fixture(root):
    def panel(n, success, duration):
        return {"episodes": n, "success_rate": success,
                "duration_s": summary(n, duration),
                "recovery_time_after_event_s": summary(n, 2.),
                "penalized_recovery_s": summary(n, 2.),
                "command_effort_Nm2_s": summary(n, [1., 3.]),
                "applied_effort_Nm2_s": summary(n, [0.5, 1.5])}
    data = {"n_training_seed_slots": 2, "all_five_full_budget_policies": False,
            "panels": {"lqr": {"2ms-balance": panel(1, 1., 10.), "2ms-push": panel(3, 1., 10.)},
                       "ppo-0": {"2ms-balance": panel(1, 1., 2.), "2ms-push": panel(3, 0., 6.)}}}
    data["panels"]["ppo-0"]["2ms-push"]["recovery_time_after_event_s"] = {
        "mean": None, "available_only_mean": 4., "available_episodes": 1, "total_episodes": 3}
    path = root / "v1/evaluation/aggregate.json"
    save(path, data)
    return path, data


def v2_fixture(root):
    root = root / "v2"
    declaration = {"smoke": False,
                   "config": {"arms": ["direct", "residual"], "policy_hold_ticks": 5,
                              "training": {"initial_seeds": [0, 1], "extension_seeds": [2]},
                              "smoke": {"evaluation_cases_per_arm": 1}},
                   "v1_protocol": {"plant": {"control_period_s": .002, "fixed_delays_s": [.002]},
                                   "scenarios": [{"name": "balance"}, {"name": "push"}],
                                   "evaluation": {"noise_seeds": [10, 11]}}}
    save(root / "run.json", declaration)
    save(root / "status.json", {"status": "COMPLETE_WITH_FAILURES",
                               "extensions": {"direct": True, "residual": False}})
    save(root / "direct/seed-0/status.json", {"status": "COMPLETE", "policy_transitions": 100,
                                              "budget": 100})
    rows = []
    for scenario in ["balance", "push"]:
        for noise in [10, 11]:
            rows.append({"controller": "direct", "policy_seed": 0, "delay_s": .002,
                         "scenario": scenario, "noise_seed": noise, "success": noise == 10,
                         "survived": True, "duration_s": 10.,
                         "recovery_time_after_event_s": 2. if noise == 10 else None,
                         "penalized_recovery_s": 2. if noise == 10 else 10.,
                         "command_effort_Nm2_s": [2., 4.], "applied_effort_Nm2_s": [1., 3.]})
    save(root / "direct/seed-0/evaluation/outcomes.json", rows)
    return root, declaration, rows


def overall(report, version, controller, seed):
    return next(r for r in report["rows"] if (r["version"], r["controller"], r["seed"], r["condition"])
                == (version, controller, seed, "all"))


class SavedEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_v1_weighted_metrics_and_unknown_survival_rate(self):
        path, _ = v1_fixture(self.root)
        r = overall(load_report(path), "v1", "ppo", 0)
        self.assertEqual(r["strict_success"]["rate"], .25)
        self.assertEqual(r["duration_s"]["mean"], 5.)  # (1*2 + 3*6)/4
        self.assertIsNone(r["survival"]["rate"])
        self.assertIsNone(r["policy_action_hz"])  # No archived protocol, no guessed rate.

    def test_partial_recovery_preserves_weighted_available_only_diagnostic(self):
        path, _ = v1_fixture(self.root)
        r = overall(load_report(path), "v1", "ppo", 0)["recovery_time_after_event_s"]
        self.assertIsNone(r["mean"])
        self.assertEqual(r["available_only_mean"], 3.)
        self.assertEqual((r["available_episodes"], r["total_episodes"]), (2, 4))

    def test_missing_seed_not_dropped_or_invented(self):
        path, _ = v1_fixture(self.root)
        r = overall(load_report(path), "v1", "ppo", 1)
        self.assertEqual((r["observed_episodes"], r["expected_episodes"]), (0, 4))
        self.assertIsNone(r["strict_success"]["count"])
        self.assertIsNone(r["duration_s"]["mean"])

    def test_missing_policy_saved_failures_stay_zero_success_null_physical(self):
        path, data = v1_fixture(self.root)
        missing = copy.deepcopy(data["panels"]["lqr"])
        for p in missing.values():
            p["success_rate"] = 0.
            for key in METRICS:
                p[key] = {"mean": None, "available_only_mean": None, "available_episodes": 0}
            p["penalized_recovery_s"] = summary(p["episodes"], 10.)
        data["panels"]["ppo-1"] = missing
        save(path, data)
        r = overall(load_report(path), "v1", "ppo", 1)
        self.assertEqual(r["strict_success"]["rate"], 0.)
        self.assertEqual(r["penalized_recovery_s"]["mean"], 10.)
        self.assertIsNone(r["recovery_time_after_event_s"]["mean"])

    def test_v2_strict_survival_null_recovery_and_held_action_rate(self):
        root, _, _ = v2_fixture(self.root)
        r = overall(load_report(v2_root=root), "v2", "direct", 0)
        self.assertEqual(r["strict_success"]["rate"], .5)
        self.assertEqual(r["survival"]["rate"], 1.)
        self.assertEqual((r["policy_action_hz"], r["plant_control_hz"]), (100., 500.))
        self.assertIsNone(r["recovery_time_after_event_s"]["mean"])
        self.assertEqual(r["recovery_time_after_event_s"]["available_episodes"], 2)
        self.assertEqual(r["penalized_recovery_s"]["mean"], 6.)
        self.assertEqual(r["applied_effort_Nm2_s"]["mean"], [1., 3.])

    def test_v2_missing_and_conditional_extension_seeds(self):
        root, _, _ = v2_fixture(self.root)
        report = load_report(v2_root=root)
        for seed in [1, 2]:
            r = overall(report, "v2", "direct", seed)
            self.assertEqual(r["expected_episodes"], 4)
            self.assertIsNone(r["strict_success"]["rate"])
        r = overall(report, "v2", "residual", 2)
        self.assertEqual(r["state"], "NOT_SCHEDULED")
        self.assertEqual(r["expected_episodes"], 0)

    def test_v2_interrupted_evaluation_reads_only_compact_json(self):
        root, _, rows = v2_fixture(self.root)
        # Use another seed, so no complete outcomes file exists.
        row = dict(rows[0], policy_seed=1)
        folder = root / "direct/seed-1/evaluation"
        save(folder / "d2-balance-n10.json", row)
        (folder / "d2-balance-n10.npz").write_bytes(b"deliberately unreadable trajectory")
        r = overall(load_report(v2_root=root), "v2", "direct", 1)
        self.assertEqual(r["observed_episodes"], 1)
        self.assertEqual(r["strict_success"]["count"], 1)
        self.assertIsNone(r["strict_success"]["rate"])
        self.assertEqual(r["duration_s"]["available_only_mean"], 10.)
        self.assertIsNone(r["duration_s"]["mean"])

    def test_v2_rejects_duplicates_and_identity_mismatch(self):
        root, _, rows = v2_fixture(self.root)
        for bad in [rows + [rows[0]], [dict(rows[0], policy_seed=9)], [dict(rows[0], noise_seed=99)]]:
            save(root / "direct/seed-0/evaluation/outcomes.json", bad)
            with self.assertRaisesRegex(ValueError, "identity"):
                load_report(v2_root=root)

    def test_v1_unexpected_seed_cannot_be_silently_selected_or_dropped(self):
        path, data = v1_fixture(self.root)
        data["panels"]["ppo-99"] = data["panels"]["lqr"]
        save(path, data)
        with self.assertRaisesRegex(ValueError, "declared seed"):
            load_report(path)

    def test_unknown_extension_not_counted_as_failed_seed(self):
        root, _, _ = v2_fixture(self.root)
        save(root / "status.json", {"status": "RUNNING"})
        r = overall(load_report(v2_root=root), "v2", "residual", 2)
        self.assertEqual(r["state"], "EXTENSION_UNDECIDED")
        self.assertEqual(r["expected_episodes"], 0)

    def test_smoke_has_separate_label_and_smoke_denominator(self):
        root, declaration, rows = v2_fixture(self.root)
        declaration["smoke"] = True
        save(root / "run.json", declaration)
        save(root / "direct/seed-0/evaluation/outcomes.json", rows[:1])
        r = overall(load_report(v2_root=root), "v2-smoke", "direct", 0)
        self.assertEqual(r["expected_episodes"], 1)
        self.assertEqual(r["strict_success"]["rate"], 1.)

    def test_v2_malformed_torque_vector_fails_before_output(self):
        root, _, rows = v2_fixture(self.root)
        rows[0]["applied_effort_Nm2_s"] = [1., 2., 3.]
        save(root / "direct/seed-0/evaluation/outcomes.json", rows)
        with self.assertRaisesRegex(ValueError, "wheel, hip"):
            load_report(v2_root=root)

    def test_combined_outputs_reference_once_and_figures_parse(self):
        path, _ = v1_fixture(self.root)
        root, _, _ = v2_fixture(self.root)
        report = load_report(path, root)
        output = self.root / "output"
        write_report(report, output, [path.parent, root])
        self.assertEqual(sum(r["controller"] == "lqr" and r["condition"] == "all" for r in report["rows"]), 1)
        for figure in output.glob("*.svg"):
            ET.parse(figure)
        self.assertEqual(len(list(output.glob("*.svg"))), 7)
        self.assertIn("available-only", (output / "comparison.md").read_text())
        self.assertIn("training_budget", (output / "comparison.csv").read_text())
        self.assertIn("NA", (output / "survival.svg").read_text())

    def test_output_cannot_overwrite_input_or_git(self):
        path, _ = v1_fixture(self.root)
        report = load_report(path)
        for output in [path.parent / "report", Path(__file__).resolve().parent / "forbidden"]:
            with self.assertRaisesRegex(ValueError, "outside"):
                write_report(report, output, [path.parent])
        output = self.root / "already-exists"
        output.mkdir()
        with self.assertRaises(FileExistsError):
            write_report(report, output)

    def test_input_budget_and_nonfinite_rejected(self):
        path = self.root / "large.json"
        with path.open("wb") as stream:
            stream.truncate(17 * 1024**2)
        with self.assertRaisesRegex(ValueError, "budget"):
            Reader().read(path)
        path = self.root / "nan.json"
        path.write_text('{"value": NaN}')
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            Reader().read(path)

    def test_cli_uses_no_simulator_dependencies(self):
        path, _ = v1_fixture(self.root)
        result = subprocess.run([sys.executable, "-S", "-m", "sim.rl.reporting", "--v1-aggregate",
                                 str(path), "--out", str(self.root / "cli")],
                                capture_output=True, text=True, timeout=3)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no replay", result.stdout)


if __name__ == "__main__":
    unittest.main()
