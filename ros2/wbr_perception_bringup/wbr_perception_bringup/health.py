"""Follow ORB JSONL, reuse the VIO converter, then reuse the health sender."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace


def follow(path, poll_s, max_bytes):
    """Handle delayed file creation and partial writes; reject truncation/replacement."""
    while not path.exists():
        time.sleep(poll_s)
    with path.open("rb") as stream:
        identity = path.stat()
        pending = b""
        while True:
            stat = path.stat()
            if (stat.st_dev, stat.st_ino) != (identity.st_dev, identity.st_ino) or stat.st_size < stream.tell():
                raise ValueError("ORB pose file replaced or truncated; new session required")
            part = stream.readline(max_bytes + 1 - len(pending))
            pending += part
            if len(pending) > max_bytes:
                raise ValueError("ORB event exceeds configured maximum size")
            if pending.endswith(b"\n"):
                if pending.strip():
                    yield json.loads(pending)
                pending = b""
            elif not part:
                time.sleep(poll_s)


def convert_event(event, converter):
    """T14 pose events -> T9 snapshot -> existing Converter. Never invent a map."""
    source = event["pose_source_d435i_ns"]
    snapshot = {"source_ns": source, "domain": event["source_clock_domain"],
        "state": event["adapter_tracking_state"], "valid": event["pose_valid"],
        "reset_counter": event["map_reset_counter"],
        "imu_initialized": event["imu_initialized"], "tracked_features": event["tracked_features"],
        "evidence": event.get("evidence", "UNKNOWN")}
    if event.get("source_session") != converter.session:
        raise ValueError("ORB source session changed; restart stack")
    converted = converter.convert(snapshot)
    if converted["tracking_state"] != event["tracking_state"]:
        raise ValueError("ORB sender state inconsistent with collapsed adapter state")
    # Mapping is deliberately absent: receipt time is never a camera clock map.
    converted["degraded"] |= event.get("degraded") is not False
    converted["integration"]["bringup_mapping_policy"] = "UNKNOWN camera-to-current-Pi mapping; age unavailable"
    return converted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--device", required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.repo_root))
    from tools.perception_health.integration.vio_to_pose_events import Converter
    from tools.perception_health.py import sender
    config = json.loads((args.run_dir / "config.json").read_text())
    if args.device == "none":
        class FrameFile:
            def __init__(self, path, baud):
                self.stream = (args.run_dir / "health_frames.bin").open("xb")

            def write(self, frame):
                self.stream.write(frame)
                self.stream.flush()

            def close(self):
                self.stream.close()
        sender.Port = FrameFile
    converter = Converter(args.session)
    original_stdin = sys.stdin
    try:
        with (args.run_dir / "health_events.jsonl").open("x") as saved:
            def lines():
                for event in follow(args.run_dir / "orb/pose_events.jsonl", config["poll_s"]["value"],
                                    config["max_event_bytes"]["value"]):
                    line = json.dumps(convert_event(event, converter)) + "\n"
                    saved.write(line)
                    saved.flush()
                    yield line
            sys.stdin = lines()
            sender.process(SimpleNamespace(device=args.device, baud=config["uart_baud"]["value"],
                input=None, session_id=None, heartbeat_ms=json.loads(
                    (args.repo_root / "tools/perception_health/config.json").read_text())["heartbeat_period_ms"]))
    except KeyboardInterrupt:
        return 0
    finally:
        sys.stdin = original_stdin
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
