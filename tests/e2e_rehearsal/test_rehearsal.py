#!/usr/bin/env python3
"""Synthetic end-to-end rehearsal of existing WBR tool interfaces."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import pty
import select
import shutil
import sqlite3
import struct
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/perception_health/py"))
sys.path.insert(0, str(ROOT / "tools/perception_health/integration"))
from tools.perception_health.integration.vio_to_pose_events import Converter, load_mapping
from tools.perception_health.py.perception_health import (
    HEARTBEAT, TYPE_HEARTBEAT, TYPE_PERCEPTION_HEALTH, StreamParser,
    decode_health_payload,
)
from tools.perception_health.py.supervisor_model import Event, SupervisorModel


CFG = json.loads((HERE / "config.json").read_text())
def val(name):
    return CFG[name]["value"]

TOPICS = {
    "ir1": ("/device_0/sensor_0/Infrared_1/image/data", "sensor_msgs/msg/Image"),
    "ir2": ("/device_0/sensor_0/Infrared_2/image/data", "sensor_msgs/msg/Image"),
    "gyro": ("/device_0/sensor_2/Gyro_0/imu/data", "sensor_msgs/msg/Imu"),
    "accel": ("/device_0/sensor_2/Accel_0/imu/data", "sensor_msgs/msg/Imu"),
}


class CDRWriter:
    """Small CDR little-endian serializer for the two ROS message shapes."""
    def __init__(self):
        self.data = bytearray(b"\x00\x01\x00\x00")

    def put(self, fmt, *values):
        size = struct.calcsize("<" + fmt)
        alignment = min(struct.calcsize("<" + fmt[0]), 8)
        self.data.extend(b"\0" * ((-len(self.data)) % alignment))
        self.data.extend(struct.pack("<" + fmt, *values))

    def string(self, text):
        raw = text.encode() + b"\0"
        self.put("I", len(raw)); self.data.extend(raw)

    def header(self, stamp_ns, frame):
        self.put("iI", stamp_ns // 1_000_000_000, stamp_ns % 1_000_000_000)
        self.string(frame)

    def image(self, stamp_ns, side):
        self.header(stamp_ns, side)
        width, height = val("image_width_px"), val("image_height_px")
        self.put("II", height, width); self.string("mono8"); self.put("B", 0)
        self.put("I", width)
        # A tiny repeated checker texture remains a standards-shaped 640x480 payload.
        pixels = bytes(((x // 16 + y // 16 + (side == "right")) & 1) * 180 + 30
                       for y in range(height) for x in range(width))
        self.put("I", len(pixels)); self.data.extend(pixels)
        return bytes(self.data)

    def imu(self, stamp_ns, gyro):
        self.header(stamp_ns, "camera_imu")
        self.put("dddd", 0.0, 0.0, 0.0, 1.0); self.put("d" * 9, *([0.0] * 9))
        self.put("ddd", 0.01, 0.02, 0.03) if gyro else self.put("ddd", 0.0, 0.0, 9.81)
        self.put("d" * 9, *([0.0] * 9))
        self.put("ddd", 0.0, 0.0, 0.0); self.put("d" * 9, *([0.0] * 9))
        return bytes(self.data)


def cdr_image(stamp, side): return CDRWriter().image(stamp, side)
def cdr_imu(stamp, gyro): return CDRWriter().imu(stamp, gyro)


def synthetic_db3(path):
    conn = sqlite3.connect(path)
    conn.executescript("""
      CREATE TABLE topics(id INTEGER PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL,
        serialization_format TEXT NOT NULL, offered_qos_profiles TEXT NOT NULL);
      CREATE TABLE messages(id INTEGER PRIMARY KEY, topic_id INTEGER NOT NULL, timestamp INTEGER NOT NULL,
        data BLOB NOT NULL);
    """)
    topic_ids = {}
    for ident, (name, typ) in enumerate(TOPICS.values(), 1):
        topic_ids[name] = ident
        conn.execute("INSERT INTO topics VALUES(?,?,?,?,?)", (ident, name, typ, "cdr", ""))
    entries = []
    period_img = round(1e9 / val("image_rate_hz"))
    period_imu = round(1e9 / val("imu_rate_hz"))
    start = val("device_header_start_ns")
    end_ns = round(val("duration_s") * 1e9)
    for i in range(round(val("duration_s") * val("image_rate_hz"))):
        stamp = start + i * period_img
        entries.extend([(stamp, "ir1", cdr_image(stamp, "left")),
                        (stamp, "ir2", cdr_image(stamp, "right"))])
    for i in range(round(val("duration_s") * val("imu_rate_hz")) + 1):
        stamp = start + i * period_imu
        entries.extend([(stamp, "gyro", cdr_imu(stamp, True)),
                        (stamp, "accel", cdr_imu(stamp, False))])
    entries.sort(key=lambda row: row[0])
    base_rx = val("bag_receive_start_ns")
    drift = 1 + val("drift_ppm") / 1_000_000
    for index, (stamp, key, blob) in enumerate(entries, 1):
        receive = base_rx + val("clock_offset_ns") + round((stamp - start) * drift)
        conn.execute("INSERT INTO messages VALUES(?,?,?,?)", (index, topic_ids[TOPICS[key][0]], receive, blob))
    conn.commit(); conn.close()
    return start, end_ns


def write_qual_config(path):
    base = json.loads((ROOT / "lab/rosbag_qual/config.json").read_text())
    specs = []
    roles = {"ir1": "image_left", "ir2": "image_right", "gyro": "gyro", "accel": "accel"}
    for key, (name, typ) in TOPICS.items():
        hz = val("image_rate_hz") if key.startswith("ir") else val("imu_rate_hz")
        tolerance = val("qualification_rate_tolerance_hz")
        specs.append({"name": name, "type": typ, "role": roles[key], "required": True,
                      "nominal_hz": hz, "rate_min_hz": hz - tolerance, "rate_max_hz": hz + tolerance,
                      "max_gap_s": val("topic_gap_limit_s"), "drop_gap_factor": val("drop_gap_factor"),
                      "threshold_source": "PROPOSED synthetic rehearsal config; no hardware acceptance claim"})
    base["topics"] = specs
    base["pairing"] = {"left_role": "image_left", "right_role": "image_right",
                       "min_fraction": val("pair_fraction_minimum"),
                       "threshold_source": "PROPOSED synthetic exact pairing contract"}
    base["storage"].update({"max_write_rate_bps": 100_000_000,
                            "min_duration_s": val("duration_s") * 0.8,
                            "threshold_source": "PROPOSED synthetic fixture limits; not storage qualification"})
    base["validation"]["threshold_source"] = "PROPOSED synthetic fixture has monotonic CDR timestamps"
    path.write_text(json.dumps(base, indent=2) + "\n")


def invoke(args, *, timeout=100):
    return subprocess.run([sys.executable, "-B", *map(str, args)], cwd=ROOT,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, timeout=timeout, check=False)


def write_fake_accuracy_inputs(sequence, export, run):
    stamps = [int(row) for row in (export / "times_ns.txt").read_text().splitlines()]
    gt = sequence / "state_groundtruth_estimate0.csv"
    trajectory = run / "f_synthetic.txt"
    noise = val("image_noise_amplitude_m")
    with gt.open("w") as g, trajectory.open("w") as e:
        for i, stamp in enumerate(stamps):
            t = i / val("image_rate_hz")
            pos = (0.4 * t, 0.1 * math.sin(t), 0.05 * math.cos(0.7 * t))
            error = (noise * math.sin(i * 1.7), noise * math.cos(i * 1.3), noise * math.sin(i * 0.9))
            g.write(f"{stamp}," + ",".join(f"{x:.12f}" for x in (*pos, 0, 0, 0, 1,
                   0, 0, 0, 0, 0, 0, 0, 0, 0, 0)) + "\n")
            estimate = tuple(pos[j] + error[j] for j in range(3))
            e.write(f"{stamp} " + " ".join(f"{x:.12f}" for x in (*estimate, 0, 0, 0, 1)) + "\n")
    (run / "exit_code.txt").write_text("0\n")
    (run / "stdout.log").write_text("IMU initialized\n")
    return gt, trajectory


def synthetic_mapping(session):
    raw = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
    base = val("synthetic_camera_epoch_ns")
    age = val("health_pose_age_ns")
    offset = raw - age - base
    return {"valid": True, "snapshot_domain": "synthetic_device_clock",
            "camera_domain": "D435i_global_time", "pi_domain": "CLOCK_MONOTONIC_RAW",
            "camera_session": session, "pi_session": "synthetic-host-session",
            "exchanges_ns": [[a, a + offset + val("synthetic_clock_exchange_transport_ns"),
                              a + offset + 2 * val("synthetic_clock_exchange_transport_ns"),
                              a + 3 * val("synthetic_clock_exchange_transport_ns")]
                             for a in (base - 2 * val("synthetic_clock_exchange_spacing_ns"),
                                       base - val("synthetic_clock_exchange_spacing_ns"), base)]}


class RehearsalTests(unittest.TestCase):
    def test_result_contract_status_fixture_paths(self):
        # Small fixture-level guard for contract precedence used by all stages.
        fixture = {"PASS": ["PASS"], "FAIL": ["PASS", "FAIL"], "BLOCKED": ["PASS", "BLOCKED"]}
        for expected, states in fixture.items():
            actual = "FAIL" if "FAIL" in states else "BLOCKED" if "BLOCKED" in states else "PASS"
            self.assertEqual(actual, expected)

    def test_synthetic_pipeline(self):
        with tempfile.TemporaryDirectory(prefix="wbr-e2e-rehearsal-") as temp:
            work = Path(temp)
            bag = work / "synthetic.db3"
            header_start, duration_ns = synthetic_db3(bag)

            qual_config = work / "rosbag-config.json"
            write_qual_config(qual_config)
            rosbag_out = work / "rosbag-qual"
            proc = invoke(["lab/rosbag_qual/analyze_bag.py", "--bag", bag, "--config", qual_config,
                           "--output-dir", rosbag_out])
            self.assertEqual(proc.returncode, 0, proc.stdout[-3000:])
            self.assertEqual(json.loads((rosbag_out / "result.json").read_text())["status"], "PASS")
            self.assertTrue((rosbag_out / "analysis.json").is_file())

            drift_out = work / "stamp-drift"
            proc = invoke(["tools/stamp_drift/analyze.py", bag, "--header-clock", "D435I_GLOBAL_TIME",
                           "--global-time-enabled", "true", "--output-dir", drift_out])
            self.assertEqual(proc.returncode, 0, proc.stdout[-3000:])
            drift_result = json.loads((drift_out / "result.json").read_text())
            report = json.loads((drift_out / "report.json").read_text())
            self.assertEqual(drift_result["status"], "PASS")
            fitted = [s["drift_ppm"] for s in report["streams"]]
            self.assertTrue(fitted)
            self.assertTrue(all(abs(x - val("drift_ppm")) <= val("drift_tolerance_ppm") for x in fitted), fitted)

            euroc = work / "euroc"
            proc = invoke(["tools/n4b_offline/db3_to_euroc.py", bag, euroc])
            self.assertEqual(proc.returncode, 0, proc.stdout[-3000:])
            qualified = work / "euroc-qual"
            proc = invoke(["tools/n4b_offline/qualify_euroc.py", euroc, "--outdir", qualified])
            self.assertEqual(proc.returncode, 0, proc.stdout[-3000:])
            self.assertEqual(json.loads((qualified / "result.json").read_text())["status"], "PASS")
            self.assertEqual(json.loads((euroc / "metadata.json").read_text())["imu_combination_policy"]["driver_method"], "UNKNOWN")

            bad_export = work / "bad-euroc"
            shutil.copytree(euroc, bad_export)
            right_csv = bad_export / "mav0/cam1/data.csv"
            right_csv.write_text(right_csv.read_text().replace(
                str(header_start), str(header_start + val("stereo_timestamp_fault_ns")), 1))
            failed = work / "euroc-fail"
            proc = invoke(["tools/n4b_offline/qualify_euroc.py", bad_export, "--outdir", failed])
            self.assertEqual(proc.returncode, 1, proc.stdout[-2000:])
            self.assertEqual(json.loads((failed / "result.json").read_text())["status"], "FAIL")
            blocked = work / "euroc-blocked"
            proc = invoke(["tools/n4b_offline/qualify_euroc.py", work / "missing-euroc", "--outdir", blocked])
            self.assertEqual(proc.returncode, 2, proc.stdout[-2000:])
            self.assertEqual(json.loads((blocked / "result.json").read_text())["status"], "BLOCKED")

            sequence, run = work / "sequence", work / "fake-orb-run"
            sequence.mkdir(); run.mkdir()
            gt, _ = write_fake_accuracy_inputs(sequence, euroc, run)
            evaluated = work / "accuracy"
            proc = invoke(["tools/eval_pipeline/accuracy/evaluate.py", "--sequence", "SYNTHETIC",
                           "--runs", run, "--ground-truth", gt, "--times", euroc / "times_ns.txt",
                           "--out", evaluated])
            self.assertEqual(proc.returncode, 0, proc.stdout[-3000:])
            summary = json.loads((evaluated / "summary.json").read_text())
            self.assertEqual(summary["status"], "PASS")
            ate = summary["aggregate_ate_rmse_se3_m"]["mean"]
            self.assertIsNotNone(ate)
            self.assertLess(abs(ate - val("image_noise_amplitude_m")), val("ate_tolerance_m"), ate)

            states, health_debug = self.run_health_pty(work)
            self.assertEqual(states, ["HOLD", "FRESH"], health_debug)

    def run_health_pty(self, work):
        session = "synthetic-camera-session"
        un_mapped = Converter(session).convert({"source_ns": val("synthetic_camera_epoch_ns"),
            "domain": "synthetic_device_clock", "state": "TRACKING", "valid": True,
            "reasons": 0, "orb_tracking_state": "OK", "reset_counter": 0,
            "imu_initialized": True, "tracked_features": 77})
        master, slave = pty.openpty()
        sender = ROOT / "tools/perception_health/py/sender.py"
        launcher = ("import runpy,sys,pathlib; sys.path.insert(0," + repr(str(ROOT)) + "); "
                    "import tools.clockmap.clockmap; sys.path.insert(0," + repr(str(sender.parent)) + "); "
                    "runpy.run_path(" + repr(str(sender)) + ",run_name='__main__')")
        proc = subprocess.Popen([sys.executable, "-B", "-c", launcher, "--device", os.ttyname(slave),
                                "--session-id", "9"], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        parser, frames = StreamParser(), []
        model = SupervisorModel(primary_fresh=True)
        states = []
        debug = []
        start = time.monotonic_ns()
        deadline = time.monotonic() + val("health_pty_timeout_s")
        try:
            while time.monotonic() < deadline and not any(t == TYPE_HEARTBEAT for t, _, _ in frames):
                ready, _, _ = select.select([master], [], [], 0.1)
                if ready:
                    frames.extend(parser.feed(os.read(master, 65536)))
            self.assertTrue(any(t == TYPE_HEARTBEAT for t, _, _ in frames), "sender readiness heartbeat absent")
            for typ, seq, payload in frames:
                if typ == TYPE_HEARTBEAT:
                    _, session_id = HEARTBEAT.unpack(payload)
                    now = (time.monotonic_ns() - start) // 1000
                    model.update(now, Event("heartbeat", now, session_id=session_id, wire_seq=seq))
            # Anchor the assumed camera→CLOCK_MONOTONIC_RAW mapping immediately
            # before sending so process startup is not mistaken for pose age.
            __import__("tools.clockmap.clockmap")
            map_path = work / "synthetic-clockmap.json"
            map_path.write_text(json.dumps(synthetic_mapping(session)) + "\n")
            mapping = load_mapping(map_path)
            mapped = Converter(session, mapping).convert({"source_ns": val("synthetic_camera_epoch_ns"),
                "domain": "synthetic_device_clock", "state": "TRACKING", "valid": True,
                "reasons": 0, "orb_tracking_state": "OK", "reset_counter": 0,
                "imu_initialized": True, "tracked_features": 77})
            events = [un_mapped, mapped]
            seen = 0
            for event_index, event in enumerate(events, 1):
                proc.stdin.write((json.dumps(event) + "\n").encode()); proc.stdin.flush()
                while seen < event_index and time.monotonic() < deadline:
                    ready, _, _ = select.select([master], [], [], 0.1)
                    if ready:
                        frames.extend(parser.feed(os.read(master, 65536)))
                    health = [(t, seq, payload) for t, seq, payload in frames if t == TYPE_PERCEPTION_HEALTH]
                    if len(health) > seen:
                        _, seq, payload = health[seen]
                        value = decode_health_payload(payload)
                        now = (time.monotonic_ns() - start) // 1000
                        model.update(now, Event("health", now, value.pose_age_us,
                            value.tracking_state, value.flags, map_reset_counter=value.map_reset_counter,
                            imu_initialized=value.imu_initialized, wire_seq=seq))
                        states.append(model.state); seen += 1
                        debug.append({"age_us": value.pose_age_us, "flags": value.flags,
                                      "tracking": value.tracking_state, "reason": model.reason})
            proc.stdin.close()
            proc.wait(timeout=val("sender_shutdown_timeout_s"))
            self.assertEqual(proc.returncode, 0, proc.stderr.read().decode(errors="replace"))
            self.assertEqual(len([1 for t, _, _ in frames if t == TYPE_PERCEPTION_HEALTH]), 2, debug)
            return states, debug
        finally:
            if proc.poll() is None:
                proc.kill(); proc.wait()
            if proc.stdout: proc.stdout.close()
            if proc.stderr: proc.stderr.close()
            os.close(master); os.close(slave)


if __name__ == "__main__":
    unittest.main()
