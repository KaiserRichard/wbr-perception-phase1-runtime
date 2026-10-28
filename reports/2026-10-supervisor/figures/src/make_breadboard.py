#!/usr/bin/env python3
"""Compatibility entry point for the reusable wiring diagram tool."""
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TOOL = ROOT / "tools/wiring_diagram/wiring_diagram.py"
SPEC = HERE / "bench_wiring.yaml"
OUT = HERE.parent
raise SystemExit(subprocess.call([
    sys.executable, str(TOOL), str(SPEC), "--output-dir", str(OUT),
    "--png-width", "2400",
]))
