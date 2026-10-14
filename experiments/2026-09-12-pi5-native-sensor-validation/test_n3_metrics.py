"""Synthetic unit fixtures validate tooling only; never hardware PASS evidence."""
import copy
import unittest
from types import SimpleNamespace as NS

from n3_metrics import TopicStats, compare_replay, evaluate, read_topics


def image(stamp_ns, width=640):
    return NS(header=NS(stamp=NS(sec=stamp_ns // 1_000_000_000, nanosec=stamp_ns % 1_000_000_000),
                        frame_id="camera_infra1_optical_frame"),
              width=width, height=480, encoding="mono8", step=640, data=b"\x00" * (640 * 480), is_bigendian=0)


class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.spec = read_topics()[0]

    def state(self, stamps):
        result = TopicStats(self.spec)
        for index, stamp in enumerate(stamps):
            result.add(image(stamp), b"synthetic" + str(stamp).encode(), index / 15)
        return result

    def test_nanosecond_precision_repeats_and_backward(self):
        result = self.state([1_800_000_000_000_000_000, 1_800_000_000_000_000_001,
                             1_800_000_000_000_000_001, 1_800_000_000_000_000_000]).report(0, 1)
        self.assertEqual(result["repeated_stamps"], 1)
        self.assertEqual(result["backward_stamps"], 1)
        self.assertEqual(result["nonpositive_stamp_steps"], 2)

    def test_whole_window_rate_does_not_hide_stall(self):
        result = self.state([1_000_000_000 + i * 66_666_667 for i in range(15)]).report(0, 10)
        self.assertAlmostEqual(result["stamp_span_hz"], 15, places=5)
        self.assertEqual(result["whole_window_hz"], 1.5)
        failures = evaluate({self.spec["name"]: result}, [self.spec], live=True)
        self.assertTrue(any("whole-window" in failure for failure in failures))

    def test_wrong_image_dimensions_rejected(self):
        state = TopicStats(self.spec)
        state.add(image(1_000_000_000, 320), b"synthetic", 0)
        self.assertEqual(state.report(0, 1)["invalid_messages"], 1)

    def test_header_digest_catches_changed_order(self):
        first = self.state([1_000_000_000, 1_100_000_000]).report(0, 1)
        other = self.state([1_100_000_000, 1_000_000_000]).report(0, 1)
        self.assertNotEqual(first["header_sha256"], other["header_sha256"])

    def test_payload_digest_catches_corruption(self):
        state = self.state([1_000_000_000])
        other = TopicStats(self.spec)
        corrupted = image(1_000_000_000)
        corrupted.data = b'\x01' + corrupted.data[1:]
        other.add(corrupted, b"corrupt synthetic", 0)
        self.assertNotEqual(state.report(0, 1)["payload_sha256"], other.report(0, 1)["payload_sha256"])

    def test_wire_padding_is_preserved_but_not_semantic_corruption(self):
        a, b = TopicStats(self.spec), TopicStats(self.spec)
        a.add(image(1_000_000_000), b'synthetic wire padding A', 0)
        b.add(image(1_000_000_000), b'synthetic wire padding B', 0)
        self.assertEqual(a.report(0, 1)['payload_sha256'], b.report(0, 1)['payload_sha256'])
        self.assertNotEqual(a.report(0, 1)['serialized_payload_sha256'], b.report(0, 1)['serialized_payload_sha256'])

    def test_missing_required_context_rejected(self):
        failures = evaluate({}, read_topics())
        self.assertEqual(len(failures), len(read_topics()))

    def test_disconnected_tf_is_not_presence_pass(self):
        result = self.state([1_000_000_000, 1_066_666_667]).report(0, 0.1)
        failures = evaluate({self.spec["name"]: result}, [self.spec])
        self.assertTrue(any("TF static graph" in failure for failure in failures))

    def test_static_zero_stamp_is_permitted(self):
        spec = next(spec for spec in read_topics() if spec["role"] == "imu_info")
        state = TopicStats(spec)
        msg = NS(header=NS(stamp=NS(sec=0, nanosec=0), frame_id="gyro"),
                 data=[1., 0, 0, 0, 0, 1., 0, 0, 0, 0, 1., 0], noise_variances=[0]*3, bias_variances=[0]*3)
        state.add(msg, b"synthetic static info", 0)
        self.assertEqual(evaluate({spec["name"]: state.report(0, 1)}, [spec]), [])

    def test_replay_loss_rejected(self):
        result = self.state([1_000_000_000, 1_066_666_667]).report(0, 0.1)
        stored = {"topics": {self.spec["name"]: result}}
        replay = copy.deepcopy(stored)
        replay["topics"][self.spec["name"]]["count"] -= 1
        self.assertTrue(any("count differs" in item for item in compare_replay(stored, replay, [self.spec])))

    def test_camera_info_nan_rejected(self):
        spec = next(spec for spec in read_topics() if spec["role"] == "camera_info")
        state = TopicStats(spec)
        msg = NS(header=image(1_000_000_000).header, width=640, height=480,
                 k=[float("nan")] * 9, p=[1.] * 12, r=[1.] * 9, d=[], distortion_model="plumb_bob")
        state.add(msg, b"synthetic malformed CameraInfo", 0)
        self.assertEqual(state.invalid, 1)


if __name__ == "__main__":
    unittest.main()
