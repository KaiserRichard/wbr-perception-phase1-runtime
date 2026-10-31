import copy
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from sim.augmented import AugmentedRuntime, RuntimeConfig
from sim.rl.g1.environment import G1Env
from sim.rl.g1.control import Predictor
from sim.rl.g1.metrics import compare, recovery, strata
from sim.rl.g1.protocol import HERE, model_config, panel, reference


class EnvironmentTests(unittest.TestCase):
    def test_step_shapes_and_seed(self):
        a,b=G1Env(),G1Env()
        oa,ia=a.reset(seed=123);ob,ib=b.reset(seed=123)
        self.assertEqual(ia,ib);np.testing.assert_array_equal(oa,ob)
        for action in ([.3],[-.7],[1.]):
            ra,rb=a.step(action),b.step(action)
            self.assertEqual(ra[0].shape,(25,));self.assertEqual(ra[0].dtype,np.float32)
            self.assertIsInstance(ra[1],float)
            for x,y in zip(ra[:4],rb[:4]):np.testing.assert_array_equal(x,y)
        a.reset(seed=123);self.assertEqual(a.case,ia['case'])

    def test_zero_action_identity(self):
        case=panel(True)[4]
        a,b=G1Env(baseline=True),G1Env()
        a.reset(options=case);b.reset(options=case)
        for _ in range(20):
            ra,rb=a.step([0]),b.step([0])
            for x,y in zip(ra[:4],rb[:4]):np.testing.assert_array_equal(x,y)
            np.testing.assert_array_equal(a.runtime.truth(),b.runtime.truth())

    def test_bounds_ramp_and_reversal(self):
        for command in (-.2,.2):
            case=panel(True)[0].copy();case.update(command=command,pitch_deg=0.,push_N=0.)
            env=G1Env();env.reset(options=case)
            for i in range(120):
                env.step([10 if command>0 else -10])
            for i in range(50):env.step([-10 if command>0 else 10])
            actions=np.array(env.actions)
            self.assertLessEqual(np.max(abs(actions[:,1])),.03+1e-12)
            self.assertLessEqual(np.max(abs(actions[:,2])),.2+1e-12)
            self.assertLessEqual(np.max(abs(np.diff(np.r_[0.,actions[:,1]]))),.001+1e-12)
            env.step([np.nan]);self.assertEqual(env.rejects,1)
            with self.assertRaises(ValueError):env.step([0.,0.])

    def test_original_position_reference(self):
        np.testing.assert_allclose(reference(.5,.2),[.025,.1,0,0,0,0])
        np.testing.assert_allclose(reference(10,.2),[1.9,.2,0,0,0,0])

    def test_model_independent(self):
        nominal,variant=model_config(),model_config(1)
        self.assertEqual(nominal['physics']['body_mass']['value'],3.5)
        self.assertEqual(variant['physics']['wheel_mass']['value'],.7)
        self.assertAlmostEqual(variant['physics']['body_com']['value'],.066)
        self.assertAlmostEqual(variant['physics']['wheel_inertia']['value'],.00132)
        old=json.loads((HERE.parents[1]/'configs/assumed_planar.json').read_text())
        self.assertEqual(old['physics']['body_mass']['value'],2.)

    def test_frozen_panels(self):
        final,dev=panel(),panel(True)
        saved=json.loads((HERE/'cases.json').read_text())
        self.assertEqual(saved,dict(development=dev,final=final))
        self.assertEqual(len(final),200);self.assertEqual(len(dev),20)
        self.assertEqual([c['noise_seed'] for c in final],list(range(3000,3200)))
        self.assertEqual([sum(abs(c['delay_s']-d)<1e-12 for c in final) for d in [.002,.005,.006,.008,.01]],[40]*5)
        self.assertEqual(final[0],dict(delay_s=.002,command=0.,pitch_deg=-5.,push_N=-6.,variant=0,noise_seed=3000))


class DelayTests(unittest.TestCase):
    def test_fractional_actual_arrival(self):
        for delay in (.002,.005,.006,.008,.01,.00337):
            rt=AugmentedRuntime(model_config(),RuntimeConfig(delay_s=delay))
            rt.reset(np.zeros(6),seed=0)
            pieces=[]
            for tick in range(7):pieces.extend(rt.step([1.,0.]).intervals)
            first=next(i for i in pieces if i.source_submitted_s==0.)
            self.assertAlmostEqual(first.time_s,delay,places=11)
            self.assertTrue(all(np.all(i.delayed_command==0) for i in pieces if i.time_s<delay-1e-12))
            self.assertAlmostEqual(sum(i.dt_s for i in pieces),.014,places=12)

    def test_predictor_event_partition(self):
        rt=AugmentedRuntime(model_config(),RuntimeConfig(delay_s=.005))
        rt.reset(np.zeros(6))
        rt.step([.1,.2]);rt.step([.3,.4]);rt.step([.5,.6])
        p=Predictor(.005)
        z=np.r_[rt.measurement(),rt.observation().torque_estimate]
        # At6ms, first command held; arrivals7ms and9ms occur within horizon11ms.
        expected=p.advance(z,np.array([.1,.2]),.001)
        expected=p.advance(expected,np.array([.3,.4]),.002)
        expected=p.advance(expected,np.array([.5,.6]),.002)
        np.testing.assert_allclose(p.predict(rt),expected,atol=1e-12)

    def test_recovery_completion_deadline(self):
        t=np.arange(5001)*.002
        within=np.ones(5001,dtype=bool)
        self.assertEqual(recovery(t,within,0.),1.)
        within[:2251]=False
        self.assertGreater(recovery(t,within,0.),5.)


class ResumeTests(unittest.TestCase):
    def test_resume_and_corrupt_checkpoint_fallback(self):
        from sim.rl.g1.training import train,newest
        from sim.rl.g1.evaluation import load_policy
        import pickle
        cfg=json.loads((HERE/'config.json').read_text())
        cfg.update(n_envs=1,n_steps=8,batch_size=8,n_epochs=1,transitions=32)
        with tempfile.TemporaryDirectory() as tmp:
            run=Path(tmp)
            first=train(run,17,seconds=.01,config=cfg,subprocess=False)
            self.assertEqual(first['completed_steps'],8)
            old=newest(run)
            model,norm,state=load_policy(run)
            obs=np.ones((1,25),dtype=np.float32)
            action=model.predict(norm.normalize_obs(obs),deterministic=True)[0]
            norm.close()
            second=train(run,17,seconds=120,resume=True,config=cfg,subprocess=False)
            self.assertEqual(second['completed_steps'],32)
            self.assertEqual(second['segment_steps'],24)
            current=newest(run)
            with (current/'state.pkl').open('rb') as f:s=pickle.load(f)
            self.assertGreater(s['updates'],state['updates'])
            (current/'policy.zip').write_bytes(b'corrupt')
            self.assertEqual(newest(run),old)
            model2,norm2,_=load_policy(run)
            np.testing.assert_array_equal(action,model2.predict(norm2.normalize_obs(obs),deterministic=True)[0])
            norm2.close()
            with self.assertRaises(ValueError):train(run,18,seconds=120,resume=True,config=cfg,subprocess=False)

if __name__=='__main__':unittest.main()
