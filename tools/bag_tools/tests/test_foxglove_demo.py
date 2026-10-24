"""Small rosbag2-to-MCAP integration test for the offline demo converter."""
from pathlib import Path
import sys

import numpy as np
from mcap.reader import make_reader
from rosbags.rosbag2 import Writer as RosbagWriter
from rosbags.typesys import Stores, get_typestore

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.bag_tools.foxglove_demo import convert


def _stamp(header):
    return (header.stamp.sec, header.stamp.nanosec, header.frame_id)


def test_tiny_rosbag_gets_stamped_overlay(tmp_path):
    ts = get_typestore(Stores.ROS2_JAZZY)
    t = ts.types
    bag = tmp_path / 'tiny'
    writer = RosbagWriter(bag, version=9)
    writer.open()
    conns = {}
    for topic, kind in (
        ('/camera/camera/color/image_raw', 'sensor_msgs/msg/Image'),
        ('/camera/camera/aligned_depth_to_color/image_raw', 'sensor_msgs/msg/Image'),
        ('/camera/camera/color/camera_info', 'sensor_msgs/msg/CameraInfo'),
        ('/camera/camera/aligned_depth_to_color/camera_info', 'sensor_msgs/msg/CameraInfo'),
        ('/tf_static', 'tf2_msgs/msg/TFMessage'),
    ):
        conns[topic] = writer.add_connection(topic, kind, typestore=ts)

    time_msg = t['builtin_interfaces/msg/Time'](1, 234)
    hdr = t['std_msgs/msg/Header'](time_msg, 'camera_color_optical_frame')
    cam_hdr = t['std_msgs/msg/Header'](time_msg, 'camera_color_optical_frame')
    camera_info = t['sensor_msgs/msg/CameraInfo'](
        cam_hdr, 4, 4, 'plumb_bob', np.zeros(5, dtype=np.float64),
        np.array([100., 0., 1.5, 0., 100., 1.5, 0., 0., 1.]),
        np.eye(3).reshape(-1), np.zeros(12), 0, 0,
        t['sensor_msgs/msg/RegionOfInterest'](0, 0, 0, 0, False),
    )
    color = t['sensor_msgs/msg/Image'](hdr, 4, 4, 'rgb8', 0, 12,
                                       np.zeros(48, dtype=np.uint8))
    depth_bytes = np.full((4, 4), 1000, dtype='<u2').view(np.uint8).reshape(-1)
    depth = t['sensor_msgs/msg/Image'](hdr, 4, 4, '16UC1', 0, 8, depth_bytes)
    now = 1_000_000_000
    writer.write(conns['/camera/camera/color/camera_info'], now, ts.serialize_cdr(camera_info, 'sensor_msgs/msg/CameraInfo'))
    writer.write(conns['/camera/camera/aligned_depth_to_color/camera_info'], now, ts.serialize_cdr(camera_info, 'sensor_msgs/msg/CameraInfo'))
    writer.write(conns['/camera/camera/color/image_raw'], now + 1, ts.serialize_cdr(color, 'sensor_msgs/msg/Image'))
    writer.write(conns['/camera/camera/aligned_depth_to_color/image_raw'], now + 2, ts.serialize_cdr(depth, 'sensor_msgs/msg/Image'))
    tf = t['tf2_msgs/msg/TFMessage']([])
    writer.write(conns['/tf_static'], now + 3, ts.serialize_cdr(tf, 'tf2_msgs/msg/TFMessage'))
    writer.close()

    output = tmp_path / 'tiny.mcap'
    result = convert(bag, output)
    assert result['message_counts']['/wbr_obstacle_node/advisory'] == 1
    assert result['message_counts']['/wbr_obstacle_node/markers'] == 1
    assert result['message_counts']['/wbr_obstacle_node/obstacle_points'] == 1
    assert output.stat().st_size > 0

    observed = {}
    with output.open('rb') as stream:
        for schema, channel, message in make_reader(stream).iter_messages():
            if channel.topic in ('/wbr_obstacle_node/markers', '/wbr_obstacle_node/obstacle_points'):
                decoded = ts.deserialize_cdr(message.data, schema.name)
                if channel.topic.endswith('/markers'):
                    observed['markers'] = _stamp(decoded.markers[0].header)
                else:
                    observed['points'] = _stamp(decoded.header)
            elif channel.topic == '/wbr_obstacle_node/advisory':
                observed['advisory'] = ts.deserialize_cdr(message.data, schema.name).data
    assert observed['markers'] == (1, 234, 'camera_color_optical_frame')
    assert observed['points'] == observed['markers']
    assert 'plane_valid' in observed['advisory']
