import unittest, numpy as np
from tools.ground_plane.synth import render,Box
from tools.obstacle_decision.detect import process_frame,Params
from tools.obstacle_decision.decide import update,DecisionParams,Advisory
from tools.obstacle_decision.advisory_codec import encode,decode

K=np.array([[386.953,0,321.034],[0,386.953,241.040],[0,0,1.]])
def sequence(h=None,d=1.,pitch=0.,x=0.):
    boxes=() if h is None else (Box((x,d+.06,h/2),(.30,.12,h)),)
    dep,_,_=render(height=.30,pitch=pitch,boxes=boxes,sigma_d=.1)
    ps=Params(); st={}; ds={}; result=None
    for _ in range(5):
        fr,st=process_frame(dep,K,ps,st); result,ds=update(fr,ds,DecisionParams())
    return fr,result

class TestObstacleDecision(unittest.TestCase):
    def test_box_and_pitch(self):
        for pitch in (0.,3.):
            fr,dec=sequence(.05,pitch=pitch)
            self.assertIsNotNone(fr.nearest)
            self.assertAlmostEqual(fr.nearest.height_m,.05,delta=.01)
            self.assertAlmostEqual(fr.nearest.distance_m,1.,delta=.05)
            self.assertEqual(dec.advisory,Advisory.JUMP_CANDIDATE)
    def test_tall_box(self): self.assertEqual(sequence(.20)[1].advisory,Advisory.STOP_CANDIDATE)
    def test_empty_and_outside(self):
        self.assertEqual(sequence()[1].advisory,Advisory.NONE)
        self.assertEqual(sequence(.05,x=.7)[1].advisory,Advisory.NONE)
    def test_blip_not_confirmed(self):
        from types import SimpleNamespace
        state={}; params=DecisionParams(); out=None
        for exists in (True,False,False):
            f=SimpleNamespace(nearest=SimpleNamespace(distance_m=1.,height_m=.05,width_m=.3) if exists else None,plane_valid=True)
            out,state=update(f,state,params)
        self.assertNotEqual(out.advisory,Advisory.JUMP_CANDIDATE)
    def test_codec_round_trip(self):
        wire=encode(123,7,pi_monotonic_ns=1000,frame_stamp_ns=900,advisory=1,confidence=.8,
            distance_m=1.2,height_m=.05,width_m=.3,plane_valid=True,plane_pitch_rad=.02,plane_height_m=.30)
        got=decode(wire)
        self.assertEqual((got['session'],got['sequence'],got['advisory']),(123,7,1))
        self.assertAlmostEqual(got['height_m'],.05,places=6)
        self.assertAlmostEqual(got['plane_height_m'],.30,places=6)

if __name__=='__main__': unittest.main()
