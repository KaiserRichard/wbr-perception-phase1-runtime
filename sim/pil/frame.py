"""PIL wire frames: COBS(header || payload || CRC-32C) || 00, little endian.

CRC-32C and COBS are the existing link codec (tools/link_proto/py), reused
unchanged. Layout and rationale: docs/pil/DESIGN.md.
"""

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import struct

_SPEC = importlib.util.spec_from_file_location(
    "link_proto", Path(__file__).resolve().parents[2] / "tools/link_proto/py/link_proto.py")
link_proto = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(link_proto)
crc32c, cobs_encode, cobs_decode = link_proto.crc32c, link_proto.cobs_encode, link_proto.cobs_decode

VERSION = 1
STATE, TORQUE = 0x10, 0x11
FLAG_RESET = 0x01
STATUS = {0: "OK", 1: "LQR_INVALID", 2: "NOT_READY", 3: "BAD_DELAY"}

_STATE = struct.Struct("<BBIBB6d")         # 56 B + CRC = 60 B decoded
_TORQUE = struct.Struct("<BBIBB2d2dII")    # 48 B + CRC = 52 B decoded
STATE_RAW, TORQUE_RAW = _STATE.size + 4, _TORQUE.size + 4


def _seal(body):
    return cobs_encode(body + struct.pack("<I", crc32c(body))) + b"\0"


def _open(raw, size):
    if len(raw) != size or struct.unpack_from("<I", raw, size - 4)[0] != crc32c(raw[:size - 4]):
        raise ValueError("bad length or CRC")
    return raw[:size - 4]


def pack_state(seq, delay_ms, measurement, reset=False):
    """Host -> MCU: six measurements (SI, float64) for one 2 ms tick."""
    return _seal(_STATE.pack(VERSION, STATE, seq & 0xFFFFFFFF, FLAG_RESET if reset else 0,
                             delay_ms, *map(float, measurement)))


def unpack_state(raw):
    version, kind, seq, flags, delay_ms, *y = _STATE.unpack(_open(raw, STATE_RAW))
    if version != VERSION or kind != STATE or flags & ~FLAG_RESET:
        raise ValueError("not a PIL state frame")
    return seq, delay_ms, y, bool(flags & FLAG_RESET)


@dataclass(frozen=True)
class Reply:
    seq: int
    status: int
    requested: tuple
    clipped: tuple
    exec_ticks: int   # MCU counter ticks spent in wbr_lqr_step only
    tick_hz: int      # counter rate: core clock on the Nucleo, 1e9 on the fake MCU

    @property
    def exec_s(self):
        return self.exec_ticks / self.tick_hz if self.tick_hz else float("nan")


def pack_torque(reply):
    return _seal(_TORQUE.pack(VERSION, TORQUE, reply.seq, reply.status, 0, *reply.requested,
                              *reply.clipped, reply.exec_ticks, reply.tick_hz))


def unpack_torque(raw):
    version, kind, seq, status, reserved, r0, r1, c0, c1, ticks, hz = _TORQUE.unpack(_open(raw, TORQUE_RAW))
    if version != VERSION or kind != TORQUE or reserved:
        raise ValueError("not a PIL torque frame")
    return Reply(seq, status, (r0, r1), (c0, c1), ticks, hz)


class Deframer:
    """Split a byte stream on 0x00 and COBS-decode; bad frames are counted."""

    def __init__(self, cap=64):
        self.buffer, self.cap, self.errors = bytearray(), cap, 0

    def feed(self, data):
        frames = []
        for byte in data:
            if byte:
                self.buffer.append(byte)
                continue
            if self.buffer:
                try:
                    if len(self.buffer) > self.cap:
                        raise ValueError("oversize")
                    frames.append(cobs_decode(bytes(self.buffer)))
                except ValueError:
                    self.errors += 1
            self.buffer.clear()
        return frames


def wire_bits(n_bytes, bits_per_byte=10):
    """8N1 UART: start + 8 data + stop."""
    return n_bytes * bits_per_byte


STATE_WIRE = len(pack_state(0, 2, [0.0] * 6))                # worst case is the same: COBS adds 1 B for <254 B
TORQUE_WIRE = len(pack_torque(Reply(0, 0, (0., 0.), (0., 0.), 0, 0)))
