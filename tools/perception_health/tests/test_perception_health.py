import json, os, pathlib, pty, subprocess, sys, tempfile, threading, time, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "py"))
from perception_health import *
from supervisor_model import Event, SupervisorModel

class ProtocolTests(unittest.TestCase):
    def test_crc_vector_and_frozen_vector_python(self):
        self.assertEqual(crc16_ccitt_false(b"123456789"), 0x29B1)
        line = next(x for x in (ROOT / "tests/vectors.txt").read_text().splitlines() if x.startswith("PH_HEALTH"))
        expected = bytes.fromhex(line.split()[1])
        value = PerceptionHealth(0x0102030405060708,0x11223344,3,0x5566,1,0x7788,3)
        self.assertEqual(encode_health(0x1234,value), expected)
        self.assertEqual(decode_health_payload(expected[7:-2]),value)

    def test_upstream_frozen_frames_byte_at_a_time(self):
        lines=[x.split()[1] for x in (ROOT/"tests/vectors.txt").read_text().splitlines() if x.startswith("UPSTREAM")]
        parser=StreamParser(); got=[]
        for frame in map(bytes.fromhex,lines):
            for byte in frame: got.extend(parser.feed(bytes([byte])))
        self.assertEqual([x[0:2] for x in got],[(2,13355),(2,13356)])

    def test_crc_and_len_errors_resync(self):
        valid=encode_health(1,PerceptionHealth(1,1,3,0,1,10,3))
        bad=bytearray(valid); bad[-1]^=1
        parser=StreamParser(); frames=parser.feed(bytes(bad)+b"\xa5\x5a\x03\x05\x00\x00\x41"+valid)
        self.assertEqual(parser.crc_errors,1); self.assertEqual(parser.len_errors,1)
        self.assertEqual(len(frames),1)

    def test_saturation_and_invalid_clock(self):
        self.assertEqual(saturating_age_us(9_000_000_000_000_000,0),U32_MAX)
        with self.assertRaises(ValueError): saturating_age_us(1,2)

class ModelTests(unittest.TestCase):
    def setUp(self): self.m=SupervisorModel()
    def start(self, age=1000, state=3, flags=3):
        self.m.update(1000,Event("heartbeat",1000,session_id=9))
        self.m.update(1100,Event("health",1100,age,state,flags))
    def test_fresh_then_hold_age(self):
        self.start(); self.assertEqual(self.m.state,"FRESH")
        self.m.update(1100+self.m.c["pose_age_hold_us"],Event("health",1100+self.m.c["pose_age_hold_us"],age_at_send_us=100000,tracking_state=3,flags=3))
        self.assertEqual((self.m.state,self.m.reason),("HOLD","SOURCE_AGE_HOLD"))
    def test_lost_latches_until_rearm(self):
        self.start(); self.m.update(1200,Event("health",1200,tracking_state=5,flags=3))
        self.assertEqual(self.m.state,"FAILSAFE"); self.assertTrue(self.m.rearm(1300)); self.assertEqual(self.m.state,"INIT")
    def test_missing_mapping_holds_then_silence_fails(self):
        self.start(flags=0); self.assertEqual(self.m.state,"HOLD")
        self.m.update(1100+self.m.c["pose_age_timeout_us"])
        self.assertEqual(self.m.state,"FAILSAFE")

    def test_source_age_timeout_uses_upstream_reason(self):
        self.start(age=self.m.c["pose_age_timeout_us"])
        self.assertEqual((self.m.state,self.m.reason),("FAILSAFE","SOURCE_AGE_TIMEOUT"))

    def test_receipt_silence_hold_before_timeout(self):
        self.start()
        self.m.update(1100+self.m.c["receipt_silence_hold_us"])
        self.assertEqual((self.m.state,self.m.reason),("HOLD","RESULT_SILENCE"))
    def test_heartbeat_silence_failsafe(self):
        self.start(); self.m.update(1100+self.m.c["heartbeat_timeout_us"])
        self.assertEqual((self.m.state,self.m.reason),("FAILSAFE","HEARTBEAT_TIMEOUT"))

    def test_mcu_clock_regression_latches(self):
        self.start(); self.m.update(1099)
        self.assertEqual((self.m.state,self.m.reason),("FAILSAFE","CLOCK_REGRESSION"))
    def test_degraded_tracking_holds_and_reset_counter_survives_wire(self):
        self.start(state=4); self.assertEqual(self.m.state,"HOLD")
        self.m.update(1200); self.assertEqual(self.m.state,"HOLD")

    def test_map_reset_counter_change_downgrades(self):
        self.m.update(1000,Event("heartbeat",1000,session_id=9))
        self.m.update(1100,Event("health",1100,age_at_send_us=1000,tracking_state=3,flags=3,map_reset_counter=4))
        self.assertEqual(self.m.state,"FRESH")
        self.m.update(1200,Event("health",1200,age_at_send_us=1000,tracking_state=3,flags=3,map_reset_counter=5))
        self.assertEqual((self.m.state,self.m.reason),("HOLD","MAP_RESET"))

