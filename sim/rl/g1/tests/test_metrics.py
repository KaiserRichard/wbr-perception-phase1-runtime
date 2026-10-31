import copy
import unittest
from types import SimpleNamespace
import numpy as np
from sim.rl.g1.metrics import compare,episode_metrics
from sim.rl.g1.protocol import panel,TOL


class MetricsTests(unittest.TestCase):
    def test_thresholds_and_failed_precision(self):
        times=np.arange(5001)*.002
        samples=[(t,np.zeros(6),np.zeros(2),np.zeros(2),0.,0.) for t in times]
        env=SimpleNamespace(samples=samples,actions=[(0.,0.,0.)]*1000,case={'command':0.},failed=False,
                            runtime=SimpleNamespace(limits=np.array([2.,4.])),numerical=False,collision=False,
                            rejects=0,clips=0,actuator_clips=0)
        self.assertTrue(episode_metrics(env)['strict'])
        for j in range(4500,5001):
            e=np.zeros(6);e[0]=.020001
            samples[j]=(times[j],e,np.zeros(2),np.zeros(2),0.,0.)
        self.assertFalse(episode_metrics(env)['strict'])
        env.failed=True
        self.assertIsNone(episode_metrics(env)['E'])
        self.assertFalse(episode_metrics(env)['survived'])

    def test_five_seed_paired_interval_and_individual_engineering(self):
        cases=panel()
        def row(case,strict):
            return dict(case=case,strict=strict,survived=True,caps_respected=True,numerical_failure=False,E=0.,E_observed=0.)
        # Baseline80% difficult,100% reference; governor100% for each seed.
        A=[row(c,not(c['delay_s']>.005 and i%5==0)) for i,c in enumerate(cases)]
        B=[[row(c,True) for c in cases] for _ in range(5)]
        result=compare(A,B)
        self.assertTrue(result['pass_endpoint']);self.assertEqual(result['df'],4)
        self.assertAlmostEqual(result['mean_difficult_gain'],.2)
        for r in B[4][:11]:r['strict']=False
        result=compare(A,B)
        self.assertFalse(result['engineering_per_seed'][4]);self.assertFalse(result['pass_endpoint'])
        with self.assertRaises(ValueError):compare(A,B[:4])

    def test_policy_numerical_failure_invalidates_comparison(self):
        def row(case):
            return dict(case=case,strict=True,survived=True,caps_respected=True,
                        numerical_failure=False,E=0.,E_observed=0.)
        baseline=[row(c) for c in panel()]
        policies=[[row(c) for c in panel()] for _ in range(5)]
        policies[2][17]['numerical_failure']=True
        result=compare(baseline,policies)
        self.assertFalse(result['valid'])
        self.assertFalse(result['pass_endpoint'])
