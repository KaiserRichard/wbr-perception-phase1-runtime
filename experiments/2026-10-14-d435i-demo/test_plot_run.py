#!/usr/bin/env python3
"""Synthetic/offline checks only; no sensor, SDK, or ORB-SLAM3 execution."""
import csv
import json
from pathlib import Path
import tempfile
import unittest

import plot_run as demo
import numpy as np

ROOT = Path(__file__).resolve().parent


class OfflineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic-", dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)

    def write_poses(self, name, xyz, times=None):
        times = np.arange(len(xyz)) if times is None else np.asarray(times)
        poses = np.column_stack([times * 1e9, xyz, np.tile([0, 0, 0, 1], (len(xyz), 1))])
        np.savetxt(self.run / name, poses)
        return poses

    def test_complete_synthetic_run(self):
        self.write_poses("f_fixture.txt", [[0, 0, 0], [1, 0, 0], [1, 1, 0]])
        self.write_poses("kf_fixture.txt", [[0, 0, 0], [1, 1, 0]], [0, 2])
        with (self.run / "timestamps.csv").open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow("stream,index,frame_number,sdk_ms,domain,host_steady_ns,host_utc_ns,x,y,z,exposure_us".split(","))
            for stream, index, times in [("Infrared", 1, [0, 100, 300]), ("Infrared", 2, [0, 200]),
                                         ("Gyro", 0, [100, 90, 110])]:
                for number, stamp in enumerate(times):
                    writer.writerow([stream, index, number, stamp, "hardware_clock", number * 100000000,
                                     0, 0, 0, 0, 1000])
        (self.run / "power.log").write_text(
            "87 throttled=0x50005\n"  # Summary is not another raw sample.
            "2026-10-14T00:00:00Z throttled=0x50000 EXT5V_V temp=50'C frequency(0)=1000\n"
            "2026-10-14T00:00:01Z throttled=0x50005 EXT5V_V temp=50'C frequency(0)=1000\n"
            "2026-10-14T00:00:02Z throttled=0x8 EXT5V_V temp=50'C frequency(0)=1000\n"
            "2026-10-14T00:00:03Z throttled=0x0 EXT5V_V temp=50'C frequency(0)=1000\n")
        result = demo.analyze_run(self.run)
        self.assertEqual(result["path_length_m"], 2)
        self.assertEqual(result["duration_s"], 2)
        self.assertEqual(result["extent_m"], {"x": 1, "y": 1, "z": 0})
        self.assertEqual(result["num_keyframes"], 2)
        self.assertEqual(result["pose_rate_hz"], 1)
        self.assertAlmostEqual(result["streams"]["Infrared:1"]["rate_hz"], 2 / 0.3)
        self.assertAlmostEqual(result["streams"]["Infrared:1"]["max_gap_s"], 0.2)
        self.assertEqual(result["streams"]["Infrared:2"]["rate_hz"], 5)
        self.assertEqual(result["streams"]["Gyro:0"]["nonpositive_steps"], 1)
        self.assertIsNone(result["streams"]["Gyro:0"]["rate_hz"])
        self.assertEqual(result["power"]["samples"], 4)
        self.assertEqual(result["power"]["live_bits_0_3_fraction"], 0.5)
        self.assertEqual(result["power"]["live_undervoltage_bit_0_fraction"], 0.25)
        self.assertEqual(json.loads((self.run / "demo_stats.json").read_text()), result)
        self.assertTrue((self.run / "demo_plot.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))

    def test_rigid_alignment_and_no_scale_correction(self):
        xyz = np.array([[0, 0, 0], [1, 0, 0], [0, 2, 0], [0, 0, 3]], dtype=float)
        rotation = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
        target = xyz @ rotation.T + [3, -4, 5]
        recovered_rotation, recovered_translation = demo.align_se3(xyz, target)
        np.testing.assert_allclose(recovered_rotation, rotation, atol=1e-12)
        np.testing.assert_allclose(recovered_translation, [3, -4, 5], atol=1e-12)
        r, t = demo.align_se3(xyz, target * 2)
        self.assertGreater(np.linalg.norm(xyz @ r.T + t - target * 2), 1)
        r, _ = demo.align_se3(xyz, xyz * [-1, 1, 1])
        self.assertAlmostEqual(np.linalg.det(r), 1)  # Reflections must not be SE3.
        with self.assertRaisesRegex(ValueError, "underconstrained"):
            demo.align_se3(np.zeros((3, 3)), np.zeros((3, 3)))

    def test_timestamp_association_and_insufficient_overlap(self):
        xyz = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        estimate = np.column_stack([np.arange(3), xyz])
        reference = np.column_stack([np.arange(3) + 0.01, xyz])
        self.assertLess(demo.ate_stats(estimate, reference)["rmse_m"], 1e-12)
        reference[:, 0] += 10
        with self.assertRaisesRegex(ValueError, "three timestamp matches"):
            demo.associate(estimate, reference)

    def test_keyframe_coordinate_reconciliation(self):
        xyz = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        frames = self.write_poses("f_fixture.txt", xyz)
        frames[:, 0] /= 1e9
        keyframes = frames.copy()
        rotation = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
        keyframes[:, 1:4] = xyz @ rotation.T + [3, -4, 5]
        keyframes[:, 4:] = [0, 0, np.sqrt(0.5), np.sqrt(0.5)]
        reconciled, info = demo.keyframes_in_frame_coordinates(frames, keyframes)
        np.testing.assert_allclose(reconciled[:, 1:4], xyz, atol=1e-12)
        self.assertEqual(info["shared_poses"], 3)
        keyframes[1, 1] += 1
        with self.assertRaisesRegex(ValueError, "export mismatch"):
            demo.keyframes_in_frame_coordinates(frames, keyframes)
        keyframes[:, 0] += 0.2
        with self.assertRaisesRegex(ValueError, "No shared"):
            demo.keyframes_in_frame_coordinates(frames, keyframes)

    def test_epoch_nanoseconds_conversion(self):
        path = self.run / "f_epoch.txt"
        path.write_text("1403636580063555584.000000 0 0 0 0 0 0 1\n")
        self.assertEqual(demo.read_trajectory(path, 1e9)[0, 0], 1403636580.063555479)

    def test_mixed_domains_invalidate_sdk_rate(self):
        path = self.run / "timestamps.csv"
        path.write_text("stream,index,sdk_ms,domain,host_steady_ns\n"
                        "Gyro,0,0,hardware_clock,0\nGyro,0,5,system_time,5000000\n")
        stream = demo.stream_stats(path)["Gyro:0"]
        self.assertIsNone(stream["rate_hz"])
        self.assertIsNone(stream["max_gap_s"])
        self.assertEqual(stream["host_steady"]["rate_hz"], 200)

    def test_bad_trajectory_and_ambiguous_inputs(self):
        path = self.run / "f_fixture.txt"
        path.write_text("0 0 0 0 0 0 0 1\n0 1 0 0 0 0 0 1\n")
        with self.assertRaisesRegex(ValueError, "duplicate or backward"):
            demo.analyze_run(self.run)
        self.assertFalse((self.run / "demo_stats.json").exists())
        path.write_text("nan 0 0 0 0 0 0 1\n")
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            demo.analyze_run(self.run)
        path.write_text("0 0 0\n")
        with self.assertRaisesRegex(ValueError, "eight columns"):
            demo.analyze_run(self.run)
        (self.run / "f_other.txt").write_text("")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            demo.find_trajectories(self.run)

    def test_single_pose_without_optional_evidence(self):
        self.write_poses("f_fixture.txt", [[0, 0, 0]])
        result = demo.analyze_run(self.run)
        self.assertIsNone(result["pose_rate_hz"])
        self.assertEqual(result["num_keyframes"], 0)
        self.assertEqual(result["path_length_m"], 0)
        self.assertNotIn("streams", result)
        self.assertNotIn("power", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
