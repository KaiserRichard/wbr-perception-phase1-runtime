"""Create a Foxglove MCAP with offline WBR obstacle-detector overlays.

Usage: foxglove_demo.py BAG_DIR OUT.mcap
The bag must be a rosbag2 SQLite directory containing RealSense color and
aligned-depth topics. RealSense Metadata connections are deliberately skipped.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import numpy as np
from mcap.writer import Writer
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ros2.wbr_obstacle_node.wbr_obstacle_node.core import AdvisoryCore, CoreParams, depth_to_metres

COLOR = '/camera/camera/color/image_raw'
DEPTH = '/camera/camera/aligned_depth_to_color/image_raw'
COLOR_INFO = '/camera/camera/color/camera_info'
DEPTH_INFO = '/camera/camera/aligned_depth_to_color/camera_info'
TF_STATIC = '/tf_static'
OUT_TOPICS = {
    'markers': '/wbr_obstacle_node/markers',
    'advisory': '/wbr_obstacle_node/advisory',
    'points': '/wbr_obstacle_node/obstacle_points',
}


def _image_array(msg):
    """Decode packed ROS depth image respecting step, endianness, and padding."""
    encoding = msg.encoding.upper()
    dtype = np.dtype(('>' if msg.is_bigendian else '<') + ('u2' if encoding == '16UC1' else 'f4'))
    if encoding not in ('16UC1', '32FC1'):
        raise ValueError(f'unsupported aligned depth encoding: {msg.encoding}')
    itemsize = dtype.itemsize
    row = np.frombuffer(msg.data, dtype=dtype, count=(msg.step // itemsize) * msg.height)
    return row.reshape(msg.height, msg.step // itemsize)[:, :msg.width]


def _create_messages(ts):
    t = ts.types
    return {
        'Header': t['std_msgs/msg/Header'], 'Point': t['geometry_msgs/msg/Point'],
        'Quaternion': t['geometry_msgs/msg/Quaternion'], 'Pose': t['geometry_msgs/msg/Pose'],
        'Vector3': t['geometry_msgs/msg/Vector3'], 'Duration': t['builtin_interfaces/msg/Duration'],
        'Color': t['std_msgs/msg/ColorRGBA'], 'Marker': t['visualization_msgs/msg/Marker'],
        'MarkerArray': t['visualization_msgs/msg/MarkerArray'], 'String': t['std_msgs/msg/String'],
        'PointField': t['sensor_msgs/msg/PointField'], 'PointCloud2': t['sensor_msgs/msg/PointCloud2'],
        'CompressedImage': t['sensor_msgs/msg/CompressedImage'], 'MeshFile': t['visualization_msgs/msg/MeshFile'],
    }


def _marker_array(specs, header, m):
    enums = {'CUBE': 1, 'LINE_LIST': 5, 'TRIANGLE_LIST': 11, 'TEXT_VIEW_FACING': 9}
    markers = []
    for spec in specs:
        xyz = spec.get('position', spec.get('center', [0.0, 0.0, 0.0]))
        scale = spec['scale']
        color = m['Color'](*map(float, spec['color']))
        pose = m['Pose'](m['Point'](*map(float, xyz)), m['Quaternion'](0.0, 0.0, 0.0, 1.0))
        points = [m['Point'](*map(float, p)) for p in spec.get('points', [])]
        markers.append(m['Marker'](
            header, spec['ns'], int(spec['id']), enums[spec['type']], 0, pose,
            m['Vector3'](*map(float, scale)), color, m['Duration'](0, 0), False,
            points, [], '', m['CompressedImage'](header, '', np.empty(0, dtype=np.uint8)),
            [], spec.get('text', ''), '', m['MeshFile']('', np.empty(0, dtype=np.uint8)), False,
        ))
    return m['MarkerArray'](markers)


def _pointcloud(points, header, m):
    fields = [m['PointField'](name, offset, 7, 1) for name, offset in (('x', 0), ('y', 4), ('z', 8))]
    data = np.asarray(points, dtype='<f4').reshape(-1, 3).tobytes()
    return m['PointCloud2'](header, 1, len(points), fields, False, 12, len(points) * 12,
                            np.frombuffer(data, dtype=np.uint8).copy(), True)


def convert(bag_dir: str | Path, output: str | Path):
    bag_dir, output = Path(bag_dir), Path(output)
    if not bag_dir.is_dir() or not (bag_dir / 'metadata.yaml').is_file():
        raise ValueError(f'expected a rosbag2 directory with metadata.yaml: {bag_dir}')
    output.parent.mkdir(parents=True, exist_ok=True)
    ts = get_typestore(Stores.ROS2_JAZZY)
    m = _create_messages(ts)
    core = AdvisoryCore(str(REPO_ROOT), CoreParams())
    with Reader(bag_dir) as reader, output.open('wb') as stream:
        writer = Writer(stream)
        writer.start(profile='ros2')
        channels, schemas = {}, {}

        def register(topic, msgtype):
            if msgtype not in schemas:
                definition, _ = ts.generate_msgdef(msgtype, ros_version=2)
                schemas[msgtype] = writer.register_schema(msgtype, 'ros2msg', definition.encode())
            channels[topic] = writer.register_channel(topic, 'cdr', schemas[msgtype])

        conns = {c.topic: c for c in reader.connections}
        required = (COLOR, DEPTH, COLOR_INFO, DEPTH_INFO, TF_STATIC)
        missing = [topic for topic in required if topic not in conns]
        if missing:
            raise ValueError(f'missing required topics: {missing}')
        for topic in required:
            conn = conns[topic]
            if conn.msgtype not in ts.types:
                raise ValueError(f'unsupported type for required topic {topic}: {conn.msgtype}')
            register(topic, conn.msgtype)
        register(OUT_TOPICS['markers'], 'visualization_msgs/msg/MarkerArray')
        register(OUT_TOPICS['advisory'], 'std_msgs/msg/String')
        register(OUT_TOPICS['points'], 'sensor_msgs/msg/PointCloud2')
        selected = [c for c in reader.connections if c.topic in required]
        # Camera calibration is static in these recordings. Seed it before the
        # time-ordered pass because some bags begin recording images before the
        # first CameraInfo sample.
        latest_k = None
        for info_conn, _, info_raw in reader.messages(connections=[conns[COLOR_INFO]]):
            info = ts.deserialize_cdr(info_raw, info_conn.msgtype)
            candidate = np.asarray(info.k, dtype=np.float64).reshape(3, 3)
            if np.isfinite(candidate).all() and candidate[0, 0] > 0 and candidate[1, 1] > 0:
                latest_k = candidate
                break
        if latest_k is None:
            raise ValueError(f'no valid CameraInfo on {COLOR_INFO}')
        counts, histogram = Counter(), Counter()

        for conn, log_time, raw in reader.messages(connections=selected):
            log_time = int(log_time)
            msg = ts.deserialize_cdr(raw, conn.msgtype)
            writer.add_message(channels[conn.topic], log_time, raw, publish_time=log_time)
            counts[conn.topic] += 1
            if conn.topic == COLOR_INFO:
                k = np.asarray(msg.k, dtype=np.float64).reshape(3, 3)
                if np.isfinite(k).all() and k[0, 0] > 0 and k[1, 1] > 0:
                    latest_k = k
            elif conn.topic == DEPTH:
                if latest_k is None:
                    raise ValueError('aligned depth arrived before valid color CameraInfo')
                arr = _image_array(msg)
                depth_m = depth_to_metres(arr, msg.encoding)
                stamp = int(msg.header.stamp.sec) * 1_000_000_000 + int(msg.header.stamp.nanosec)
                out = core.process(depth_m, latest_k, frame_stamp_ns=stamp, frame_id=msg.header.frame_id)
                header = msg.header
                marker_array = _marker_array(out['markers'], header, m)
                advisory = {key: out['advisory'][key] for key in (
                    'advisory', 'height_m', 'distance_m', 'width_m', 'confidence', 'plane_valid')}
                generated = (
                    (OUT_TOPICS['markers'], 'visualization_msgs/msg/MarkerArray', marker_array),
                    (OUT_TOPICS['advisory'], 'std_msgs/msg/String', m['String'](json.dumps(advisory, separators=(',', ':'), allow_nan=False))),
                    (OUT_TOPICS['points'], 'sensor_msgs/msg/PointCloud2', _pointcloud(out['points'], header, m)),
                )
                for topic, msgtype, output_msg in generated:
                    writer.add_message(channels[topic], log_time,
                                       ts.serialize_cdr(output_msg, msgtype), publish_time=log_time)
                    counts[topic] += 1
                histogram[advisory['advisory']] += 1
        writer.finish()
    return {'output': str(output), 'message_counts': dict(sorted(counts.items())),
            'advisory_histogram': dict(sorted(histogram.items())), 'size_bytes': output.stat().st_size}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bag_dir')
    parser.add_argument('output_mcap')
    args = parser.parse_args(argv)
    print(json.dumps(convert(args.bag_dir, args.output_mcap), indent=2))


if __name__ == '__main__':
    main()
