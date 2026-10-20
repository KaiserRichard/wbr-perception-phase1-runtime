"""Protect the predeclared comparison against drift; no RL training here."""
import json
import math
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
PROTOCOL = ROOT / "sim/rl/protocol.json"


def strict_json(text):
    def invalid(token):
        raise ValueError(f"Non-finite JSON token: {token}")

    def finite_float(token):
        number = float(token)
        return number if math.isfinite(number) else invalid(token)

    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(text, parse_constant=invalid, parse_float=finite_float,
                      object_pairs_hook=unique_keys)


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = strict_json(PROTOCOL.read_text())
        cls.base = strict_json((ROOT / cls.p["baseline"]["config"]).read_text())

    def test_strict_json_rejects_nonfinite_and_duplicate_keys(self):
        for invalid in ('{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}',
                        '{"x":1e999}', '{"x":1,"x":2}', '{"x":1,}'):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                strict_json(invalid)
        self.assertEqual(self.p, strict_json(json.dumps(self.p, allow_nan=False)))

    def test_training_and_evaluation_seeds_are_distinct_and_paired(self):
        train = self.p["training"]["policy_seeds"]
        heldout = self.p["evaluation"]["noise_seeds"]
        self.assertEqual(train, list(range(5)))
        self.assertEqual(len(set(train)), 5)
        self.assertEqual(heldout, list(range(1000, 1020)))
        self.assertEqual(len(set(heldout)), 20)
        self.assertTrue(set(train).isdisjoint(heldout))
        # Every possible training episode gets a reserved integer outside the
        # held-out range; the runtime internally splits angle/gyro streams.
        rng = self.p["rng"]
        stride = rng["training_noise_seed_stride"]
        self.assertEqual(stride, self.p["training"]["steps_per_seed"])
        ranges = [(rng["training_noise_seed_base"] + stride * seed,
                   rng["training_noise_seed_base"] + stride * (seed + 1))
                  for seed in train]
        for start, stop in ranges:
            self.assertTrue(all(not start <= seed < stop for seed in heldout))
        self.assertTrue(all(a[1] <= b[0] for a, b in zip(ranges, ranges[1:])))
        self.assertTrue(self.p["evaluation"]["held_out"])
        self.assertFalse(self.p["evaluation"]["tuning_on_evaluation"])
        self.assertIn("every delay x scenario, controller and PPO policy seed",
                      self.p["evaluation"]["pairing"])

    def test_scenarios_preserve_approved_initial_conditions_and_pulse(self):
        scenarios = self.p["scenarios"]
        baseline = self.base["protocol"]
        self.assertEqual([s["name"] for s in scenarios], ["balance", "push"])
        for scenario in scenarios:
            self.assertEqual(scenario["duration_s"], 10.0)
            self.assertEqual(scenario["initial_state"], baseline["initial_state"])
        self.assertIsNone(scenarios[0]["push"])
        pulse = scenarios[1]["push"]
        self.assertEqual(pulse["force_N"], baseline["push_force_N"])
        self.assertEqual(pulse["start_s"], 3.0)
        self.assertEqual(pulse["end_exclusive_s"], 3.15)
        self.assertAlmostEqual(pulse["force_N"] *
                               (pulse["end_exclusive_s"] - pulse["start_s"]), 0.9)
        self.assertEqual(pulse["impulse_Ns"], 0.9)
        self.assertIn("body COM", pulse["location"])
        for name in ("fall_angle_deg", "max_displacement_m", "state_abs_tolerance",
                     "settle_window_s", "recovery_deadline_s"):
            self.assertEqual(self.p["acceptance"][name], baseline[name])

    def test_same_augmented_plant_controls_and_available_information(self):
        plant, obs = self.p["plant"], self.p["observations"]
        self.assertEqual(plant["shared_by"], ["ppo", "lqr"])
        self.assertEqual(obs["shared_by"], plant["shared_by"])
        self.assertEqual(plant["control_period_s"], 0.002)
        self.assertEqual(plant["fixed_delays_s"], [0.002, 0.003, 0.004, 0.005])
        self.assertEqual(plant["motor_lag_s"], 0.005)
        self.assertEqual(plant["torque_limits_Nm"], [2.0, 4.0])
        self.assertEqual(plant["body_angle_noise_std_deg"], 0.1)
        self.assertEqual(plant["body_gyro_noise_std_rad_s"], 0.01)
        self.assertEqual(obs["sensor_order"], self.base["controller"]["state_order"])
        self.assertEqual(obs["history_steps"], 3)
        self.assertEqual(self.p["policy_input"]["dimension"],
                         len(obs["sensor_order"]) + 2 + 2 * obs["history_steps"] + 1)
        self.assertEqual(self.p["policy_input"]["dimension"], 15)
        self.assertEqual(self.p["policy_input"]["delay_divisor_s"], 0.005)
        self.assertIn("right-pad", obs["history"])
        self.assertEqual(obs["true_state_use"], ["reward", "evaluation"])
        self.assertIn("privileged critic state", obs["forbidden"])
        self.assertIn("true motor/filter/queue state", obs["forbidden"])

    def test_full_budget_has_no_rollout_rounding_or_smoke_substitution(self):
        training, hyper = self.p["training"], self.p["ppo_hyperparameters"]
        self.assertEqual(training["steps_per_seed"], 150000)
        self.assertEqual(training["n_envs"], 1)
        rollout_size = hyper["n_steps"] * training["n_envs"]
        self.assertEqual(training["steps_per_seed"] % rollout_size, 0)
        self.assertEqual(rollout_size % hyper["batch_size"], 0)
        self.assertGreater(hyper["batch_size"], 1)
        self.assertFalse(training["sweeps"])
        self.assertFalse(self.p["smoke"]["counts_as_training_seed"])
        self.assertEqual(self.p["smoke"]["steps"], 64)
        self.assertLess(self.p["smoke"]["steps"], training["steps_per_seed"])
        self.assertIn("Final checkpoint", training["checkpoint_selection"])
        self.assertIn("Retain all", training["failed_seeds"])

    def test_evaluation_counts_do_not_duplicate_lqr(self):
        evaluation = self.p["evaluation"]
        count = (len(evaluation["noise_seeds"]) *
                 len(self.p["plant"]["fixed_delays_s"]) *
                 len(self.p["scenarios"]))
        self.assertEqual(evaluation["episodes_per_policy"], count)
        self.assertEqual(evaluation["lqr_unique_episodes"], count)
        self.assertEqual(evaluation["ppo_episodes_total"],
                         count * len(self.p["training"]["policy_seeds"]))
        self.assertTrue(evaluation["deterministic_policy"])
        self.assertEqual(self.p["aggregation"]["unit"], "training seed")
        self.assertIn("paired 95% CI", self.p["aggregation"]["claim_rule"])

    def test_direct_torque_fixed_ppo_and_reward_are_declared(self):
        self.assertEqual(self.p["ppo"]["algorithm"], "PPO")
        self.assertEqual(self.p["ppo"]["control"], "direct torque")
        self.assertFalse(self.p["ppo"]["residual_lqr"])
        self.assertEqual(self.p["ppo"]["device"], "cpu")
        self.assertEqual(self.p["ppo"]["threads"], 1)
        self.assertEqual(self.p["ppo_hyperparameters"]["n_steps"], 1000)
        self.assertEqual(self.p["ppo_hyperparameters"]["batch_size"], 250)
        self.assertEqual(self.p["ppo_hyperparameters"]["gamma"], 0.9995)
        self.assertEqual(self.p["ppo_policy_kwargs"]["net_arch"],
                         {"pi": [64, 64], "vf": [64, 64]})
        for name in ("Q_diagonal", "R_diagonal"):
            self.assertEqual(self.p["reward"][name], self.base["controller"][name])
        self.assertIn("bootstrapping", self.p["episode_end"]["truncated"])

    def test_metrics_include_failures_recovery_tracking_and_actuation(self):
        metrics = self.p["metrics"]
        for name in ("success_rate", "fall_count", "training_failure_count",
                     "numerical_failure_count"):
            self.assertIn(name, metrics["outcomes"])
        for name in ("recovery_time_successes_s", "unrecovered_count",
                     "penalized_recovery_s"):
            self.assertIn(name, metrics["recovery"])
        for name in ("peak_leg_tilt_deg", "peak_body_tilt_deg", "state_rmse",
                     "peak_tilt_after_push_start_deg", "final_window_max_abs_error"):
            self.assertIn(name, metrics["kinematics"])
        for name in ("command_effort_Nm2_s", "applied_effort_Nm2_s",
                     "peak_command_torque_Nm", "peak_applied_torque_Nm",
                     "command_saturation_fraction", "command_saturation_duration_s"):
            self.assertIn(name, metrics["actuation"])
        self.assertIn("null", metrics["failure_reporting"])

    def test_pins_keep_the_intel_backend_and_existing_plant(self):
        requirements = (PROTOCOL.parent / "requirements.txt").read_text().splitlines()
        for pin in ("-r ../requirements.lock", "torch==2.2.2",
                    "stable-baselines3==2.3.2", "gymnasium==0.29.1"):
            self.assertIn(pin, requirements)
        base_pins = (ROOT / "sim/requirements.lock").read_text().splitlines()
        self.assertIn("mujoco==3.3.7", base_pins)
        self.assertIn("numpy==1.26.4", base_pins)


if __name__ == "__main__":
    unittest.main()
