"""Opt-in Pi ROS integration test using a ~10 MB synthetic bag, never a camera.

WBR_RUN_ROS_SYNTHETIC=1 enables this test after sourcing Jazzy. The temporary
bag is explicitly synthetic and removed on completion; no N1/N2/N3 receipt
is generated. Native replay uses test domains 181/182, not the live domain 42.
"""
import json
import os
import shutil
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest


@unittest.skipUnless(os.environ.get('WBR_RUN_ROS_SYNTHETIC') == '1', 'opt-in camera-free ROS integration')
class SyntheticROSTest(unittest.TestCase):
    def test_finalized_bag_complete_replay_and_no_publisher_boundary(self):
        import rosbag2_py
        import yaml
        from rclpy.serialization import serialize_message
        from sensor_msgs.msg import Image, CameraInfo, Imu
        from tf2_msgs.msg import TFMessage
        from geometry_msgs.msg import TransformStamped
        from n3_metrics import read_topics
        from n3_bag import inspect_bag, replay, assert_quiet
        try:
            from realsense2_camera_msgs.msg import IMUInfo, Extrinsics
            full_context = True
        except ImportError:
            full_context = False

        with tempfile.TemporaryDirectory(prefix='wbr-SYNTHETIC-ros-') as temp:
            root = Path(temp); bag = root / 'SYNTHETIC-bag'
            specs = [s for s in read_topics() if full_context or s['role'] in ('image', 'camera_info', 'gyro', 'accel', 'tf_static')]
            topics_file = root/'synthetic-topics.json'
            topics_file.write_text(json.dumps({'scope': 'SYNTHETIC_SUBSET_NOT_CAMERA_QUALIFICATION', 'topics': specs}))
            qos_file = root/'synthetic-qos.yaml'
            defaults = yaml.safe_load(Path(__file__).with_name('n3_qos.yaml').read_text())
            qos_file.write_text(yaml.safe_dump({s['name']: defaults[s['name']] for s in specs}))
            writer = rosbag2_py.SequentialWriter()
            writer.open(rosbag2_py.StorageOptions(uri=str(bag), storage_id='sqlite3'),
                        rosbag2_py.ConverterOptions('cdr', 'cdr'))
            for spec in specs:
                writer.create_topic(rosbag2_py.TopicMetadata(id=0, name=spec['name'], type=spec['type'], serialization_format='cdr'))
            samples = []
            frames = {'image': 'camera_infra1_optical_frame', 'camera_info': 'camera_infra1_optical_frame',
                      'gyro': 'camera_gyro_optical_frame', 'accel': 'camera_accel_optical_frame'}
            for spec in specs:
                role = spec['role']
                hz = {'image': 15, 'camera_info': 15, 'gyro': 200, 'accel': 100}.get(role, 0)
                if role == 'tf_static':
                    msg = TFMessage()
                    for frame in sorted(set(frames.values())):
                        tf = TransformStamped(); tf.header.frame_id = 'camera_link'; tf.child_frame_id = frame
                        tf.transform.rotation.w = 1.; msg.transforms.append(tf)
                    samples.append((1_000_000_000, spec['name'], serialize_message(msg)))
                    continue
                if role in ('imu_info', 'extrinsics'):
                    if role == 'imu_info':
                        msg = IMUInfo(); msg.header.frame_id = frames['gyro' if '/gyro/' in spec['name'] else 'accel']
                        msg.data = [1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.]
                    else:
                        msg = Extrinsics(); msg.rotation = [1.,0.,0.,0.,1.,0.,0.,0.,1.]
                    samples.append((1_000_000_000, spec['name'], serialize_message(msg)))
                    continue
                for index in range(2 * hz):
                    stamp = 1_000_000_000 + round((index + .5) * 1e9 / hz)
                    if role == 'image':
                        msg = Image(); msg.width = 640; msg.height = 480; msg.step = 640; msg.encoding = 'mono8'
                        msg.data = bytes([index % 256]) * 307200
                    elif role == 'camera_info':
                        msg = CameraInfo(); msg.width = 640; msg.height = 480; msg.distortion_model = 'plumb_bob'
                        msg.k = [400.,0.,320.,0.,400.,240.,0.,0.,1.]
                        msg.p = [400.,0.,320.,0.,0.,400.,240.,0.,0.,0.,1.,0.]
                        msg.r = [1.,0.,0.,0.,1.,0.,0.,0.,1.]
                    else:
                        msg = Imu(); msg.linear_acceleration.z = 9.81
                    msg.header.frame_id = frames[role]
                    msg.header.stamp.sec, msg.header.stamp.nanosec = divmod(stamp, 1_000_000_000)
                    samples.append((stamp, spec['name'], serialize_message(msg)))
            for stamp, topic, payload in sorted(samples, key=lambda row: row[0]):
                writer.write(topic, payload, stamp)
            del writer  # rosbag2 writer finalizes metadata on destruction.
            stored = inspect_bag(bag, specs)
            self.assertEqual(stored['failures'], [])
            result = replay(SimpleNamespace(bag=bag, output_dir=root/'replay', live_domain=181,
                replay_domain=182, topics_file=topics_file, qos_file=qos_file, synthetic_fixture=True), specs)
            if result:
                for p in (root/'replay').glob('*'):
                    if p.suffix in ('.log', '.json') and p.stat().st_size < 60000:
                        print(p.name, p.read_text())
            self.assertEqual(result, 0)
            observed = json.loads((root/'replay/observed.json').read_text())
            for name, expected in stored['topics'].items():
                self.assertEqual(observed['topics'][name]['count'], expected['count'])
                self.assertEqual(observed['topics'][name]['payload_sha256'], expected['payload_sha256'])
                if expected.get('first_camera_info_wire_hex'):
                    before = bytes.fromhex(expected['first_camera_info_wire_hex'])
                    after = bytes.fromhex(observed['topics'][name]['first_camera_info_wire_hex'])
                    print('SYNTHETIC CameraInfo wire byte differences:',
                          [(i, a, b) for i, (a, b) in enumerate(zip(before, after)) if a != b])
            print('SYNTHETIC complete replay counts:', {name: value['count'] for name, value in observed['topics'].items()})
            # A constructed TF publisher is enough to reject the stop-live boundary.
            # This is not a camera node and it accesses no sensor/hardware API.
            import rclpy
            rclpy.init(domain_id=181)
            node = rclpy.create_node('wbr_synthetic_context_only')
            try:
                node.create_publisher(TFMessage, '/tf_static', 10)
                with self.assertRaisesRegex(RuntimeError, 'not demonstrably quiet'):
                    assert_quiet(181, root/'synthetic-contamination.json', topics_file)
            finally:
                node.destroy_node(); rclpy.shutdown()
            # An unfinalized copy cannot be inspected or rescued through reindex.
            (bag/'metadata.yaml').rename(bag/'SYNTHETIC-metadata-held.yaml')
            with self.assertRaisesRegex(ValueError, 'Finalized metadata'):
                inspect_bag(bag, specs)
            if os.environ.get('WBR_SYNTHETIC_EVIDENCE'):
                evidence = Path(os.environ['WBR_SYNTHETIC_EVIDENCE'])
                shutil.copytree(root/'replay', evidence)
                shutil.copy2(root/'synthetic-contamination.json', evidence/'synthetic-contamination.json')
                shutil.copy2(topics_file, evidence/'synthetic-topics.json')
                (evidence/'README.md').write_text(
                    '# SYNTHETIC TOOLING EVIDENCE ONLY\n\n'
                    'Constructed messages, no camera API or hardware execution. '
                    'The temporary ~10 MB fixture bag was removed after testing; '
                    'reproduce with test_ros_offline.py and recorded package/source hashes. '
                    'No N1/N2/N3 physical PASS is established.\n')


if __name__ == '__main__':
    unittest.main()
