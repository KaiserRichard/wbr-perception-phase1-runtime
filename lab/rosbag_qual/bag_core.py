"""Offline rosbag2 SQLite analysis with a small, explicit CDR reader.

The reader only extracts ROS header stamps and frame IDs. Payload semantics are
left to the ROS-side record/replay check; this keeps Mac analysis independent of
ROS packages while preserving the two clock domains required by the gate:
header.stamp and rosbag2 messages.timestamp.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import struct
from typing import Any, Iterable

from qual_common import criterion


class CDR:
    def __init__(self, data: bytes):
        if len(data) < 4 or data[:2] != b"\x00\x01":
            raise ValueError("expected little-endian CDR encapsulation")
        self.data = memoryview(data)
        self.pos = 4

    def align(self, boundary: int) -> None:
        self.pos = (self.pos + boundary - 1) & ~(boundary - 1)

    def unpack(self, fmt: str) -> Any:
        size = struct.calcsize("<" + fmt)
        self.align(min(size, 8))
        if self.pos + size > len(self.data):
            raise ValueError("truncated CDR field")
        value = struct.unpack_from("<" + fmt, self.data, self.pos)
        self.pos += size
        return value[0] if len(value) == 1 else value

    def string(self) -> str:
        length = self.unpack("I")
        if length < 1 or self.pos + length > len(self.data):
            raise ValueError("invalid CDR string")
        raw = bytes(self.data[self.pos:self.pos + length])
        self.pos += length
        if raw[-1:] != b"\0":
            raise ValueError("CDR string is not NUL terminated")
        return raw[:-1].decode("utf-8")


def header(cdr: CDR) -> tuple[int, str]:
    sec = cdr.unpack("i")
    nanosec = cdr.unpack("I")
    return int(sec) * 1_000_000_000 + int(nanosec), cdr.string()


def extract_header(data: bytes, msg_type: str, role: str) -> tuple[int | None, str | None]:
    """Extract a standard ROS header without importing ROS message classes."""
    cdr = CDR(data)
    if msg_type in {"sensor_msgs/msg/Image", "sensor_msgs/msg/CameraInfo",
                    "sensor_msgs/msg/Imu", "realsense2_camera_msgs/msg/IMUInfo"}:
        return header(cdr)
    if msg_type == "tf2_msgs/msg/TFMessage":
        count = cdr.unpack("I")
        if count:
            return header(cdr)
        return None, None
    # Some calibration/context messages are not stamped. They are still counted
    # and type-checked by the SQLite manifest; rate checks are not applicable.
    if role in {"tf_static", "extrinsics", "imu_info"}:
        return None, None
    raise ValueError(f"unsupported header extraction for {msg_type}")


def find_db3(path: Path) -> Path:
    path = path.resolve()
    if path.is_file():
        if path.suffix not in {".db3", ".sqlite3", ".sqlite"}:
            raise ValueError(f"expected a rosbag2 SQLite file: {path}")
        return path
    if not path.is_dir():
        raise FileNotFoundError(path)
    candidates = sorted(path.glob("*.db3")) + sorted(path.glob("*.sqlite3"))
    if len(candidates) != 1:
        raise ValueError(f"expected exactly one SQLite storage file in {path}, found {len(candidates)}")
    return candidates[0]


def storage_files(path: Path) -> list[Path]:
    path = Path(path).resolve()
    if path.is_file():
        return [path]
    if not path.is_dir():
        return []
    return sorted(item for item in path.iterdir() if item.is_file() and
                  (item.suffix in {".db3", ".sqlite3", ".sqlite", ".mcap"} or item.name == "metadata.yaml"))


def bag_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _rate(stamps: list[int]) -> float | None:
    if len(stamps) < 2 or stamps[-1] <= stamps[0]:
        return None
    return (len(stamps) - 1) / ((stamps[-1] - stamps[0]) / 1e9)


def _digest_stamps(stamps: Iterable[int]) -> str:
    digest = hashlib.sha256()
    for stamp in stamps:
        digest.update(struct.pack("<q", int(stamp)))
    return digest.hexdigest()


def _topic_report(spec: dict[str, Any], rows: list[tuple[int, bytes]]) -> dict[str, Any]:
    header_stamps: list[int] = []
    frame_ids: list[str] = []
    parse_errors = 0
    receive_stamps = [int(row[0]) for row in rows]
    for _, payload in rows:
        try:
            stamp, frame_id = extract_header(payload, spec["type"], spec.get("role", ""))
            if stamp is not None:
                header_stamps.append(stamp)
            if frame_id is not None:
                frame_ids.append(frame_id)
        except (ValueError, struct.error, UnicodeError):
            parse_errors += 1
    header_reversals = sum(b < a for a, b in zip(header_stamps, header_stamps[1:]))
    header_repeats = sum(b == a for a, b in zip(header_stamps, header_stamps[1:]))
    receive_reversals = sum(b < a for a, b in zip(receive_stamps, receive_stamps[1:]))
    header_gaps = [b - a for a, b in zip(header_stamps, header_stamps[1:]) if b > a]
    receive_gaps = [b - a for a, b in zip(receive_stamps, receive_stamps[1:]) if b > a]
    nominal = spec.get("nominal_hz")
    factor = spec.get("drop_gap_factor")
    drop_limit = (float(factor) / float(nominal)) if nominal and factor else None
    drops = sum(gap / 1e9 > drop_limit for gap in header_gaps) if drop_limit else None
    receive_drops = sum(gap / 1e9 > drop_limit for gap in receive_gaps) if drop_limit else None
    return {
        "name": spec["name"], "type": spec["type"], "role": spec.get("role"),
        "count": len(rows), "header_count": len(header_stamps),
        "first_header_stamp_ns": header_stamps[0] if header_stamps else None,
        "last_header_stamp_ns": header_stamps[-1] if header_stamps else None,
        "header_rate_hz": _rate(header_stamps),
        "bag_receive_rate_hz": _rate(receive_stamps),
        "header_reversals": header_reversals, "header_repeated_stamps": header_repeats,
        "bag_receive_reversals": receive_reversals,
        "max_header_gap_s": max(header_gaps, default=0) / 1e9,
        "max_bag_receive_gap_s": max(receive_gaps, default=0) / 1e9,
        "drop_gap_limit_s": drop_limit, "header_drop_count": drops,
        "bag_receive_drop_count": receive_drops, "parse_errors": parse_errors,
        "frame_ids": sorted(set(frame_ids)), "header_stamp_sha256": _digest_stamps(header_stamps),
        "_header_stamps": header_stamps,
    }


def read_sqlite(path: Path, config: dict[str, Any]) -> dict[str, Any]:
    db3 = find_db3(path)
    conn = sqlite3.connect(f"file:{db3}?mode=ro", uri=True)
    try:
        topic_rows = conn.execute("SELECT id,name,type,serialization_format FROM topics ORDER BY id").fetchall()
        available = {row[1]: row for row in topic_rows}
        reports: dict[str, dict[str, Any]] = {}
        all_receive: list[int] = []
        metadata_message_count = 0
        for spec in config["topics"]:
            topic = available.get(spec["name"])
            if topic is None:
                reports[spec["name"]] = {"name": spec["name"], "type": spec["type"],
                                           "role": spec.get("role"), "count": 0, "header_count": 0,
                                           "missing": True, "header_rate_hz": None,
                                           "bag_receive_rate_hz": None, "header_stamp_sha256": _digest_stamps(())}
                continue
            if topic[2] != spec["type"]:
                raise ValueError(f"{spec['name']}: type {topic[2]} != configured {spec['type']}")
            rows = conn.execute("SELECT timestamp,data FROM messages WHERE topic_id=? ORDER BY id", (topic[0],)).fetchall()
            metadata_message_count += len(rows)
            all_receive.extend(int(row[0]) for row in rows)
            reports[spec["name"]] = _topic_report(spec, rows)
        all_receive.sort()
        return {"database": str(db3), "storage_format": "sqlite3", "topic_count": len(topic_rows),
                "configured_message_count": metadata_message_count,
                "message_count": int(conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]),
                "first_bag_receive_stamp_ns": all_receive[0] if all_receive else None,
                "last_bag_receive_stamp_ns": all_receive[-1] if all_receive else None,
                "duration_s": ((all_receive[-1] - all_receive[0]) / 1e9 if len(all_receive) > 1 else None),
                "bag_bytes": bag_bytes(path if path.is_dir() else db3), "topics": reports,
                "available_topics": [{"name": row[1], "type": row[2], "serialization_format": row[3]}
                                     for row in topic_rows]}
    finally:
        conn.close()


def read_rosbag2(path: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Read MCAP or another rosbag2 storage through rosbag2_py when present."""
    try:
        import rosbag2_py
    except ImportError as error:
        raise RuntimeError("no SQLite storage and rosbag2_py is unavailable for non-SQLite bags") from error
    uri = Path(path).resolve()
    storage_id = config.get("storage", {}).get("storage_id", "mcap")
    reader = rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=str(uri), storage_id=storage_id),
                rosbag2_py.ConverterOptions(input_serialization_format="cdr", output_serialization_format="cdr"))
    available = {item.name: item.type for item in reader.get_all_topics_and_types()}
    rows_by_name: dict[str, list[tuple[int, bytes]]] = {spec["name"]: [] for spec in config["topics"]}
    total = 0
    while reader.has_next():
        name, payload, receive_ns = reader.read_next()
        total += 1
        if name in rows_by_name:
            rows_by_name[name].append((int(receive_ns), bytes(payload)))
    reports = {}
    all_receive: list[int] = []
    for spec in config["topics"]:
        if spec["name"] not in available:
            reports[spec["name"]] = {"name": spec["name"], "type": spec["type"],
                                       "role": spec.get("role"), "count": 0, "header_count": 0,
                                       "missing": True, "header_rate_hz": None,
                                       "bag_receive_rate_hz": None, "header_stamp_sha256": _digest_stamps(())}
            continue
        if available[spec["name"]] != spec["type"]:
            raise ValueError(f"{spec['name']}: type {available[spec['name']]} != configured {spec['type']}")
        reports[spec["name"]] = _topic_report(spec, rows_by_name[spec["name"]])
        all_receive.extend(row[0] for row in rows_by_name[spec["name"]])
    all_receive.sort()
    return {"database": str(uri), "storage_format": storage_id, "topic_count": len(available),
            "configured_message_count": sum(len(value) for value in rows_by_name.values()),
            "message_count": total, "first_bag_receive_stamp_ns": all_receive[0] if all_receive else None,
            "last_bag_receive_stamp_ns": all_receive[-1] if all_receive else None,
            "duration_s": ((all_receive[-1] - all_receive[0]) / 1e9 if len(all_receive) > 1 else None),
            "bag_bytes": bag_bytes(uri), "topics": reports,
            "available_topics": [{"name": name, "type": msg_type} for name, msg_type in sorted(available.items())]}


