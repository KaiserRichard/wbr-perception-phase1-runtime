"""Hardware-free long-lived child used only by unittest."""
import json
import os
from pathlib import Path
import signal
import sys
import time

run, role = Path(sys.argv[1]), sys.argv[2]
config = json.loads((run / "config.json").read_text())
behavior = json.loads((run.parent / "behavior.json").read_text())
poll = config["poll_s"]["value"]
signal.signal(signal.SIGINT, signal.SIG_IGN if behavior.get("ignore_int") == role else lambda *_: sys.exit(0))
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
(run / f"{role}.started").write_text(str(os.getpid()))
if role == "readiness":
    (run / "armed.json").write_text("{}")
if role in ("camera", "bag"):
    (run / "sensor.started").touch()
if role == "profile":
    target = int(sys.argv[3])
    os.kill(target, 0)
    (run / "profile_target_pid.txt").write_text(str(target))
while True:
    if (role == "readiness" and (run / "sensor.started").exists() and not behavior.get("no_ready")
            and not (run / "ready.json").exists()):
        pending = run / "ready.tmp"
        pending.write_text(json.dumps({"first_messages": dict.fromkeys(config["topics"], {})}))
        pending.replace(run / "ready.json")
    if behavior.get("exit") == role and (run / "release").exists():
        sys.exit(behavior.get("exit_code", 7))
    time.sleep(poll)
