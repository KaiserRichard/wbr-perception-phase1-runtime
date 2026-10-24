#!/usr/bin/env python3
"""Bench-only TerrainAdvisory sender and Pi-monotonic timing recorder."""
import argparse
import csv
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import sys
import time
from collections import Counter

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.link_proto.py import link_proto as lp
from tools.obstacle_decision import advisory_codec

spec = importlib.util.spec_from_file_location('link_bench', Path(__file__).with_name('link_bench.py'))
lb = importlib.util.module_from_spec(spec); spec.loader.exec_module(lb)
SESSION = lb.BENCH_SESSION
REASONS = ['NONE','WIRE','SESSION','SEQUENCE','FIELDS','AGE','RESET','DISABLED','ASSOCIATION','SILENCE','LEASE']


def stats_ns(values):
    vals = sorted(x / 1000.0 for x in values if x is not None)
    if not vals: return {'n': 0, 'p50': None, 'p95': None, 'p99': None, 'max': None}
    return {'n': len(vals), 'p50': lb.percentile(vals, 50), 'p95': lb.percentile(vals, 95),
            'p99': lb.percentile(vals, 99), 'max': vals[-1]}


class Runner:
    def __init__(self, link):
        self.link = link; self.seq = (time.monotonic_ns() // 1_000_000) & 0xffffffff
        # The port is opened before we transmit, so the next delimiter will
        # terminate a complete reply rather than an unknown partial record.
        self.link.dropping = False; self.link.synced = True
        self.pending = {}; self.rows = []; self.result_codes = Counter(); self.stale_events = 0
        self.last_stale = 0; self.echo_rejected = 0; self.accepted_count = 0; self.rejected_count = 0

    def poll(self, wait=0):
        for t, rec in self.link.poll(wait):
            if rec.get('type') != lp.ADVISORY_ECHO: continue
            if rec.get('stale') and not self.last_stale: self.stale_events += 1
            self.last_stale = rec.get('stale', 0)
            result = rec.get('result', 0); self.result_codes[REASONS[result] if result < len(REASONS) else str(result)] += 1
            if result: self.echo_rejected += 1
            self.accepted_count=max(self.accepted_count,rec.get('accepted_count',0))
            self.rejected_count=max(self.rejected_count,rec.get('rejected_count',0))
            row = self.pending.pop(rec.get('advisory_seq'), None)
            if row is not None:
                row['echo_ns'] = t; row['rtt_ns'] = t - row['before_write_ns']
                row['echo_result'] = result; row['accepted_count'] = rec['accepted_count']
                row['rejected_count'] = rec['rejected_count']; row['stale'] = rec['stale']

    def send(self, values, detector_before, detector_after, frame_stamp_ns=0, fault=None):
        self.seq = (self.seq + 1) & 0xffffffff
        seq = self.seq
        wire_seq=seq
        vals = dict(pi_monotonic_ns=detector_after, frame_stamp_ns=frame_stamp_ns,
                    advisory=values['advisory'], confidence=values['confidence'],
                    distance_m=values['distance_m'], height_m=values['height_m'],
                    width_m=values['width_m'], plane_valid=values['plane_valid'],
                    plane_pitch_rad=values['plane_pitch_rad'], plane_height_m=values['plane_height_m'])
        wire = advisory_codec.encode(SESSION, seq, **vals)
        if fault == 'crc':
            b=bytearray(wire); b[-3] ^= 0x40; wire=bytes(b)
        elif fault == 'session': wire=advisory_codec.encode(SESSION ^ 1, seq, **vals)
        elif fault == 'old':
            wire_seq=(seq-2)&0xffffffff
            wire=advisory_codec.encode(SESSION, wire_seq, **vals)
        elif fault == 'nonfinite':
            payload=struct.pack('<QQBBffffff', vals['pi_monotonic_ns'], frame_stamp_ns,
                vals['advisory'], vals['plane_valid'], float('nan'), vals['distance_m'],
                vals['height_m'], vals['width_m'], vals['plane_pitch_rad'], vals['plane_height_m'])
            raw=struct.pack('<BBHQI', lp.VERSION, lp.TERRAIN_ADVISORY, 42, SESSION, wire_seq)+payload
            raw += struct.pack('<I', lp.crc32c(raw)); wire=lp.cobs_encode(raw)+b'\0'
        row={'seq':wire_seq, 'frame_stamp_ns':frame_stamp_ns, 'detector_before_ns':detector_before,
             'detector_after_ns':detector_after, 'detector_ns':detector_after-detector_before,
             'before_write_ns':None, 'echo_ns':None, 'rtt_ns':None, 'echo_result':None,
             'accepted_count':None, 'rejected_count':None, 'stale':None, 'fault':fault or ''}
        self.pending[wire_seq]=row
        row['before_write_ns']=self.link.send(wire,mark=True); self.poll(0)
        self.rows.append(row)
        return seq

    def drain(self, seconds=0.1):
        end=time.monotonic()+seconds
        while time.monotonic()<end: self.poll(min(.02,end-time.monotonic()))


def bag_frames(path, stride):
    """Yield depth frames and their camera stamp with the detector result."""
    import numpy as np
    from rosbags.highlevel import AnyReader
    from rosbags.rosbag2 import Reader as Rosbag2Reader
    from rosbags.typesys import Stores, get_typestore
    from tools.obstacle_decision.replay_bag import _reader_paths, _resolve_topics, _intrinsics, decode_depth
    from tools.obstacle_decision.detect import Params, process_frame
    from tools.obstacle_decision.decide import DecisionParams, update
    p=Path(path); typestore=get_typestore(Stores.ROS2_JAZZY); reader=Rosbag2Reader(p) if p.is_dir() else AnyReader(_reader_paths(p), default_typestore=typestore)
    reader.open()
    try:
        dt,it=_resolve_topics(reader,p); conns=[c for c in reader.connections if c.topic in (dt,it)]
        K=None; pending=[]; count=0
        for conn, stamp, raw in reader.messages(connections=conns):
            msg=typestore.deserialize_cdr(raw,conn.msgtype)
            if conn.topic==it:
                K=_intrinsics(msg)
                frames=pending; pending=[]
                for image,bag_stamp in frames: yield image,K,int(bag_stamp)
            else:
                count+=1
                if (count-1)%stride: continue
                if K is None: pending.append((msg,stamp)); continue
                yield msg,K, int(stamp)
    finally: reader.close()


def run(args):
    link=lb.Link(args.port,args.baud); runner=Runner(link); link.marker=lb.GpioMarker(args.marker_gpio) if args.marker_gpio is not None else None
    detector_times=[]; previous_stamp=None; due=time.monotonic_ns(); frames=0
    try:
        if args.synthetic:
            rate,duration=args.synthetic; end=time.monotonic()+duration; period=1/rate
            while time.monotonic()<end:
                before=time.monotonic_ns(); after=time.monotonic_ns()
                values=dict(advisory=1,confidence=.8,distance_m=1.0,height_m=.06,width_m=.25,
                    plane_valid=1,plane_pitch_rad=0.,plane_height_m=.4)
                runner.send(values,before,after)
                due += int(period*1e9); time.sleep(max(0,(due-time.monotonic_ns())/1e9)); runner.poll(0)
                frames+=1
        else:
            from tools.obstacle_decision.replay_bag import _stamp_ns
            from tools.obstacle_decision.detect import Params, process_frame
            from tools.obstacle_decision.decide import DecisionParams, update
            ps={}; ds={}; params=Params(); dp=DecisionParams()
            for msg,K,stamp in bag_frames(args.bag,args.stride):
                frame_stamp=_stamp_ns(msg); before=time.monotonic_ns()
                frame,ps=process_frame(__import__('tools.obstacle_decision.replay_bag',fromlist=['decode_depth']).decode_depth(msg),K,params,ps)
                decision,ds=update(frame,ds,dp); after=time.monotonic_ns(); detector_times.append(after-before)
                nearest=frame.nearest
                values=dict(advisory=int(decision.advisory),confidence=float(decision.confidence),
                    distance_m=nearest.distance_m if nearest else 0.,height_m=nearest.height_m if nearest else 0.,
                    width_m=nearest.width_m if nearest else 0.,plane_valid=int(frame.plane_valid),
                    plane_pitch_rad=frame.plane_pitch_rad if math.isfinite(frame.plane_pitch_rad) else 0.,
                    plane_height_m=frame.plane_height_m if math.isfinite(frame.plane_height_m) else 0.)
                runner.send(values,before,after,frame_stamp); frames+=1
                if previous_stamp is not None and stamp>previous_stamp:
                    due += int((stamp-previous_stamp)/args.rate); time.sleep(max(0,(due-time.monotonic_ns())/1e9))
                previous_stamp=stamp; runner.poll(0)
        if args.faults:
            default=dict(advisory=0,confidence=.5,distance_m=0.,height_m=0.,width_m=0.,plane_valid=0,plane_pitch_rad=0.,plane_height_m=0.)
            for fault in ('crc','old','session','nonfinite'):
                runner.send(default,time.monotonic_ns(),time.monotonic_ns(),fault=fault); runner.drain(.08)
            time.sleep(.4); runner.drain(.15)
            runner.send(default,time.monotonic_ns(),time.monotonic_ns(),fault='recovery'); runner.drain(.2)
        else: runner.drain(.15)
    finally:
        if link.marker: os.close(link.marker.fd)
        os.close(link.fd)
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    fields=list(runner.rows[0]) if runner.rows else ['seq','frame_stamp_ns','detector_before_ns','detector_after_ns','detector_ns','before_write_ns','echo_ns','rtt_ns','echo_result','accepted_count','rejected_count','stale','fault']
    with (out/'packets.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(runner.rows)
    detector=detector_times or [r['detector_ns'] for r in runner.rows if not r['fault']]
    sent=sum(1 for r in runner.rows if not r['fault']); echoed=sum(1 for r in runner.rows if r['echo_ns'] is not None and not r['fault'])
    summary={'mode':'synthetic' if args.synthetic else 'bag','frames':frames,'sent':sent,'echoed':echoed,
        'loss':sent-echoed,'detector_time_us':stats_ns(detector),'send_echo_rtt_us':stats_ns([r['rtt_ns'] for r in runner.rows if r['rtt_ns'] is not None and not r['fault']]),
        'rejected_echoes':runner.echo_rejected,'mcu_accepted_count':runner.accepted_count,
        'mcu_rejected_count':runner.rejected_count,'echo_result_codes':dict(runner.result_codes),
        'stale_events':runner.stale_events,'clock':'all processing/RTT timestamps are Pi CLOCK_MONOTONIC; frame_stamp_ns is stored only',
        'unmatched_echoes':len(runner.pending)}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps(summary,indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--port',default='/dev/ttyAMA0'); p.add_argument('--baud',type=int,default=460800); p.add_argument('--out',required=True); p.add_argument('--marker-gpio',type=int); p.add_argument('--faults',action='store_true')
    mode=p.add_mutually_exclusive_group(required=True); mode.add_argument('--synthetic',nargs=2,type=float,metavar=('RATE_HZ','DURATION_S')); mode.add_argument('--bag')
    p.add_argument('--rate',type=float,default=1.0); p.add_argument('--stride',type=int,default=1); args=p.parse_args()
    if args.stride<1 or args.rate<=0 or (args.synthetic and (args.synthetic[0]<=0 or args.synthetic[1]<=0)): p.error('rate, duration, and stride must be positive')
    run(args)

if __name__=='__main__': main()