def _topic_criteria(report: dict[str, Any], spec: dict[str, Any], evidence: str) -> list[dict[str, Any]]:
    source = spec.get("threshold_source", "UNKNOWN: no threshold source provided")
    required = spec.get("required", True)
    if report.get("missing"):
        return [criterion(f"topic:{spec['name']}:present", "Configured topic is present in the bag",
                          0, "messages", ">= 1", "FAIL" if required else "PASS", evidence, source)]
    criteria = [criterion(f"topic:{spec['name']}:count", "Configured topic message count",
                          report["count"], "messages", ">= 1" if required else "not empty when published",
                          "PASS" if report["count"] or not required else "FAIL", evidence, source)]
    if "rate_min_hz" in spec:
        rate = report.get("header_rate_hz")
        status = "BLOCKED" if rate is None else ("PASS" if spec["rate_min_hz"] <= rate <= spec["rate_max_hz"] else "FAIL")
        criteria.append(criterion(f"topic:{spec['name']}:header_rate", "Rate from ROS header.stamp",
                                  rate, "Hz", f"{spec['rate_min_hz']}..{spec['rate_max_hz']}", status, evidence, source))
        drops = report.get("header_drop_count")
        drop_status = "BLOCKED" if drops is None else ("PASS" if drops == 0 else "FAIL")
        criteria.append(criterion(f"topic:{spec['name']}:drops", "Header-stamp gaps above k times nominal period",
                                  drops, "gaps", "0", drop_status, evidence, source))
        max_gap = report.get("max_header_gap_s")
        gap_status = "BLOCKED" if max_gap is None else ("PASS" if max_gap <= spec["max_gap_s"] else "FAIL")
        criteria.append(criterion(f"topic:{spec['name']}:max_gap", "Maximum positive header-stamp gap",
                                  max_gap, "s", f"<= {spec['max_gap_s']}", gap_status, evidence, source))
        reverse_status = "PASS" if report.get("header_reversals", 0) == 0 else "FAIL"
        criteria.append(criterion(f"topic:{spec['name']}:stamp_order", "Header stamps do not reverse",
                                  report.get("header_reversals"), "reversals", "0", reverse_status, evidence, source))
        receive_status = "PASS" if report.get("bag_receive_reversals", 0) == 0 else "FAIL"
        criteria.append(criterion(f"topic:{spec['name']}:bag_receive_order", "Bag receive timestamps do not reverse",
                                  report.get("bag_receive_reversals"), "reversals", "0", receive_status, evidence, source))
    if report.get("parse_errors"):
        criteria.append(criterion(f"topic:{spec['name']}:cdr", "CDR headers decode without errors",
                                  report["parse_errors"], "errors", "0", "FAIL", evidence, source))
    return criteria


