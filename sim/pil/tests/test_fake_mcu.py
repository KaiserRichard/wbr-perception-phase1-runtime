"""Fake MCU over a real pty: same C code as the firmware, compiled for the host.

Replays the archived control_c fixtures through the serial link, so the
whole chain (frame -> COBS/CRC -> pil_core -> wbr_lqr -> reply) is checked.
"""

import json
import math
from pathlib import Path
import shutil
import time
import unittest

from sim.pil import frame
from sim.pil.link import FakeMcu, LinkError, QemuMcu, SerialMcu

FIXTURE = Path(__file__).resolve().parents[2] / "control_c/fixtures/recorded.json"
TOLERANCE = 1e-6  # same absolute tolerance as sim/control_c/tests


def replay_fixtures(mcu):
    """Worst absolute error over the 4 x 64 archived ticks, controller state kept on the MCU."""
    worst = 0.0
    for profile in json.loads(FIXTURE.read_text())["profiles"]:
        records = [r for r in profile["archive_case"]["records"] if r["op"] == "S"]
        assert len(records) == 64
        for i, record in enumerate(records):
            reply, _ = mcu.step(record["input"], profile["delay_ms"], reset=i == 0)
            for got, want in ((reply.requested, record["requested"]), (reply.clipped, record["clipped"])):
                worst = max(worst, *(abs(g - w) for g, w in zip(got, want)))
    return worst


class FakeMcuLink(unittest.TestCase):
    def setUp(self):
        self.fake = FakeMcu()
        self.mcu = SerialMcu(self.fake.path, baud=FakeMcu.BAUD, timeout_s=0.5)

    def tearDown(self):
        self.mcu.close()
        self.fake.close()

    def raw_exchange(self, data, wait_s=0.2):
        self.mcu.port.write(data)
        deadline, frames = time.monotonic() + wait_s, []
        while time.monotonic() < deadline:
            frames += self.mcu.deframer.feed(self.mcu.port.read(max(1, self.mcu.port.in_waiting)))
        return [frame.unpack_torque(f) for f in frames]

    def test_archived_fixtures_over_link(self):
        self.assertLess(replay_fixtures(self.mcu), TOLERANCE)

    def test_needs_reset_first(self):
        with self.assertRaisesRegex(LinkError, "NOT_READY"):
            self.mcu.step([0.0] * 6, 5)

    def test_bad_and_changed_delay(self):
        with self.assertRaisesRegex(LinkError, "BAD_DELAY"):
            self.mcu.step([0.0] * 6, 6, reset=True)
        self.mcu.step([0.0] * 6, 4, reset=True)
        with self.assertRaisesRegex(LinkError, "BAD_DELAY"):
            self.mcu.step([0.0] * 6, 3)

    def test_nonfinite_measurement(self):
        self.mcu.step([0.0] * 6, 2, reset=True)
        with self.assertRaisesRegex(LinkError, "LQR_INVALID"):
            self.mcu.step([0.0, math.nan, 0.0, 0.0, 0.0, 0.0], 2)

    def test_resync_after_garbage_and_no_reply_to_corrupt_frame(self):
        good = frame.pack_state(41, 2, [0.0, 0.1, -0.1, 0.0, 0.0, 0.0], reset=True)
        corrupt = bytearray(good)
        corrupt[5] ^= 0x40
        replies = self.raw_exchange(b"\x01\x02\x03\x00" + bytes(200) + bytes(corrupt) + good)
        self.assertEqual([r.seq for r in replies], [41])

    def test_reports_exec_time(self):
        reply, rtt = self.mcu.step([0.0, 0.1, -0.1, 0.0, 0.0, 0.0], 5, reset=True)
        self.assertEqual(reply.tick_hz, 1_000_000_000)
        self.assertGreater(rtt, reply.exec_s)


@unittest.skipUnless(shutil.which("qemu-system-arm") and QemuMcu.ELF.exists(),
                     "needs qemu-system-arm and `make -C sim/pil/firmware build/pil_emu.elf`")
class QemuFirmwareLink(unittest.TestCase):
    """The ARM firmware binary itself, emulated: same fixtures, same tolerance."""

    def test_archived_fixtures_on_cross_compiled_binary(self):
        with QemuMcu() as qemu:
            mcu = SerialMcu(qemu.path, baud=QemuMcu.BAUD, timeout_s=2.0)
            try:
                self.assertLess(replay_fixtures(mcu), TOLERANCE)
            finally:
                mcu.close()


if __name__ == "__main__":
    unittest.main()
