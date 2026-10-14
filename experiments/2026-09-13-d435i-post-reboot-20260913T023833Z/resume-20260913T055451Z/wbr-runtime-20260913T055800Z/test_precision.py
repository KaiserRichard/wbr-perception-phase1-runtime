"""Synthetic rejection/precision tests; no device or physical PASS."""
import json
from pathlib import Path
import tempfile
import unittest
from analyze_precision import analyze


class PrecisionAnalysisTests(unittest.TestCase):
    def fixture(self):
        result = []
        for name, rate in [('Infrared 1', 15), ('Gyro', 200), ('Accel', 100)]:
            for i in range(rate * 2):
                row = {'stream': name, 'frame_number': i+1, 'sdk_timestamp_ms': 1789267180000.123 + 1000*i/rate,
                       'timestamp_domain': 'Global Time', 'host_steady_ns': 10**12+round(1e9*i/rate),
                       'host_utc_ns': 1789267180000123000+round(1e9*i/rate), 'metadata': {'Frame Timestamp': i}}
                if name != 'Infrared 1': row['xyz'] = [0.0001234567890123, -0.00045678901234, 9.806650161743164]
                result.append(row)
        return result

    def evaluate(self, rows):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'SYNTHETIC.jsonl'
            p.write_text(''.join(json.dumps(r)+'\n' for r in rows))
            return analyze(p)

    def test_precision_and_domains(self):
        result = self.evaluate(self.fixture())
        self.assertTrue(result['automatic_timing_pass'])
        self.assertAlmostEqual(result['streams']['Gyro']['xyz_mean'][0], .0001234567890123, places=16)
        self.assertEqual(result['streams']['Gyro']['domains'], {'Global Time': 400})

    def test_repeated_timestamp_rejected(self):
        rows = self.fixture(); rows[1]['sdk_timestamp_ms'] = rows[0]['sdk_timestamp_ms']
        self.assertFalse(self.evaluate(rows)['automatic_timing_pass'])

    def test_missing_ir_rejected(self):
        rows = self.fixture(); del rows[2]
        self.assertFalse(self.evaluate(rows)['automatic_timing_pass'])

    def test_arrival_gap_rejected(self):
        rows = self.fixture(); rows[32]['host_steady_ns'] += 100000000
        self.assertFalse(self.evaluate(rows)['automatic_timing_pass'])

    def test_absent_stream_rejected(self):
        self.assertFalse(self.evaluate([r for r in self.fixture() if r['stream'] != 'Accel'])['automatic_timing_pass'])


if __name__ == '__main__': unittest.main()
