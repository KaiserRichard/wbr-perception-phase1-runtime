# Lesson: processor-in-the-loop (PIL), and what it can and cannot prove

## 1. The problem

The LQR (linear-quadratic regulator) balances the simulated robot in 160/160
cases, but that result comes from NumPy on a PC. The robot runs a C port on an
STM32, gets its state over a wire, and its commands arrive late. Three things
can break between "works in Python" and "works on the robot":

1. **Arithmetic on the chip**: different float hardware, compiler flags, `libm`.
2. **Software around the math**: framing, byte order, reset, stored history.
3. **Time**: the controller takes time to run and the link takes time to carry
   bytes. A controller that is correct but late is a different controller.

PIL attacks 1 and 2 directly and measures the ingredients of 3.

## 2. The mechanism

```mermaid
sequenceDiagram
  participant Sim as MuJoCo plant (Mac)
  participant Link as UART 460800 (ST-Link USB)
  participant MCU as Nucleo: wbr_lqr_step
  Note over Sim: tick k: plant time frozen
  Sim->>Link: STATE k (62 B, 1.35 ms on the wire)
  Link->>MCU: bytes -> COBS/CRC check
  Note over MCU: PA8 HIGH, run LQR, PA8 LOW<br/>DWT counts cycles
  MCU->>Link: TORQUE k (54 B, 1.17 ms)
  Link->>Sim: requested + clipped torque, exec cycles
  Note over Sim: apply torque, advance 2 ms, tick k+1
```

In **lockstep**, the plant waits for each answer. The chip computes every
torque, but compute and link time never reach the physics. So a lockstep
PIL run is a very strict **arithmetic and software** test: it should match
the Python run almost exactly, tick by tick.

Latency is studied separately, on purpose: `--link-delay-ticks N` applies
each command N ticks late, so the effect of a slow link can be measured
deterministically, without any chip at all.

## 3. Assumptions

- The plant is the ASSUMED planar model (`sim/README.md`): masses, motor lag,
  sensor noise and the 2–5 ms actuator delay are illustrative, not identified.
- The F446 is a stand-in: Cortex-M4 at 84 MHz with a **single-precision**
  FPU. The robot's H7 has a double-precision FPU and a faster clock.
- The six measurements arrive perfect (bit-exact); on the robot they come from
  a real IMU (inertial measurement unit) and encoders.

## 4. Why PIL cannot prove balance

PIL proves *"this chip computes the same function as the model, on time"*. It
says nothing about whether that function balances the **real** robot,
because the plant on the other side of the wire is still the model. If the
model's mass, inertia, motor lag or sensor noise is wrong, PIL inherits the
error and still passes. Balance on the robot needs the robot (or at least
identified parameters plus hardware-in-the-loop tests with real actuators).

| Question | Answered by |
|---|---|
| Does the C port equal Python? | host parity tests (`sim/control_c`) |
| Does it still equal Python on the chip, through a real link? | **PIL, lockstep** |
| How long does one step take on the chip? | **rung 3: PA8 pulse + DWT** |
| How much extra delay can the controller tolerate? | `--link-delay-ticks` (sim) |
| Does the robot balance? | only the robot |

## 5. Worked example: latency budget for a real-time link

Suppose the bench ran in **real time** (the MCU's timer owns the 500 Hz tick)
over the same 460800 baud ST-Link link. Follow one measurement from the moment
it is taken until its torque is applied:

| Stage | Time | Status |
|---|---:|---|
| STATE frame on the wire: 62 B × 10 bit / 460800 | 1.346 ms | CALCULATED |
| USB full-speed polling, host → ST-Link | ≤ 1.0 ms | INFERRED |
| `wbr_lqr_step` on the F446 at 84 MHz | ~0.2 ms | INFERRED, rung 3 measures it |
| TORQUE frame on the wire: 54 B × 10 bit / 460800 | 1.172 ms | CALCULATED |
| USB polling, ST-Link → host | ≤ 1.0 ms | INFERRED |
| **Total** | **≈ 4.7 ms** | |

Commands only change at tick boundaries (every 2 ms), so 4.7 ms rounds up to
the third boundary: **3 ticks = 6 ms** of extra delay. If the robot's own
actuator path is the 2 ms profile, the controller would really see
$2 + 6 = 8$ ms while its gains and torque estimate assume 2 ms. The extra
6 ms is **unmodelled**: the controller believes its last commands have
already reached the motors when they have not.

How to observe this without real time: run the lockstep panel with
`--link-delay-ticks 3`. MEASURED in the simulation (fake MCU, push, 2 ms profile,
10 seeds): 10/10 still recover, mean recovery after the push 2.7448 s → 2.7516 s,
peak tilt 8.01° → 8.09°. In this ASSUMED model the controller tolerates the
extra 6 ms with little cost. That is a model result, not a robot margin
(`docs/pil/DESIGN.md` §5).

What this example teaches: the link, not the chip, dominates. Removing USB
(direct UART on the robot), using float32 frames, or raising the baud rate
each shrink the budget far more than a faster CPU would.

## 6. How to test on the bench

1. Flash `sim/pil/firmware/build/pil_f446.bin`, connect the Nucleo's USB.
2. Rung 3: logic analyser on D7 (PA8) and GND, run any PIL command, read the
   pulse width; compare with `mcu_exec_s` in the run's `summary.json`.
3. Rung 4: a short panel first (10 episodes), then the full 160.

Commands are in [sim/pil/README.md](../../sim/pil/README.md).

## 7. What evidence would contradict the expectations

- **Torque differs at tick 1 by more than 1e-9 N·m** → chip arithmetic differs
  (check `-mfloat-abi`, `-ffp-contract=off`, newlib `expm1`).
- **Errors grow over time while tick 1 matches** → state handling bug.
- **PA8 pulse ≫ 0.3 ms** → clock not 84 MHz, or caches off.
- **Any PIL outcome differs from Python in lockstep** → stop and debug before
  trusting any later rung; lockstep should be identical.

## 8. Project implication

A PIL pass lets you trust the C controller and the link code when they move to
the H7, and the timing numbers size the real-time budget. Balance remains an
open question for the robot itself in November.