def evaluate_report(report: dict[str, Any], config: dict[str, Any], evidence: str = "analysis.json") -> list[dict[str, Any]]:
    criteria: list[dict[str, Any]] = []
    topics = report.get("topics", {})
    for spec in config["topics"]:
        criteria.extend(_topic_criteria(topics.get(spec["name"], {"missing": True}), spec, evidence))

    pairing = config.get("pairing", {})
    left = next((topics.get(s["name"]) for s in config["topics"] if s.get("role") == pairing.get("left_role")), None)
    right = next((topics.get(s["name"]) for s in config["topics"] if s.get("role") == pairing.get("right_role")), None)
    if left and right and not left.get("missing") and not right.get("missing"):
        # Counts are used as a conservative fallback because only the digest is
        # retained in an analysis artifact. The live reader also records exact
        # pairing counts below when the stamp lists are available.
        pairing_counts = report.get("pairing", {})
        matched = pairing_counts.get("matched")
        denominator = pairing_counts.get("denominator", max(left.get("count", 0), right.get("count", 0)))
        fraction = (matched / denominator) if matched is not None and denominator else None
        status = "BLOCKED" if fraction is None else ("PASS" if fraction >= pairing["min_fraction"] else "FAIL")
        criteria.append(criterion("ir_pairing", "IR left/right exact header-stamp pairing fraction",
                                  fraction, "fraction", f">= {pairing['min_fraction']}", status,
                                  evidence, pairing.get("threshold_source", "UNKNOWN")))

    storage = config.get("storage", {})
    duration = report.get("duration_s")
    write_rate = (report.get("bag_bytes") / duration) if duration and duration > 0 else None
    duration_status = "BLOCKED" if duration is None else ("PASS" if duration >= storage.get("min_duration_s", 0) else "FAIL")
    criteria.append(criterion("disk:duration", "Bag has a positive measurable receive-time duration",
                              duration, "s", f">= {storage.get('min_duration_s', 0)}", duration_status,
                              evidence, storage.get("threshold_source", "UNKNOWN")))
    write_status = "BLOCKED" if write_rate is None else ("PASS" if write_rate <= storage["max_write_rate_bps"] else "FAIL")
    criteria.append(criterion("disk:write_rate", "Bag bytes divided by bag receive-time duration",
                              write_rate, "bytes/s", f"<= {storage['max_write_rate_bps']}", write_status,
                              evidence, storage.get("threshold_source", "UNKNOWN")))
    return criteria


