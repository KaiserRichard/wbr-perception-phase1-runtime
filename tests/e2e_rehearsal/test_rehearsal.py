#!/usr/bin/env python3
"""Synthetic end-to-end rehearsal of existing WBR tool interfaces."""
from __future__ import annotations

import json
import csv
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
    def __init__(self, *, legacy_imu_alignment=False):
        self.legacy_imu_alignment = legacy_imu_alignment
        self.data = bytearray(b"\x00\x01\x00\x00")

    def put(self, fmt, *values):
        alignment = min(struct.calcsize("<" + fmt[0]), 8)
        origin = 0 if self.legacy_imu_alignment else 4
        self.data.extend(b"\0" * ((-(len(self.data) - origin)) % alignment))
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
        self.put("ddd", *( (0.01, 0.02, 0.03) if gyro else (0.0, 0.0, 0.0)))
        self.put("d" * 9, *([0.0] * 9))
        self.put("ddd", *( (0.0, 0.0, 0.0) if gyro else (0.0, 0.0, 9.81)))
        self.put("d" * 9, *([0.0] * 9))
        return bytes(self.data)


def cdr_image(stamp, side): return CDRWriter().image(stamp, side)
def cdr_imu(stamp, gyro, *, legacy_imu_alignment=False):
    return CDRWriter(legacy_imu_alignment=legacy_imu_alignment).imu(stamp, gyro)


def synthetic_db3(path, *, legacy_imu_alignment=False):
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
        entries.extend([(stamp, "gyro", cdr_imu(stamp, True, legacy_imu_alignment=legacy_imu_alignment)),
                        (stamp, "accel", cdr_imu(stamp, False, legacy_imu_alignment=legacy_imu_alignment))])
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
    base["storage"].update({"max_write_rate_bps": val("synthetic_storage_ceiling_bps"),
                            "min_duration_s": val("duration_s") * val("synthetic_min_duration_fraction"),
                            "threshold_source": "PROPOSED synthetic fixture limits; not storage qualification"})
    base["validation"]["threshold_source"] = "PROPOSED synthetic fixture has monotonic CDR timestamps"
    path.write_text(json.dumps(base, indent=2) + "\n")


def invoke(args, *, timeout=None):
    timeout = val("cli_timeout_s") if timeout is None else timeout
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
            # Distinct complete Fourier modes are centered and mutually orthogonal.
            # Thus E.T @ P == 0: SE3 fits identity and RMSE = amplitude * sqrt(3/2).
            phase = 2 * math.pi * i / len(stamps)
            pos = (0.4 * math.cos(phase), 0.4 * math.sin(phase), 0.1 * math.sin(2 * phase))
            error = (noise * math.sin(3 * phase), noise * math.cos(3 * phase), noise * math.sin(4 * phase))
            g.write(f"{stamp}," + ",".join(f"{x:.12f}" for x in (*pos, 1, 0, 0, 0,
                   0, 0, 0, 0, 0, 0, 0, 0, 0, 0)) + "\n")
            estimate = tuple(pos[j] + error[j] for j in range(3))
            e.write(f"{stamp} " + " ".join(f"{x:.12f}" for x in (*estimate, 0, 0, 0, 1)) + "\n")
    (run / "exit_code.txt").write_text("0\n")
    (run / "stdout.log").write_text("IMU initialized\n")
    return gt, trajectory


