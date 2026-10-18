"""R_T26 regression checks; only R26-01 is a known external-tool failure."""
import csv
import json
import math
import os
from pathlib import Path
import sqlite3
import struct
import subprocess
import tempfile
import unittest

from test_rehearsal import (CDRWriter, CFG, HERE, ROOT, TOPICS, cdr_image,
                            cdr_imu, invoke, val, write_fake_accuracy_inputs,
                            write_qual_config)


class ReviewTests(unittest.TestCase):
    def test_standard_cdr_imu_fields_and_alignment(self):
        # Independent ROS Imu field offsets for frame_id='camera_imu':
        # encapsulation=4, Header=23, relative padding=1, quaternion=32,
        # orientation covariance=72, gyro=24, gyro covariance=72, accel=24.
        for gyro in (False, True):
            with self.subTest(gyro=gyro):
                raw = cdr_imu(val('device_header_start_ns'), gyro)
                self.assertEqual(len(raw), 324)
                self.assertEqual(struct.unpack_from('<dddd', raw, 28), (0, 0, 0, 1))
                self.assertEqual(struct.unpack_from('<ddd', raw, 132),
                                 (0.01, 0.02, 0.03) if gyro else (0, 0, 0))
                self.assertEqual(struct.unpack_from('<ddd', raw, 228),
                                 (0, 0, 0) if gyro else (0, 0, 9.81))

    @unittest.expectedFailure
    def test_standard_cdr_export_R26_01(self):
        """R26-01: exporter aligns doubles to encapsulation, not CDR body."""
        with tempfile.TemporaryDirectory() as td:
            bag = Path(td) / 'standard.db3'
            start = val('device_header_start_ns')
            with sqlite3.connect(bag) as db:
                db.executescript('CREATE TABLE topics(id INTEGER PRIMARY KEY,name TEXT,type TEXT,serialization_format TEXT);'
                                 'CREATE TABLE messages(id INTEGER PRIMARY KEY,topic_id INTEGER,timestamp INTEGER,data BLOB);')
                for ident, (key, (name, typ)) in enumerate(TOPICS.items(), 1):
                    db.execute('INSERT INTO topics VALUES(?,?,?,?)', (ident, name, typ, 'cdr'))
                    payload = cdr_image(start, key) if key.startswith('ir') else cdr_imu(start, key == 'gyro')
                    db.execute('INSERT INTO messages VALUES(?,?,?,?)', (ident, ident, start, payload))
            proc = invoke(['tools/n4b_offline/db3_to_euroc.py', bag, Path(td) / 'export'])
            print(f'R26-01 standard CDR exporter: exit={proc.returncode}; {proc.stdout.strip()}')
            self.assertEqual(proc.returncode, 0, proc.stdout)
            metadata = json.loads((Path(td) / 'export/metadata.json').read_text())
            self.assertEqual(metadata['stereo_pairs'], 1)

    def test_accuracy_fixture_has_exact_known_ate_and_quaternions(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            sequence, export, run = (work / p for p in ('sequence', 'export', 'run'))
            for directory in (sequence, export, run):
                directory.mkdir()
            stamps = [val('device_header_start_ns') + round(i * 1e9 / val('image_rate_hz'))
                      for i in range(val('ground_truth_samples'))]
            (export / 'times_ns.txt').write_text(''.join(f'{t}\n' for t in stamps))
            gt, trajectory = write_fake_accuracy_inputs(sequence, export, run)
            truth = list(csv.reader(gt.read_text().splitlines()))
            estimate = [line.split() for line in trajectory.read_text().splitlines()]
            errors = [[float(e[j+1]) - float(g[j+1]) for j in range(3)] for g, e in zip(truth, estimate)]
            for g, e in zip(truth, estimate):
                self.assertEqual(list(map(float, g[4:8])), [1, 0, 0, 0])  # EuRoC wxyz
                self.assertEqual(list(map(float, e[4:8])), [0, 0, 0, 1])  # TUM xyzw
            expected = val('image_noise_amplitude_m') * math.sqrt(1.5)
            self.assertLess(abs(math.sqrt(sum(x*x for row in errors for x in row) / len(errors)) - expected),
                            val('ate_tolerance_m'))
            # Centered noise has no translation or rotation component for SE3 to absorb.
            for axis in range(3):
                self.assertLess(abs(sum(e[axis] for e in errors)), val('ate_tolerance_m'))
                for coord in range(3):
                    self.assertLess(abs(sum(float(g[coord+1]) * e[axis] for g, e in zip(truth, errors))),
                                    val('ate_tolerance_m'))

    def test_make_uses_bash_and_propagates_failed_python(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            (work / 'Makefile').write_bytes((HERE / 'Makefile').read_bytes())
            fake_python = work / 'python3'
            fake_python.write_text('#!/bin/bash\nset -euo pipefail\ntouch invoked\nexit 1\n')
            fake_python.chmod(0o755)
            subprocess.run(['bash', '-n', str(fake_python)], check=True)
            env = dict(os.environ, PATH=str(work) + os.pathsep + os.environ['PATH'])
            proc = subprocess.run(['make', 'test'], cwd=work, env=env, capture_output=True, text=True)
            self.assertTrue((work / 'invoked').is_file(), proc.stdout + proc.stderr)
            self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_synthetic_thresholds_come_from_config(self):
        # Verify generated CLI thresholds carry the centralized configuration.
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'qual.json'
            write_qual_config(path)
            config = json.loads(path.read_text())
            self.assertEqual(config['storage']['max_write_rate_bps'], val('synthetic_storage_ceiling_bps'))
            self.assertEqual(config['storage']['min_duration_s'], val('duration_s') * val('synthetic_min_duration_fraction'))
            self.assertEqual(val('ground_truth_samples'), round(val('duration_s') * val('image_rate_hz')))
            for name, item in CFG.items():
                if isinstance(item, dict) and 'value' in item:
                    self.assertTrue(item.get('source'), name)

    def test_real_saved_header_excerpt_through_cli_and_analyze_only(self):
        # Reuse exact saved evidence, not a new claim about live recorder clocks.
        fixture = json.loads((ROOT / 'tools/stamp_drift/tests/fixtures/real_ros_headers.json').read_text())
        self.assertEqual(fixture['evidence_label'], 'MEASURED')
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            bag = work / 'real-header-excerpt.db3'
            with sqlite3.connect(bag) as db:
                db.executescript('CREATE TABLE topics(id INTEGER PRIMARY KEY,name TEXT,type TEXT,serialization_format TEXT);'
                                 'CREATE TABLE messages(id INTEGER PRIMARY KEY,topic_id INTEGER,timestamp INTEGER,data BLOB);')
                for ident, topic in enumerate(fixture['topics'], 1):
                    db.execute('INSERT INTO topics VALUES(?,?,?,?)', (ident, topic['name'], topic['type'], 'cdr'))
                    for row in topic['rows']:
                        writer = CDRWriter(); writer.header(row['ros_header_stamp_ns'], row['frame_id'])
                        self.assertEqual(bytes(writer.data).hex(), row['cdr_header_hex'])
                        db.execute('INSERT INTO messages(topic_id,timestamp,data) VALUES(?,?,?)',
                                   (ident, row['bag_receive_stamp_ns'], bytes.fromhex(row['cdr_header_hex'])))
            out = work / 'drift'
            proc = invoke(['tools/stamp_drift/analyze.py', bag, '--output-dir', out])
            self.assertEqual(proc.returncode, 0, proc.stdout)
            report = json.loads((out / 'report.json').read_text())
            self.assertEqual(report['input']['row_count'], sum(len(t['rows']) for t in fixture['topics']))
            for stream in report['streams']:
                self.assertLess(abs(stream['drift_ppm']), val('drift_tolerance_ppm'))
            replay = invoke(['tools/stamp_drift/analyze.py', '--analyze-only', out])
            self.assertEqual(replay.returncode, 0, replay.stdout)
            self.assertEqual(json.loads((out / 'result.json').read_text())['status'], 'PASS')


if __name__ == '__main__':
    unittest.main()
