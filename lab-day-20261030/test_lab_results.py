"""Small synthetic evidence only; no hardware, network or archive writes."""
import contextlib
import csv
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('lab_results', Path(__file__).with_name('lab_results.py'))
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class LabResultsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'evidence'
        self.root.mkdir()

    def run_dir(self, name):
        run = self.root / name
        run.mkdir()
        return run

    def write_json(self, path, data):
        path.write_text(json.dumps(data))

    def live(self, name='arbitrary-name'):
        run = self.run_dir(name)
        self.write_json(run / 'summary.json', {'frames': 3, 'sent': 3, 'echoed': 3, 'loss': 0, 'rejected_echoes': 0})
        with (run / 'packets.csv').open('w', newline='') as stream:
            keys = ['seq', 'advisory', 'height_m', 'distance_m', 'frame_receipt_pi_ns', 'receipt_to_before_write_ns', 'rtt_ns', 'stale']
            writer = csv.writer(stream)
            writer.writerow(keys)
            writer.writerows([[0, '3', '', '', 1e9, 1e6, 1e5, 0],
                              [1, '1', .05, 2, 2e9, 2e6, 2e5, 1],
                              [2, '2', .15, 1, 3e9, 3e6, 3e5, 1]])
        return run

    def bag(self, run, *, stereo=False):
        import numpy as np
        from rosbags.rosbag2 import Writer
        from rosbags.typesys import Stores, get_typestore
        store = get_typestore(Stores.ROS2_JAZZY)
        types = store.types
        with Writer(run / 'bag', version=9) as writer:
            conns = {}
            for topic, msgtype in [(lab.POSE, 'geometry_msgs/msg/PoseStamped'),
                                   (lab.STATUS, 'std_msgs/msg/String'),
                                   (lab.SUGGESTION, 'std_msgs/msg/String')]:
                conns[topic] = writer.add_connection(topic, msgtype, typestore=store)
            if stereo:
                for topic in (lab.LEFT, lab.RIGHT):
                    conns[topic] = writer.add_connection(topic, 'sensor_msgs/msg/Image', typestore=store)
            for i in range(3):
                stamp = (i + 1) * 10**9
                header = types['std_msgs/msg/Header'](types['builtin_interfaces/msg/Time'](i + 1, 0), 'slam_world')
                pose = types['geometry_msgs/msg/PoseStamped'](header, types['geometry_msgs/msg/Pose'](
                    types['geometry_msgs/msg/Point'](float(i), 0., 0.), types['geometry_msgs/msg/Quaternion'](0., 0., 0., 1.)))
                payloads = {lab.POSE: pose,
                            lab.STATUS: types['std_msgs/msg/String'](json.dumps({'tracking_state': 2 if i else 4, 'pose_published': bool(i)})),
                            lab.SUGGESTION: types['std_msgs/msg/String'](json.dumps({'action': 'NO_POSE' if i == 0 else 'FORWARD', 'timings_ms': {'total': i + 1}}))}
                if stereo:
                    for topic in (lab.LEFT, lab.RIGHT):
                        payloads[topic] = types['sensor_msgs/msg/Image'](header, 1, 1, 'mono8', 0, 1, np.array([0], dtype=np.uint8))
                for topic, msg in payloads.items():
                    writer.write(conns[topic], stamp, store.serialize_cdr(msg, conns[topic].msgtype))

    def row(self, name):
        return next(r for r in lab.collect(self.root) if r['run'] == name)

    def test_missing_runs(self):
        rows = lab.collect(self.root)
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(r['status'] == 'MISSING' for r in rows))

    def test_live_reuses_summarizer_without_evidence_writes(self):
        run = self.live()
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in run.iterdir()}
        from tools.link_bench.pi import summarize_live
        with patch.object(summarize_live, 'summarize_run', wraps=summarize_live.summarize_run) as called:
            row = self.row(run.name)
        called.assert_called_once()
        m = row['metrics']
        self.assertEqual(m['advisory_histogram'], {'JUMP': 1, 'STOP': 1, 'UNCERTAIN': 1})
        self.assertEqual(m['first_confirmed_distance_m'], 2)
        self.assertAlmostEqual(m['confirmed_median_height_m'], .1)
        self.assertEqual(m['receipt_to_send_p50_ms'], 2)
        self.assertAlmostEqual(m['receipt_to_send_p95_ms'], 2.9)
        self.assertAlmostEqual(m['rtt_p99_ms'], .298)
        self.assertEqual(m['stale_events'], 1)
        self.assertNotIn('plot', m)
        self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in run.iterdir()})

    def test_capture_and_exact_header_pairing(self):
        run = self.run_dir('M1-lab-map')
        self.bag(run, stereo=True)
        self.write_json(run / 'capture_summary.json', {'measured_recording_window_seconds': 4, 'errors': [], 'process_returncodes': {'slam': 0}})
        (run / 'slam.log').write_text('Creation of new map with id: 0\nFail to track local map!\nFail to track local map!\nSYSTEM RESET\nCreation of new map with id: 1\n')
        (self.root / 'kernel-live.log').write_text('usb 1: reset SuperSpeed USB device\nnormal boot\n')
        row = self.row(run.name)
        m = row['metrics']
        self.assertEqual(m['paired_frames'], 3)
        self.assertEqual(m['paired_header_rate_hz'], 1)
        self.assertAlmostEqual(m['tracked_fraction'], 2/3)
        self.assertEqual(m['endpoint_m'], 2)
        self.assertEqual(m['track_failure_messages'], 2)
        self.assertEqual(m['map_creation_messages'], 2)
        self.assertEqual(m['reset_messages'], 1)
        self.assertEqual(m['kernel_errors'], 1)
        self.assertIn('endpoint, not accuracy', lab.render([row]))

    def test_sensor_only_capture_does_not_invent_tracking_or_pairing(self):
        run = self.run_dir('L1-3m-line')
        self.write_json(run / 'capture_summary.json', {'errors': []})
        (run / 'slam.log').write_text('Vocabulary loaded!\n')
        (run / 'bag-info.txt').write_text(f'Duration: 30.0s\nTopic: {lab.LEFT} | Type: Image | Count: 450\nTopic: {lab.RIGHT} | Type: Image | Count: 450\n')
        row = self.row(run.name)
        self.assertNotIn('paired_frames', row['metrics'])
        self.assertNotIn('tracked_fraction', row['metrics'])
        self.assertNotIn('endpoint_m', row['metrics'])
        self.assertEqual(row['metrics']['bag_duration_s'], 30)
        self.assertIsNone(row['metrics']['kernel_errors'])

    def test_capture_failure_keeps_metrics(self):
        run = self.run_dir('M1-lab-map')
        self.write_json(run / 'capture_summary.json', {'errors': ['recorder exited'], 'measured_recording_window_seconds': 5, 'process_returncodes': {'record': 1}})
        row = self.row(run.name)
        self.assertIn('FAIL: recorder exited', row['status'])
        self.assertEqual(row['metrics']['capture_window_s'], 5)

    def test_rgbd_and_planner_bag(self):
        approach = self.run_dir('A1-approach')
        planner = self.run_dir('P1-path-test')
        self.bag(approach)
        self.bag(planner)
        a = self.row(approach.name)['metrics']
        self.assertEqual(a['pose_count'], 3)
        self.assertEqual(a['orb_status_histogram'], {'4': 1, '2': 2})
        p = self.row(planner.name)['metrics']
        self.assertEqual(p['suggestion_counts'], {'NO_POSE': 1, 'FORWARD': 2})
        self.assertAlmostEqual(p['no_pose_fraction'], 1/3)
        self.assertEqual(p['planner_core_mean_ms'], 2)
        self.assertEqual(p['planner_core_max_ms'], 3)

    def test_planner_log_fallback_and_sheet(self):
        run = self.run_dir('P1-path-test')
        (run / 'planner.log').write_text('[INFO] {"action":"NO_POSE","timings_ms":{"total":4}}\n[INFO] {"action":"BLOCKED"}\n')
        (self.root / 'run_sheet.csv').write_text('run_id,outcome,reason,tape_distance_m,box_height_m\nP1-path-test,FAIL,display absent,3.01,0.049\n')
        row = self.row(run.name)
        self.assertEqual(row['metrics']['no_pose_fraction'], .5)
        self.assertEqual(row['physical']['tape_distance_m'], '3.01')
        self.assertIn('display absent', row['status'])

    def test_malformed_run_does_not_hide_other_runs(self):
        run = self.run_dir('M1-lab-map')
        (run / 'capture_summary.json').write_text('{bad json')
        (run / 'stereo-quality.json').write_text('{"streams":{}}')
        self.run_dir('A1-approach')
        self.assertTrue(self.row(run.name)['status'].startswith('FAIL:'))
        self.assertEqual(self.row('A1-approach')['status'], 'INCOMPLETE')

    def test_process_failure_log_is_explicit(self):
        run = self.run_dir('P1-path-test')
        (run / 'session.log').write_text('Timed out waiting for /d435_orb/pose; inspect slam.log')
        row = self.row(run.name)
        self.assertIn('FAIL: session.log: Timed out', row['status'])

    def test_cli_outputs_and_read_only_guard(self):
        out = Path(self.temp.name) / 'results.md'
        js = Path(self.temp.name) / 'results.json'
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            lab.main([str(self.root), '--out', str(out), '--json', str(js)])
        self.assertEqual(out.read_text(), stream.getvalue())
        self.assertEqual(len(json.loads(js.read_text())['runs']), 5)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            lab.main([str(self.root), '--out', str(self.root / 'forbidden.md')])
        self.assertFalse((self.root / 'forbidden.md').exists())

    def test_direct_live_root_and_empty_packets(self):
        run = self.live()
        rows = lab.collect(run)
        self.assertTrue(any(r['run'] == run.name for r in rows))
        (run / 'packets.csv').write_text('seq,advisory\n')
        self.assertTrue(self.row(run.name)['status'].startswith('FAIL:'))


if __name__ == '__main__':
    unittest.main()