def analyze_database(path: Path, config: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = Path(path)
    sqlite_available = False
    if path.is_file():
        sqlite_available = path.suffix in {".db3", ".sqlite3", ".sqlite"}
    elif path.is_dir():
        sqlite_available = len(list(path.glob("*.db3")) + list(path.glob("*.sqlite3"))) == 1
    report = read_sqlite(path, config) if sqlite_available else read_rosbag2(path, config)
    # Pairing is computed from the DB here and reduced to counts in the saved artifact.
    left_spec = next((s for s in config["topics"] if s.get("role") == config.get("pairing", {}).get("left_role")), None)
    right_spec = next((s for s in config["topics"] if s.get("role") == config.get("pairing", {}).get("right_role")), None)
    if left_spec and right_spec:
        left_stamps = report.get("topics", {}).get(left_spec["name"], {}).get("_header_stamps", [])
        right_stamps = report.get("topics", {}).get(right_spec["name"], {}).get("_header_stamps", [])
        if left_stamps or right_stamps:
            common = Counter(left_stamps) & Counter(right_stamps)
            matched = sum(common.values())
            report["pairing"] = {"left_count": len(left_stamps), "right_count": len(right_stamps),
                                  "matched": matched, "denominator": max(len(left_stamps), len(right_stamps)),
                                  "unmatched_left": len(left_stamps) - matched, "unmatched_right": len(right_stamps) - matched}
    for topic in report.get("topics", {}).values():
        topic.pop("_header_stamps", None)
    report["criteria"] = evaluate_report(report, config)
    return report, report["criteria"]

