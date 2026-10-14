# Pi ↔ STM32 link bench test (Nucleo-F446RE stand-in)

**OPEN / diagnostic.** Bench tooling around the CANDIDATE codec in
[`../link_proto`](../link_proto/README.md). The Nucleo-F446RE stands in for the
STM32H7 for the link and message format only: no balancing, LQR/VMC, FSM,
actuator or motor code exists here. Results are diagnostic numbers, not a gate PASS.

## What it measures

| Phase | What happens | What it shows |
|---|---|---|
| preflight | Pi listens 1 s, sends nothing | MCU→Pi direction alone (20 Hz `McuStatus` heartbeat, state `NO_LINK`) |
| rtt | Pi sends `PerceptionHealth` at 50 Hz for 60 s; MCU replies with `McuStatus` right after each packet | round-trip P50/P95/P99/max, round-trip loss, wire errors per direction |
| faults | corrupted CRC, duplicate sequence, wrong session (10 each) | MCU rejects with `WIRE` / `SEQUENCE` / `SESSION` and recovers on the next valid packet |
| timeout | Pi goes silent for 100 ms (5×) and 300 ms (5×) | 100 ms: link held. 300 ms: MCU declares `NO_LINK` at its 150 ms silence rule, and the link recovers when packets resume |

Clock domains are never mixed. Round trip = Pi `CLOCK_MONOTONIC` at reply decode
minus Pi `CLOCK_MONOTONIC` before `write()`. MCU silence = `action_mcu_ns` of the
`NO_LINK` status minus `sample_mcu_ns` of the reply to the last packet, both from
the MCU's TIM2 clock. "Pi detect" is Pi time from the last send to the `NO_LINK`
status arriving.

The health packets are deliberately **ineligible** (`flags = 0`, tracking
`STARTING`, no clock mapping): there is no Pi→MCU clock mapping yet, so the test
exercises link liveness, CRC/sequence/session checks and the silence rule, not
estimate freshness or references. Linked state therefore reads
`RESET_PENDING_REENABLE` (no local enable is ever issued), and `NO_LINK` during silence.

Test-only provisioning: the firmware binds at boot to the fixed session
`WBRLINK1` with mapping/transform revision `0xF446`, and the Pi script uses the
same values. That stands in for the SPEC's trusted local bind; it is not a
handshake design. The Pi starts its sequence at its monotonic milliseconds, so
reruns within one Pi boot keep increasing. If the MCU still rejects with
`SEQUENCE` (for example after a Pi reboot), press the Nucleo's black RESET button.

## Firmware

Bare-metal C99, register level, no HAL/CMSIS download: needs only
`arm-none-eabi-gcc`. It compiles `../link_proto/link_proto.c` unchanged.

* USART1 PA9 TX / PA10 RX (Arduino D8 / D2) at 460800 8N1: Pi GPIO path.
* USART2 PA2/PA3 at 460800 8N1: ST-Link virtual COM port over the Nucleo USB (fallback path).
  Both ports run the same logic independently.
* LD2 (green user LED, PA5) is on while either port holds a link, off in `NO_LINK`.
* 84 MHz from the ST-Link 8 MHz MCO (HSE bypass), HSI fallback; baud error +0.16 %.
* TIM2 free-running at 1 MHz is the MCU monotonic clock. The silence/staleness rule
  runs every main-loop pass; status replies are sent from the main loop, never from the ISR.
* `McuStatus.session` is the MCU boot ID (chip UID + boot counter in RTC backup register 0),
  so an MCU reset shows up on the Pi as `mcu_reboots_seen`.

Prebuilt binary: [`firmware/prebuilt/link_bench_f446.bin`](firmware/prebuilt/)
(SHA-256 in `SHA256SUMS`, built with Arm GNU Toolchain 13.2.rel1 from this tree).
Rebuild with `make -C tools/link_bench/firmware`.

Flash (pick one):

```sh
cp tools/link_bench/firmware/prebuilt/link_bench_f446.bin /Volumes/NOD_F446RE/   # ST-Link USB drive
st-flash --reset write tools/link_bench/firmware/prebuilt/link_bench_f446.bin 0x08000000   # brew install stlink
```

## Wiring (both sides 3.3 V logic)

| Pi 5 header | Nucleo-F446RE |
|---|---|
| pin 8, GPIO14 TXD | PA10 USART1_RX (CN9 D2) |
| pin 10, GPIO15 RXD | PA9 USART1_TX (CN5 D8) |
| pin 6, GND | any GND |

Power and flash the Nucleo from the Mac over its USB. Do not connect any Nucleo
5V/3V3 pin to the Pi.

## Pi side

Standard library only. Copy `pi/link_bench.py` and `../link_proto/py/link_proto.py`
into one directory on the Pi, then:

```sh
python3 link_bench.py --port /dev/ttyAMA0 --out ~/link-bench-$(date -u +%Y%m%dT%H%M%SZ)
python3 link_bench.py --port /dev/ttyAMA0 --out OUT --loopback   # no Nucleo: jumper pin 8 to pin 10
python3 link_bench.py --port /dev/ttyACM0 --out OUT              # fallback: Nucleo USB into the Pi (USART2 via ST-Link)
```

On a Pi 5, GPIO14/15 appear as `/dev/ttyAMA0` only when UART0 is enabled in
`/boot/firmware/config.txt` (`dtparam=uart0=on`, then a reboot; INFERRED from
Raspberry Pi firmware conventions, verify with `ls -l /dev/ttyAMA0`). The user needs
the `dialout` group or `sudo`.

Writes `summary.json`, `rtt.csv`, `faults.csv`, `timeout.csv`.

## Expected numbers (CALCULATED / INFERRED, not measured on hardware)

* Serialization floor of one round trip: (102 + 66) bytes × 10 bits / 460800 baud ≈ 3.65 ms.
  RTT P50 should sit a little above that on the GPIO path. Python wake-up and
  scheduling on a loaded Pi add the tail, so P99 is the number to watch.
* USB fallback adds ST-Link bridge and USB polling delay; its RTT is not
  representative of the GPIO UART link.
* Loss and wire errors: 0 expected on a short bench cable.
* 300 ms gap: MCU silence about 150–151 ms; Pi detect about 150 ms plus one status
  record time. 100 ms gap: no `NO_LINK`.

## Verification done here

`make -C tools/link_bench test` (MEASURED, host only):

* Python decoder reads the frozen C `McuStatus` vector from `../link_proto/tests/vectors.txt`;
  every single-byte corruption of a bench health packet is rejected.
* Host simulator (`host/sim.c`, the firmware's `bench.c` behind a pseudo-terminal, real clock):
  all four phases, zero loss, 3/3 of each fault kind rejected with the expected reason,
  100 ms gap held, 300 ms gap tripped with MCU silence in [150, 200) ms.
* The actual firmware sources (with `-DBENCH_EMU`, which only skips RCC/UID) on QEMU
  `netduinoplus2` (STM32F405, same USART1/TIM2 addresses): vector table, USART
  interrupts, ring buffers and codec work end to end. QEMU does not model the F446
  clock tree, so its timing is ignored.

UNKNOWN until the bench run: real UART timing and error rate, the Pi's UART0
state, Pi-side scheduling tail, F446 clock start-up (HSE MCO vs HSI fallback) on this board.
