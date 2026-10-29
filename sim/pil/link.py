"""Host side of the PIL link: a serial port (Nucleo or fake MCU pty).

Lockstep: one state frame out, wait for its torque reply, then step MuJoCo.
The simulation owns the clock; wall-clock round-trip time is measured only.
"""

from pathlib import Path
import shutil
import subprocess
import time

import serial

from sim.pil import frame

ROOT = Path(__file__).resolve().parents[2]
C_DIR = Path(__file__).resolve().parent / "c"
BUILD = Path(__file__).resolve().parent / ".build"


class LinkError(RuntimeError):
    """Timeout, malformed reply, sequence mismatch or non-OK MCU status."""


class SerialMcu:
    def __init__(self, port, baud=460800, timeout_s=0.5):
        self.port = serial.Serial(port, baudrate=baud, timeout=0.05, write_timeout=timeout_s)
        self.timeout_s = timeout_s
        self.deframer = frame.Deframer()
        self.seq = 0
        self.port.reset_input_buffer()

    def step(self, measurement, delay_ms, reset=False):
        """Returns (Reply, round_trip_s). Raises LinkError; never invents torque."""
        self.seq = (self.seq + 1) & 0xFFFFFFFF
        start = time.perf_counter()
        self.port.write(frame.pack_state(self.seq, delay_ms, measurement, reset))
        while time.perf_counter() - start < self.timeout_s:
            chunk = self.port.read(max(1, self.port.in_waiting))
            for raw in self.deframer.feed(chunk):
                try:
                    reply = frame.unpack_torque(raw)
                except ValueError as exc:
                    raise LinkError(f"malformed reply: {exc}") from exc
                if reply.seq != self.seq:
                    raise LinkError(f"sequence {reply.seq} != {self.seq}")
                if reply.status != 0:
                    raise LinkError(f"MCU status {frame.STATUS.get(reply.status, reply.status)}")
                return reply, time.perf_counter() - start
        raise LinkError(f"no reply to seq {self.seq} within {self.timeout_s} s")

    def close(self):
        self.port.close()


def build_fake_mcu(cc=None):
    """Compile pil_core + wbr_lqr + link_proto codec for the host; returns the path."""
    cc = cc or shutil.which("cc")
    BUILD.mkdir(exist_ok=True)
    out = BUILD / "fake_mcu"
    sources = [C_DIR / "fake_mcu.c", C_DIR / "pil_core.c", ROOT / "sim/control_c/wbr_lqr.c",
               ROOT / "tools/link_proto/link_proto.c"]
    # Same numerical flags as the control_c parity build: no contraction, no fast math.
    cmd = [cc, "-std=c99", "-O2", "-Wall", "-Wextra", "-Werror", "-ffp-contract=off",
           f"-I{C_DIR}", f"-I{ROOT / 'sim/control_c'}", f"-I{ROOT / 'tools/link_proto'}",
           *map(str, sources), "-lm", "-o", str(out)]
    newest = max(p.stat().st_mtime for p in sources + [C_DIR / "pil_core.h"])
    if not out.exists() or out.stat().st_mtime < newest:
        subprocess.run(cmd, check=True)
    return out


class FakeMcu:
    """Starts fake_mcu behind a pty; `.path` is the serial device to open.

    A pty has no baud rate, and macOS rejects its custom-speed ioctl for
    460800, so open it with `baud=FakeMcu.BAUD` (a standard, ignored value).
    """

    BAUD = 115200

    def __init__(self, binary=None):
        self.process = subprocess.Popen([str(binary or build_fake_mcu())], stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True)
        self.path = self.process.stdout.readline().strip()
        if not self.path:
            self.close()
            raise LinkError("fake MCU did not report a pty")

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=5)
        self.process.stdout.close()
        self.process.stderr.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class QemuMcu(FakeMcu):
    """The cross-compiled firmware (`make build/pil_emu.elf`) on QEMU netduinoplus2.

    USART2 is QEMU's second serial device, exposed as a pty. This checks the
    ARM binary's arithmetic (soft double, newlib libm); QEMU timing is not real.
    """

    ELF = Path(__file__).resolve().parent / "firmware/build/pil_emu.elf"

    def __init__(self, elf=None, qemu=None):
        qemu = qemu or shutil.which("qemu-system-arm")
        if not qemu:
            raise LinkError("qemu-system-arm not found")
        self.process = subprocess.Popen(
            [qemu, "-M", "netduinoplus2", "-display", "none", "-monitor", "none",
             "-serial", "null", "-serial", "pty", "-kernel", str(elf or self.ELF)],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.path = ""
        for line in self.process.stdout:  # "char device redirected to /dev/ttysNNN (label serial1)"
            if "redirected to" in line:
                self.path = line.split("redirected to", 1)[1].split()[0]
                break
        if not self.path:
            self.close()
            raise LinkError("QEMU did not report a pty")

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=5)
        self.process.stdout.close()
