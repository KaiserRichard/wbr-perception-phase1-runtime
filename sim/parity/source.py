"""Read and verify pinned source data without implementing the gain equation."""
from __future__ import annotations

import json
from pathlib import Path
import re

from .build_reference import VENDOR, extract_coefficients, sha256

FIXTURES = Path(__file__).parent / "fixtures" / "shared_vectors.json"


def verify_vendor() -> dict:
    manifest = json.loads((VENDOR / "PROVENANCE.json").read_text())
    for name, expected in manifest["files"].items():
        if sha256(VENDOR / name) != expected:
            raise ValueError(f"Pinned source checksum mismatch: {name}")
    return manifest


def load_coefficients() -> tuple[tuple[float, ...], ...]:
    """Load 12 rows in upstream order, each ordered [a3, a2, a1, a0]."""
    verify_vendor()
    initializer = extract_coefficients((VENDOR / "User/APP/chassisR_task.c").read_text())
    rows = re.findall(r"\{([^{}]+)\}", initializer)
    return tuple(tuple(float(value.strip().removesuffix("f"))
                       for value in row.split(",")) for row in rows)


def load_vectors() -> dict:
    return json.loads(FIXTURES.read_text(), parse_constant=_reject_nonfinite)


def _reject_nonfinite(value: str):
    raise ValueError(f"Non-standard JSON numeric token: {value}")
