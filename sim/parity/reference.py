"""Typed, sequential-only bindings to a checksum-verified host C build."""
from __future__ import annotations

import ctypes
import json
import math
from pathlib import Path
import threading

from .build_reference import sha256

_FLOAT = ctypes.c_float
_PTR = ctypes.POINTER(_FLOAT)
_VMC_LOCK = threading.Lock()  # Original C contains static pitch temporaries.
OUTPUTS = ("L0", "phi0", "theta", "dtheta", "j11", "j12", "j21", "j22",
           "tau0", "tau1", "l1", "l5")


def finite_float32(value: float) -> float:
    converted = _FLOAT(float(value)).value
    if not math.isfinite(converted):
        raise ValueError("Input must be finite and representable as float32")
    return converted


class CReference:
    def __init__(self, build_dir: Path):
        build_dir = Path(build_dir).resolve()
        self.metadata = json.loads((build_dir / "build_metadata.json").read_text())
        name = self.metadata["library"]
        if Path(name).name != name:
            raise ValueError("Library must be a filename inside the build directory")
        library = build_dir / name
        if sha256(library) != self.metadata["library_sha256"]:
            raise ValueError("Built library checksum mismatch")
        self.lib = ctypes.CDLL(str(library))
        self.lib.wbr_gain.argtypes = [_PTR, _FLOAT]
        self.lib.wbr_gain.restype = _FLOAT
        self.lib.wbr_schedule.argtypes = [_FLOAT, _PTR]
        self.lib.wbr_schedule.restype = None
        self.lib.wbr_vmc.argtypes = [ctypes.c_int] + [_FLOAT] * 7 + [_PTR]
        self.lib.wbr_vmc.restype = ctypes.c_int

    def scalar_gain(self, coefficients, length_m: float) -> float:
        if len(coefficients) != 4:
            raise ValueError("Expected four cubic coefficients")
        row = (_FLOAT * 4)(*(finite_float32(x) for x in coefficients))
        answer = float(self.lib.wbr_gain(row, finite_float32(length_m)))
        if not math.isfinite(answer):
            raise ValueError("C gain evaluation was nonfinite")
        return answer

    def schedule(self, length_m: float) -> list[float]:
        out = (_FLOAT * 12)()
        self.lib.wbr_schedule(finite_float32(length_m), out)
        result = list(out)
        if not all(map(math.isfinite, result)):
            raise ValueError("C schedule evaluation was nonfinite")
        return result

    def vmc(self, *, side: str, phi1_rad: float, phi4_rad: float,
            pitch_rad: float, pitch_rate_rad_s: float, dt_s: float,
            F0_N: float, Tp_Nm: float) -> dict[str, float]:
        if side not in ("right", "left"):
            raise ValueError("Side must be right or left")
        values = tuple(finite_float32(x) for x in
                       (phi1_rad, phi4_rad, pitch_rad, pitch_rate_rad_s, dt_s, F0_N, Tp_Nm))
        out = (_FLOAT * 12)()
        with _VMC_LOCK:
            status = self.lib.wbr_vmc(0 if side == "right" else 1, *values, out)
        if status:
            raise ValueError(f"Host VMC wrapper rejected input: status={status}")
        return dict(zip(OUTPUTS, out, strict=True))


def vmc_arguments(case: dict) -> dict:
    names = ("side", "phi1_rad", "phi4_rad", "pitch_rad", "pitch_rate_rad_s", "dt_s", "F0_N", "Tp_Nm")
    return {name: case[name] for name in names}
