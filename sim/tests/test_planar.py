import copy
import csv
import json
from pathlib import Path
import tempfile
import unittest

import mujoco
import numpy as np

from sim.lqr import synthesize
from sim.planar import Plant, TO_JOINT, finite_difference, load_config, parameters
from sim.run_planar import evaluate


CONFIG = Path(__file__).resolve().parents[1] / "configs" / "assumed_planar.json"


class PlanarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_config(CONFIG)
        cls.plant = Plant(cls.cfg)
        cls.K, cls.design = synthesize(cls.plant)

    def test_three_independent_coordinates_and_only_two_torque_actuators(self):
        m = self.plant.model
        self.assertEqual((m.nq, m.nv, m.nu, m.neq), (3, 3, 2, 0))
        np.testing.assert_array_equal(m.jnt_stiffness, 0.)
        np.testing.assert_array_equal(m.dof_damping, 0.)
        np.testing.assert_array_equal(m.dof_frictionloss, 0.)
        np.testing.assert_array_equal(m.body_gravcomp, 0.)
        self.assertEqual(m.opt.integrator, mujoco.mjtIntegrator.mjINT_RK4)
        np.testing.assert_allclose(m.opt.gravity, [0, 0, -9.81])
        state = np.array([0.1, 0.2, -0.3, 0.4, -0.2, 0.6])
        d = self.plant.data(state)
        np.testing.assert_allclose(self.plant.state(d), state, atol=1e-15)
        np.testing.assert_allclose(d.xmat[self.plant.body_id].reshape(3, 3)[:, 2],
                                   [np.sin(state[2]), 0, np.cos(state[2])], atol=1e-15)
        self.assertEqual(d.nefc, 0)

    def test_nonlinear_forward_dynamics_against_independent_lagrange_equations(self):
        # This analytical oracle is test-only; the actual plant uses mj_step.
        p = parameters(self.cfg)
        mw, ml, mb = p["wheel_mass"], p["leg_mass"], p["body_mass"]
        r, L, a, b = p["wheel_radius"], p["leg_length"], p["leg_com"], p["body_com"]
        coupling = mb * L * b
        G = np.array([[1 / r, 0], [-1, -1], [0, 1]])
        rng = np.random.default_rng(20261020)
        for _ in range(20):
            state = rng.uniform(-0.4, 0.4, 6)
            u = rng.uniform(-0.7, 0.7, 2)
            _, th, ph, _, td, pd = state
            M = np.array([
                [mw + p["wheel_inertia"] / r**2 + ml + mb,
                 (ml*a + mb*L)*np.cos(th), mb*b*np.cos(ph)],
                [(ml*a + mb*L)*np.cos(th), p["leg_inertia"] + ml*a*a + mb*L*L,
                 coupling*np.cos(th-ph)],
                [mb*b*np.cos(ph), coupling*np.cos(th-ph), p["body_inertia"] + mb*b*b],
            ])
            bias = np.array([
                -(ml*a + mb*L)*np.sin(th)*td**2 - mb*b*np.sin(ph)*pd**2,
                coupling*np.sin(th-ph)*pd**2 - (ml*a + mb*L)*p["gravity"]*np.sin(th),
                -coupling*np.sin(th-ph)*td**2 - mb*b*p["gravity"]*np.sin(ph),
            ])
            expected = np.r_[state[3:], np.linalg.solve(M, G @ u - bias)]
            np.testing.assert_allclose(self.plant.derivative(state, u), expected, rtol=2e-12, atol=2e-12)

    def test_motor_virtual_work_reactions_and_mujoco_clipping(self):
        p = parameters(self.cfg)
        d = self.plant.data()
        # Deliberately bypass Python clipping; MuJoCo must enforce its own caps.
        self.plant.forward(d, [100, -100])
        wheel, hip = self.plant.limits * [1, -1]
        np.testing.assert_allclose(d.actuator_force, [wheel, hip])
        absolute_force = TO_JOINT.T @ d.qfrc_actuator
        np.testing.assert_allclose(absolute_force, [wheel/p["wheel_radius"], -wheel-hip, hip])
        # Opposite hip torque acts on the leg; no grounded orientation servo.
        self.plant.forward(d, [0., 0.])
        np.testing.assert_array_equal(d.qfrc_actuator, 0)
        np.testing.assert_array_equal(d.qfrc_passive, 0)

    def test_body_push_at_com_has_correct_generalized_force(self):
        state = np.array([0., 0.2, -0.1, 0., 0., 0.])
        d = self.plant.data(state)
        self.plant.forward(d, [0, 0], push=6)
        pushed = d.qacc.copy()
        self.plant.forward(d, [0, 0], push=0)
        M = np.zeros((3, 3))
        mujoco.mj_fullM(self.plant.model, M, d.qM)
        generalized = TO_JOINT.T @ M @ (pushed - d.qacc)
        p = parameters(self.cfg)
        np.testing.assert_allclose(generalized, 6*np.array([
            1., p["leg_length"]*np.cos(state[1]), p["body_com"]*np.cos(state[2])
        ]), rtol=1e-12, atol=1e-12)

    def test_riccati_residuals_controllability_and_sampled_poles(self):
        d = self.design
        self.assertEqual(d["continuous_controllability"]["rank"], 6)
        self.assertEqual(d["discrete_controllability"]["rank"], 6)
        self.assertLess(d["CARE_relative_residual"], 1e-8)
        self.assertLess(d["DARE_relative_residual"], 1e-8)
        self.assertLess(d["equilibrium_derivative_max_abs"], 1e-12)
        self.assertGreater(max(v[0] for v in d["continuous_open_loop_eigenvalues"]), 1.)
        self.assertLess(max(np.hypot(*v) for v in d["discrete_closed_loop_eigenvalues"]), 1.)
        self.assertLess(d["actual_vs_zoh_A_max_abs"], 1e-7)
        self.assertLess(d["actual_vs_zoh_B_max_abs"], 1e-7)

    def test_finite_differences_converge_and_predict_real_steps(self):
        A, B = finite_difference(self.plant.transition, 1e-5)
        Ad = np.array(self.design["A_discrete_actual"])
        Bd = np.array(self.design["B_discrete_actual"])
        np.testing.assert_allclose(A, Ad, atol=1e-9, rtol=1e-8)
        np.testing.assert_allclose(B, Bd, atol=1e-9, rtol=1e-8)
        rng = np.random.default_rng(42)
        for _ in range(10):
            x, u = rng.normal(size=6)*1e-4, rng.normal(size=2)*1e-4
            np.testing.assert_allclose(self.plant.transition(x, u), Ad @ x + Bd @ u, atol=1e-10, rtol=1e-6)

    def test_timestep_changes_actual_discretization(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["simulation"]["dt_s"] *= 0.5
        smaller = Plant(cfg)
        Ah, Bh = finite_difference(smaller.transition, 1e-6)
        A, B = np.array(self.design["A_discrete_actual"]), np.array(self.design["B_discrete_actual"])
        np.testing.assert_allclose(A, Ah @ Ah, atol=1e-7, rtol=1e-7)
        np.testing.assert_allclose(B, Ah @ Bh + Bh, atol=1e-7, rtol=1e-7)

    def test_passive_energy_conservation_and_gravity_driven_instability(self):
        d = self.plant.data(self.cfg["protocol"]["initial_state"])
        initial_energy = sum(d.energy)
        for _ in range(100):
            self.plant.forward(d, [0, 0])
            mujoco.mj_step(self.plant.model, d)
        self.plant.forward(d, [0, 0])
        self.assertLess(abs(sum(d.energy) - initial_energy), 1e-6)
        self.assertGreater(max(abs(self.plant.state(d)[1:3])),
                           max(abs(np.array(self.cfg["protocol"]["initial_state"])[1:3])))

    def test_full_protocol_and_csv_impulse_accounting(self):
        # Keep each test artifact outside git, including any failed trajectory.
        out = Path(tempfile.mkdtemp(prefix="wbr-planar-tests-"))
        results = {}
        for scenario in ("balance", "push", "open_loop"):
            result, _ = evaluate(self.plant, self.K, scenario, out)
            (out / f"{scenario}.json").write_text(json.dumps(result, indent=2))
            results[scenario] = result
            self.assertEqual(result["status"], "PASS", f"{scenario}: {result}; retained at {out}")
        with (out / "push.csv").open() as f:
            rows = list(csv.DictReader(f))
        impulse = sum(float(row["push_N"])*float(row["interval_dt_s"]) for row in rows)
        self.assertAlmostEqual(impulse, 0.9, places=12)
        self.assertAlmostEqual(sum(float(row["interval_dt_s"]) for row in rows), 10, places=10)
        self.assertEqual(results["push"]["integration_steps"], 5000)
        self.assertTrue(results["open_loop"]["fallen"])
        self.assertFalse(results["balance"]["fallen"])
        self.assertFalse(results["push"]["fallen"])

    def test_zero_controller_cannot_pass_balance(self):
        out = Path(tempfile.mkdtemp(prefix="wbr-planar-negative-"))
        result, _ = evaluate(self.plant, np.zeros((2, 6)), "balance", out)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(result["fallen"])

    def test_care_option_is_also_stable_at_actual_sample_time(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["controller"]["solver"] = "CARE"
        _, result = synthesize(Plant(cfg))
        self.assertLess(max(np.hypot(*v) for v in result["discrete_closed_loop_eigenvalues"]), 1.)


if __name__ == "__main__":
    unittest.main()
