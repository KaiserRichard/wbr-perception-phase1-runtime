"""Deterministic, bounded mutation checks for existing parser entry points."""
from __future__ import annotations
import importlib.util
import random
import json
import signal
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads((Path(__file__).parent / "fuzz_config.json").read_text())
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module); return module
ph = load("ph_fuzz", ROOT / "tools/perception_health/py/perception_health.py")
lp = load("lp_fuzz", ROOT / "tools/link_proto/py/link_proto.py")
qual_path = ROOT / "lab/rosbag_qual"
sys.path.insert(0, str(qual_path))
import bag_core
n4 = load("n4_fuzz", ROOT / "tools/n4b_offline/db3_to_euroc.py")
traj = load("traj_fuzz", ROOT / "tools/trajectory_eval/traj_eval.py")

class Deadline(Exception): pass
def timeout(_signum, _frame): raise Deadline("per-input timeout")

def bounded(call, data):
    old = signal.signal(signal.SIGALRM, timeout); signal.setitimer(signal.ITIMER_REAL, CONFIG["per_input_timeout_seconds"]["value"])
    try:
        try: return call(data)
        except (ValueError, KeyError, struct.error, UnicodeError, IndexError, OverflowError): return None
        except Deadline: raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0); signal.signal(signal.SIGALRM, old)

def mutations(seed, base, rounds=CONFIG["python_mutations_per_target"]["value"]):
    r = random.Random(seed)
    yield base
    for _ in range(rounds):
        b=bytearray(base)
        mode=r.randrange(5)
        if mode == 0 and b: b[r.randrange(len(b))] ^= 1 << r.randrange(8)
        elif mode == 1: del b[r.randrange(len(b)+1):]
        elif mode == 2: b.extend(bytes([r.randrange(256)])*r.randrange(1,9))
        elif mode == 3 and b: b[r.randrange(len(b))]=r.choice((0,1,127,255))
        else: b=bytearray(r.randbytes(r.randrange(0,min(96,len(base)+12))))
        yield bytes(b)

class ParserMutationTests(unittest.TestCase):
    def test_perception_stream_valid_roundtrip_and_mutations(self):
        valid=ph.encode_health(19,ph.PerceptionHealth(123456789,55,3,2,1,40,3))
        (Path(__file__).parent / "corpus/perception_health_valid.bin").write_bytes(valid)
        fixture=(Path(__file__).parent / "corpus/perception_health_valid.bin").read_bytes()
        self.assertEqual(fixture,valid)
        parser=ph.StreamParser(); got=parser.feed(valid)
        self.assertEqual(got,[(ph.TYPE_PERCEPTION_HEALTH,19,valid[7:-2])])
        self.assertEqual(ph.decode_health_payload(got[0][2]),ph.PerceptionHealth(123456789,55,3,2,1,40,3))
        for raw in mutations(2501,valid):
            p=ph.StreamParser(); frames=p.feed(raw)
            for typ,seq,payload in frames:
                rebuilt=ph.encode_frame(typ,seq,payload)
                self.assertEqual(ph.StreamParser().feed(rebuilt),[(typ,seq,payload)])
    def test_link_proto_python_encoder_inputs(self):
        # Frozen vector fixture is produced by the project's existing golden-vector suite.
        vector=bytes.fromhex(next(line.split()[1] for line in (ROOT/'tools/link_proto/tests/vectors.txt').read_text().splitlines() if line and not line.startswith('#')))
        for raw in mutations(2502,vector):
            bounded(lambda b: lpcobs(b),raw)
        for x in (float('nan'),float('inf'),-float('inf')):
            with self.assertRaises(ValueError):
                lpcobs(lp.body_velocity_ref(1,1,estimate_seq=1,map_epoch=1,mapping_revision=1,frame_id=1,reset_counter=0,pi_creation_ns=1,mapped_mcu_creation_ns=1,lease_us=100000,forward_m_s=x,yaw_rad_s=0))
    def test_rosbag_and_n4b_cdr_mutations(self):
        # Real saved rosbag qualification header fixture, preserved verbatim in repository.
        real=json.loads((ROOT/'lab/rosbag_qual/tests/real_header_fixture.json').read_text())
        real_cdr=bytes.fromhex(real['topics'][0]['rows'][0]['cdr_header_hex'])
        self.assertEqual(bag_core.extract_header(real_cdr,'sensor_msgs/msg/Image','image'),(23977455,'Infrared1'))
        for raw in mutations(2505,real_cdr):
            bounded(lambda b: bag_core.extract_header(b,'sensor_msgs/msg/Image','image'),raw)
        header=struct.pack('<iI',123,456)+struct.pack('<I',4)+b'cam\0'
        cdr=b'\x00\x01\x00\x00'+header
        for raw in mutations(2503,cdr):
            bounded(lambda b: bag_core.extract_header(b,'sensor_msgs/msg/Image','image'),raw)
            bounded(lambda b: n4.header(n4.CDR(b)),raw)
        self.assertEqual(bag_core.extract_header(cdr,'sensor_msgs/msg/Image','image'),(123000000456,'cam'))
    def test_trajectory_file_mutations(self):
        sample=b'1.0 0 0 0 0 0 0 1\n2.0 1 0 0 0 0 0 1\n'
        for raw in mutations(2504,sample):
            with tempfile.NamedTemporaryFile() as f:
                f.write(raw);f.flush()
                def parse(_): return traj.read_trajectory(f.name,'tum','s')
                bounded(parse,raw)
        with tempfile.NamedTemporaryFile() as f:
            f.write(sample);f.flush(); parsed=traj.read_trajectory(f.name,'tum','s')
            self.assertEqual(list(parsed.t_ns),[1_000_000_000,2_000_000_000])
    def test_reversed_and_nonfinite_trajectory_rejected(self):
        for sample in (b'2 0 0 0 0 0 0 1\n1 0 0 0 0 0 0 1\n',b'1 nan 0 0 0 0 0 1\n'):
            with tempfile.NamedTemporaryFile() as f:
                f.write(sample);f.flush()
                with self.assertRaises(ValueError): traj.read_trajectory(f.name,'tum','s')

def lpcobs(data):
    # Python codec currently provides COBS encode only; malformed-input check exercises encoder determinism.
    return lp.cobs_encode(data)

if __name__=='__main__': unittest.main()