def synthetic_mapping(session, source_epoch_ns=None):
    raw = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
    base = val("synthetic_camera_epoch_ns") if source_epoch_ns is None else source_epoch_ns
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
    def test_compatibility_pipeline(self):
        # R26-01: only this downstream exercise uses exporter-compatible IMU padding.
        started = time.monotonic()
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
            replay = invoke(["lab/rosbag_qual/analyze_bag.py", "--analyze-only", rosbag_out])
            self.assertEqual(replay.returncode, 0, replay.stdout)
            self.assertEqual(json.loads((rosbag_out / "result.json").read_text())["status"], "PASS")

            drift_out = work / "stamp-drift"
            proc = invoke(["tools/stamp_drift/analyze.py", bag, "--header-clock", "D435I_GLOBAL_TIME",
                           "--global-time-enabled", "true", "--output-dir", drift_out])
            self.assertEqual(proc.returncode, 0, proc.stdout[-3000:])
            drift_result = json.loads((drift_out / "result.json").read_text())
            report = json.loads((drift_out / "report.json").read_text())
            self.assertEqual(drift_result["status"], "PASS")
            fitted = [s["drift_ppm"] for s in report["streams"]]
            self.assertEqual({s["topic"] for s in report["streams"]}, {n for n, _ in TOPICS.values()})
            self.assertTrue(all(abs(x - val("drift_ppm")) <= val("drift_tolerance_ppm") for x in fitted), fitted)

            # R26-01 blocks the standard bag at export. Keep it unchanged and
            # adapt only IMU padding in a separately named downstream fixture.
            export_bag = work / "exporter-compatibility.db3"
            shutil.copyfile(bag, export_bag)
            with sqlite3.connect(export_bag) as db:
                for key in ("gyro", "accel"):
                    ident = db.execute("SELECT id FROM topics WHERE name=?", (TOPICS[key][0],)).fetchone()[0]
                    for row_id, blob in db.execute("SELECT id,data FROM messages WHERE topic_id=?", (ident,)).fetchall():
                        sec, nanosec = struct.unpack_from("<iI", blob, 4)
                        payload = cdr_imu(sec * 1_000_000_000 + nanosec, key == "gyro", legacy_imu_alignment=True)
                        db.execute("UPDATE messages SET data=? WHERE id=?", (payload, row_id))
            euroc = work / "euroc"
            proc = invoke(["tools/n4b_offline/db3_to_euroc.py", export_bag, euroc])
            self.assertEqual(proc.returncode, 0, proc.stdout[-3000:])
            qualified = work / "euroc-qual"
            proc = invoke(["tools/n4b_offline/qualify_euroc.py", euroc, "--outdir", qualified])
            self.assertEqual(proc.returncode, 0, proc.stdout[-3000:])
            self.assertEqual(json.loads((qualified / "result.json").read_text())["status"], "PASS")
            self.assertEqual(json.loads((euroc / "metadata.json").read_text())["imu_combination_policy"]["driver_method"], "UNKNOWN")
            with (euroc / "mav0/imu0/data.csv").open() as stream:
                rows = list(csv.reader(stream))[1:]
            self.assertTrue(rows)
            for row in rows:
                self.assertEqual(tuple(map(float, row[1:])), (0.01, 0.02, 0.03, 0.0, 0.0, 9.81))

            bad_export = work / "bad-euroc"
            shutil.copytree(euroc, bad_export)
            right_csv = bad_export / "mav0/cam1/data.csv"
            right_csv.write_text(right_csv.read_text().replace(
                str(header_start), str(header_start + val("stereo_timestamp_fault_ns")), 1))
            failed = work / "euroc-fail"
            proc = invoke(["tools/n4b_offline/qualify_euroc.py", bad_export, "--outdir", failed])
            self.assertEqual(proc.returncode, 1, proc.stdout[-2000:])
            failure = json.loads((failed / "result.json").read_text())
            self.assertEqual(failure["status"], "FAIL")
            self.assertEqual(next(c for c in failure["criteria"] if c["id"] == "stereo_stamps")["status"], "FAIL")
            blocked = work / "euroc-blocked"
            proc = invoke(["tools/n4b_offline/qualify_euroc.py", work / "missing-euroc", "--outdir", blocked])
            self.assertEqual(proc.returncode, 2, proc.stdout[-2000:])
            missing = json.loads((blocked / "result.json").read_text())
            self.assertEqual(missing["status"], "BLOCKED")
            self.assertEqual(next(c for c in missing["criteria"] if c["id"] == "layout")["status"], "BLOCKED")

            sequence, run = work / "sequence", work / "fake-orb-run"
            sequence.mkdir(); run.mkdir()
            gt, trajectory = write_fake_accuracy_inputs(sequence, euroc, run)
            evaluated = work / "accuracy"
            proc = invoke(["tools/eval_pipeline/accuracy/evaluate.py", "--sequence", "SYNTHETIC",
                           "--runs", run, "--ground-truth", gt, "--times", euroc / "times_ns.txt",
                           "--out", evaluated])
            self.assertEqual(proc.returncode, 0, proc.stdout[-3000:])
            summary = json.loads((evaluated / "summary.json").read_text())
            self.assertEqual(summary["status"], "PASS")
            self.assertEqual(len((euroc / "times_ns.txt").read_text().splitlines()), val("ground_truth_samples"))
            ate = summary["aggregate_ate_rmse_se3_m"]["mean"]
            self.assertIsNotNone(ate)
            self.assertLess(abs(ate - val("image_noise_amplitude_m") * math.sqrt(1.5)), val("ate_tolerance_m"), ate)

            self.run_health_pty(work, trajectory)
            health = json.loads((work / "health-summary.json").read_text())
            self.assertGreaterEqual(len(health["states"]), 3, health)
            self.assertEqual(health["states"][:-1], ["HOLD"] * (len(health["states"]) - 1), health)
            self.assertEqual(health["states"][-1], "FRESH", health)
            self.assertEqual([item["flags"] for item in health["decoded_health"]],
                             [0] * (len(health["states"]) - 1) + [3], health)
            self.assertLess(time.monotonic() - started, val("rehearsal_runtime_limit_s"))

    def run_health_pty(self, work, trajectory):
        pose = trajectory.read_text().splitlines()[-1].split()
        latest_source_ns = int(pose[0])
        session = "synthetic-camera-session"
        snapshot = {"source_ns": latest_source_ns, "position_m": list(map(float, pose[1:4])),
            "domain": "synthetic_device_clock", "state": "TRACKING", "valid": True,
            "reasons": 0, "orb_tracking_state": "OK", "reset_counter": 0,
            "imu_initialized": True, "tracked_features": 77}
        snapshot_path = work / "snapshot.jsonl"
        snapshot_path.write_text(json.dumps(snapshot) + "\n")
        converter_cli = ROOT / "tools/perception_health/integration/vio_to_pose_events.py"
        converted = invoke([converter_cli, "--input", snapshot_path, "--snapshot-session", session])
        self.assertEqual(converted.returncode, 0, converted.stdout)
        (work / "unmapped-events.jsonl").write_text(converted.stdout)
        un_mapped = json.loads((work / "unmapped-events.jsonl").read_text())
        self.assertFalse(un_mapped["mapping"]["valid"])
        master, slave = pty.openpty()
        sender = ROOT / "tools/perception_health/py/sender.py"
        proc = subprocess.Popen([sys.executable, "-B", str(sender), "--device", os.ttyname(slave),
                                "--session-id", "9"], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=ROOT)
        parser = StreamParser()
        model = SupervisorModel(primary_fresh=True)
        states, debug, wire_sequences = [], [], []
        wire = bytearray()
        start = time.monotonic_ns()
        deadline = time.monotonic() + val("health_pty_timeout_s")
        converter = None

        def read_frames(wait_s=0.1):
            ready, _, _ = select.select([master], [], [], wait_s)
            if not ready:
                return
            chunk = os.read(master, 65536)
            wire.extend(chunk)
            for typ, seq, payload in parser.feed(chunk):
                wire_sequences.append(seq)
                # Simulated MCU-local timer: elapsed CLOCK_MONOTONIC durations only.
                now = (time.monotonic_ns() - start) // 1000
                if typ == TYPE_HEARTBEAT:
                    _, session_id = HEARTBEAT.unpack(payload)
                    model.update(now, Event("heartbeat", now, session_id=session_id, wire_seq=seq))
                elif typ == TYPE_PERCEPTION_HEALTH:
                    value = decode_health_payload(payload)
                    model.update(now, Event("health", now, value.pose_age_us,
                        value.tracking_state, value.flags, map_reset_counter=value.map_reset_counter,
                        imu_initialized=value.imu_initialized, wire_seq=seq))
                    states.append(model.state)
                    debug.append({"age_us": value.pose_age_us, "flags": value.flags,
                                  "tracking": value.tracking_state, "reason": model.reason})

        def send_event(event):
            expected = len(states) + 1
            proc.stdin.write((json.dumps(event) + "\n").encode()); proc.stdin.flush()
            while len(states) < expected and time.monotonic() < deadline:
                read_frames()
            self.assertEqual(len(states), expected, debug)

        try:
            while not wire_sequences and time.monotonic() < deadline:
                read_frames()
            self.assertTrue(wire_sequences, "sender readiness heartbeat absent")
            send_event(un_mapped)
            # Exercise unavailable mapping through the direct sender CLI. This also
            # pays its cold NumPy import before a freshly timestamped mapped pose.
            invalid = dict(un_mapped, mapping={"valid": True, "camera_domain": "D435i_global_time",
                "pi_domain": "CLOCK_MONOTONIC_RAW", "camera_session": session,
                "pi_session": "synthetic-host-session", "exchanges_ns": []})
            send_event(invalid)
            map_path = work / "synthetic-clockmap.json"
            mapping = synthetic_mapping(session, latest_source_ns - val("health_mapping_preparation_ns"))
            snapshot["source_ns"] = latest_source_ns - val("health_mapping_preparation_ns")
            map_path.write_text(json.dumps(mapping) + "\n")
            converter = subprocess.Popen([sys.executable, "-B", "-u", str(converter_cli),
                "--snapshot-session", session, "--clockmap", str(map_path)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=ROOT)
            # A priming row proves the persistent converter has loaded its map.
            converter.stdin.write(json.dumps(snapshot) + "\n"); converter.stdin.flush()
            while not select.select([converter.stdout], [], [], 0)[0]:
                self.assertLess(time.monotonic(), deadline, "converter startup timed out")
                read_frames()
                send_event(un_mapped)
            primed = json.loads(converter.stdout.readline())
            self.assertTrue(primed["mapping"]["valid"])
            t1, t2, _, _ = mapping["exchanges_ns"][-1]
            offset = t2 - t1 - val("synthetic_clock_exchange_transport_ns")
            # Schedule the last fake trajectory stamp into the explicit synthetic
            # map's Pi raw-clock timeline, preserving its acquisition epoch.
            target_raw_ns = latest_source_ns + offset + val("health_pose_age_ns")
            while time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) < target_raw_ns:
                self.assertLess(time.monotonic(), deadline, "synthetic mapping preparation timed out")
                remaining_s = (target_raw_ns - time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)) / 1e9
                read_frames(min(0.1, max(0, remaining_s)))
                # Ongoing unavailable reports keep the independent receipt watchdog
                # alive while the synthetic acquisition epoch approaches.
                if time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) < target_raw_ns:
                    send_event(un_mapped)
            snapshot["source_ns"] = latest_source_ns
            (work / "mapped-snapshot.jsonl").write_text(json.dumps(snapshot) + "\n")
            converter.stdin.write(json.dumps(snapshot) + "\n"); converter.stdin.close()
            self.assertTrue(select.select([converter.stdout], [], [], val("cli_timeout_s"))[0])
            event_line = converter.stdout.readline()
            (work / "mapped-events.jsonl").write_text(event_line)
            mapped = json.loads((work / "mapped-events.jsonl").read_text())
            self.assertTrue(mapped["mapping"]["valid"])
            send_event(mapped)
            converter.wait(timeout=val("sender_shutdown_timeout_s"))
            converter_stderr = converter.stderr.read()
            (work / "converter.stderr.log").write_text(converter_stderr)
            self.assertEqual(converter.returncode, 0, converter_stderr)
            proc.stdin.close()
            proc.wait(timeout=val("sender_shutdown_timeout_s"))
            sender_stderr = proc.stderr.read()
            (work / "sender.stderr.log").write_bytes(sender_stderr)
            (work / "sender.stdout.log").write_bytes(proc.stdout.read())
            self.assertEqual(proc.returncode, 0, sender_stderr.decode(errors="replace"))
            while select.select([master], [], [], 0)[0]:
                read_frames()
            self.assertEqual(wire_sequences, list(range(len(wire_sequences))))
            self.assertFalse(parser.buf)
            self.assertEqual((parser.crc_errors, parser.len_errors, parser.bytes_dropped), (0, 0, 0))
            (work / "uart.bin").write_bytes(wire)
            (work / "health-summary.json").write_text(json.dumps({
                "evidence": "CALCULATED synthetic PTY policy; not a gate PASS",
                "primary_fresh": True, "states": states, "decoded_health": debug,
                "wire_sequences": wire_sequences, "bytes_received": len(wire),
                "source_ns": latest_source_ns}, indent=2) + "\n")
        finally:
            for child in (converter, proc):
                if child is not None:
                    if child.poll() is None:
                        child.kill(); child.wait()
                    for stream in (child.stdin, child.stdout, child.stderr):
                        if stream and not stream.closed: stream.close()
            os.close(master); os.close(slave)


if __name__ == "__main__":
    unittest.main()
