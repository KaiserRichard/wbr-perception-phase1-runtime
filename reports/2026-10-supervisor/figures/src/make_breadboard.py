#!/usr/bin/env python3
"""Render figures/breadboard-wiring.{png,pdf,svg} from bench_wiring.yaml (strict check)."""
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
TOOL = HERE.parents[3] / "tools/wiring_diagram/wiring_diagram.py"
raise SystemExit(subprocess.call([sys.executable, str(TOOL), str(HERE / "bench_wiring.yaml"),
                                  "--output-dir", str(HERE.parent), "--strict"]))
