"""Failure-inclusive paired statistics, with independent analytic examples."""

import copy
import math
import unittest

import numpy as np

from sim.rl.aggregate import aggregate, five_seed_interval
from sim.rl.metrics import missing_policy, PHYSICAL


def fixture():
    rows = []
    for controller, seed in [('lqr', None), *[('ppo', s) for s in range(5)]]:
        for delay in [.002, .003, .004, .005]:
            for scenario in ['balance', 'push']:
                for noise in range(1000, 1020):
                    row = missing_policy('fixture')
                    row.update(controller=controller, policy_seed=seed, delay_s=delay,
                               scenario=scenario, noise_seed=noise, status='PASS',
                               success=controller == 'lqr' or noise - 1000 < 4 * (seed + 1),
                               training_failure_count=0, duration_s=10., penalized_recovery_s=1.)
                    rows.append(row)
    return rows


class AggregateTests(unittest.TestCase):
    def test_five_seed_t_interval_df4_not_800_episode_ci(self):
        result = five_seed_interval([-.8, -.6, -.4, -.2, 0.])
        mean, sd = -.4, math.sqrt(.4 / 4)
        margin = 2.7764451051977987 * sd / math.sqrt(5)
        self.assertAlmostEqual(result['mean'], mean)
        self.assertAlmostEqual(result['sample_sd'], sd)
        np.testing.assert_allclose(result['ci95'], [mean - margin, mean + margin], atol=1e-12)
        self.assertEqual(result['df'], 4)
        with self.assertRaises(ValueError):
            five_seed_interval([0.] * 800)

    def test_exact_pairing_and_seed_weighting(self):
        rows = fixture()
        result = aggregate(rows, {s: {'complete': True} for s in range(5)})
        np.testing.assert_allclose(result['primary_ppo_success_rates'], [.2, .4, .6, .8, 1.])
        np.testing.assert_allclose(result['primary_paired_ppo_minus_lqr']['seed_values'], [-.8, -.6, -.4, -.2, 0.])
        self.assertEqual(result['unique_lqr_episodes'], 160)
        self.assertFalse(result['rl_superiority_supported'])
        for invalid in (rows[:-1], rows + [rows[0]]):
            with self.assertRaises(ValueError):
                aggregate(invalid, {s: {'complete': True} for s in range(5)})

    def test_missing_seed_zero_success_null_physical_and_retained_denominators(self):
        rows = fixture()
        for row in rows:
            if row['policy_seed'] == 2:
                row.update(missing_policy('retained training failure'))
        result = aggregate(rows, {s: {'complete': s != 2} for s in range(5)})
        self.assertEqual(result['primary_ppo_success_rates'][2], 0.)
        self.assertEqual(result['failure_counts_all_outcomes']['training_failure_count'], 160)
        panel = result['panels']['ppo-2']['2ms-balance']
        self.assertEqual(panel['duration_s']['available_episodes'], 0)
        self.assertIsNone(panel['duration_s']['mean'])
        self.assertIsNone(result['secondary_paired_differences_descriptive']['duration_s']['mean'])
        self.assertFalse(result['claim_eligible'])
        self.assertEqual(panel['penalized_recovery_s']['mean'], 10.)
        missing = missing_policy('none')
        self.assertTrue(all(missing[k] is None for k in PHYSICAL))
        self.assertIsNone(missing['fall_observed'])
