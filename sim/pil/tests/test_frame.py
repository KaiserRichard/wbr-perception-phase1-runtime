"""Wire-format checks; standard library plus the reused link codec only."""

import struct
import unittest

from sim.pil import frame


class Frames(unittest.TestCase):
    def test_reused_crc32c_check_value(self):
        self.assertEqual(frame.crc32c(b"123456789"), 0xE3069283)

    def test_sizes(self):
        # 60/52 decoded bytes; COBS adds one byte below 254; plus the 00 delimiter.
        self.assertEqual((frame.STATE_RAW, frame.TORQUE_RAW), (60, 52))
        self.assertEqual((frame.STATE_WIRE, frame.TORQUE_WIRE), (62, 54))
        worst = frame.pack_state(0xFFFFFFFF, 5, [1e300, -1e-300, 0.0, -0.0, 1.5, 2.5], reset=True)
        self.assertEqual(len(worst), 62)

    def test_state_round_trip_is_bit_exact(self):
        y = [0.0, 0.13962634015954636, -0.10220003906558552, 1e-17, -3.25, 0.008050894723742355]
        wire = frame.pack_state(7, 3, y, reset=True)
        self.assertEqual(wire.count(0), 1)
        self.assertEqual(wire[-1], 0)
        (raw,) = frame.Deframer().feed(wire)
        self.assertEqual(frame.unpack_state(raw), (7, 3, y, True))

    def test_torque_round_trip(self):
        reply = frame.Reply(9, 0, (2.24, -5.0), (2.0, -4.0), 12345, 84_000_000)
        (raw,) = frame.Deframer().feed(frame.pack_torque(reply))
        self.assertEqual(frame.unpack_torque(raw), reply)
        self.assertAlmostEqual(reply.exec_s, 12345 / 84e6)

    def test_corruption_rejected(self):
        raw = bytearray(frame.cobs_decode(frame.pack_state(1, 2, [0.0] * 6)[:-1]))
        raw[10] ^= 0x01
        with self.assertRaises(ValueError):
            frame.unpack_state(bytes(raw))
        with self.assertRaises(ValueError):
            frame.unpack_torque(bytes(raw))  # wrong length/type

    def test_deframer_split_garbage_and_oversize(self):
        good = frame.pack_state(1, 2, [0.5] * 6)
        stream = b"\x07\x01\x00" + bytes([1] * 100) + b"\x00" + good + good
        d, frames = frame.Deframer(), []
        for i in range(len(stream)):  # one byte at a time
            frames += d.feed(stream[i:i + 1])
        self.assertEqual(len([f for f in frames if len(f) == frame.STATE_RAW]), 2)
        self.assertGreaterEqual(d.errors, 1)

    def test_bandwidth_arithmetic(self):
        # CALCULATED in docs/pil/DESIGN.md: 8N1 at 460800 baud.
        bit = 1 / 460800
        self.assertAlmostEqual(frame.wire_bits(62) * bit * 1e3, 1.3455, places=4)
        self.assertAlmostEqual(frame.wire_bits(54) * bit * 1e3, 1.1719, places=4)
        self.assertEqual(struct.calcsize("<6d"), 48)


if __name__ == "__main__":
    unittest.main()
