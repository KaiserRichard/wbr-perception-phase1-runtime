"""The declared 64-step CartPole optimizer smoke is not WBR training."""

import unittest

import torch
from stable_baselines3 import PPO

from sim.rl.environment import load_protocol
from sim.rl.training import single_thread


class BackendTests(unittest.TestCase):
    def test_declared_cartpole_smoke_updates_finite_parameters(self):
        cfg = load_protocol()["smoke"]
        single_thread()
        model = PPO("MlpPolicy", cfg["environment"], device=cfg["device"],
                    seed=cfg["seed"], n_steps=cfg["n_steps"],
                    batch_size=cfg["batch_size"], n_epochs=cfg["n_epochs"])
        before = {k: v.detach().clone() for k, v in model.policy.state_dict().items()}
        try:
            model.learn(total_timesteps=cfg["steps"])
            self.assertEqual(model.num_timesteps, 64)
            after = model.policy.state_dict()
            self.assertTrue(any(not torch.equal(before[k], v) for k, v in after.items()))
            self.assertTrue(all(torch.isfinite(v).all() for v in after.values()))
            self.assertFalse(cfg["counts_as_training_seed"])
        finally:
            model.get_env().close()