class PtyTests(unittest.TestCase):
    def test_sender_pty_round_trip_and_silence(self):
        master, slave=pty.openpty(); path=os.ttyname(slave)
        now=time.clock_gettime_ns(getattr(time,"CLOCK_MONOTONIC_RAW",time.CLOCK_MONOTONIC))
        source_ns=1_000_000_000
        exchanges=[]
        for i in range(3):
            a=source_ns+i*1_000_000_000; b=now-1_000_000+i*1_000_000_000
            exchanges.append([a,b+1000,b+2000,a+10000])
        mapping={"valid":True,"camera_domain":"D435i_global_time","pi_domain":"host_steady",
                 "camera_session":"camera-session","pi_session":"pi-session","exchanges_ns":exchanges}
        events=[{"pose_source_d435i_ns":source_ns,"mapping":mapping,
               "tracking_state":"OK","map_reset_counter":n,"imu_initialized":True,"tracked_features":77} for n in (11,12)]
        proc=subprocess.Popen([sys.executable,str(ROOT/"py/sender.py"),"--device",path,
                               "--session-id","9","--heartbeat-ms","20"],stdin=subprocess.PIPE,
                              stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        proc.stdin.write((json.dumps(events[0])+"\n").encode()); proc.stdin.flush()
        parser=StreamParser(); got=[]; deadline=time.time()+2; stop=threading.Event()
        def receive_loop():
            while not stop.is_set():
                try: chunk=os.read(master,1024)
                except BlockingIOError: time.sleep(.005); continue
                if chunk: got.extend(parser.feed(chunk))
        os.set_blocking(master,False)
        receiver=threading.Thread(target=receive_loop,daemon=True); receiver.start()
        try:
            while time.time()<deadline and not any(t==TYPE_PERCEPTION_HEALTH for t,_,_ in got):
                time.sleep(.005)
            self.assertIsNone(proc.poll())
            proc.kill(); proc.wait(timeout=2)
        finally:
            if proc.poll() is None: proc.kill(); proc.wait()
            proc.stdin.close()
            stop.set(); receiver.join(timeout=2); os.close(master); os.close(slave)
        self.assertTrue(any(t==TYPE_HEARTBEAT for t,_,_ in got))
        health=next(decode_health_payload(p) for t,_,p in got if t==TYPE_PERCEPTION_HEALTH)
        self.assertEqual(health.map_reset_counter,11); self.assertEqual(health.tracked_features,77)
        cfg=json.loads((ROOT/"config.json").read_text()); cfg["pose_age_hold_us"]=5_000_000; cfg["pose_age_timeout_us"]=60_000_000
        model=SupervisorModel(cfg); now=1000
        model.update(now,Event("heartbeat",now,session_id=9))
        model.update(now+1,Event("health",now+1,health.pose_age_us,health.tracking_state,health.flags,
                                 map_reset_counter=health.map_reset_counter,imu_initialized=bool(health.imu_initialized)))
        self.assertEqual(model.state,"FRESH", (model.reason,health))
        model.update(now+1+model.c["receipt_silence_timeout_us"])
        self.assertEqual(model.state,"FAILSAFE")

    def test_corruption_is_counted_and_parser_recovers(self):
        p=StreamParser(); frame=encode_health(2,PerceptionHealth(1,1,3,0,1,5,3)); bad=bytearray(frame);bad[9]^=1
        self.assertEqual(p.feed(bytes(bad)+frame)[0][1],2); self.assertEqual(p.crc_errors,1)

class CTests(unittest.TestCase):
    def test_c99_encoder_decoder_matches_frozen_vector(self):
        src=ROOT/"tests/c_test.c"; exe=ROOT/"tests/c_test"
        subprocess.run(["cc","-std=c99","-Wall","-Wextra","-Werror",str(ROOT/"c/perception_health.c"),str(src),"-o",str(exe)],check=True)
        try: subprocess.run([str(exe)],check=True)
        finally: exe.unlink(missing_ok=True)

if __name__=="__main__": unittest.main()
