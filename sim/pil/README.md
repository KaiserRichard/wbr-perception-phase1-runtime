# PIL (processor-in-the-loop) bench, rungs 3 and 4

MuJoCo on the Mac sends the six measurements to an MCU each 2 ms tick; the
MCU runs the unchanged `sim/control_c` LQR and returns torque. Lockstep: the
simulation waits for each reply. Design: [docs/pil/DESIGN.md](../../docs/pil/DESIGN.md);
lesson: [docs/pil/LESSON.md](../../docs/pil/LESSON.md).

## Host setup (Python 3.12, from the repository root)

```sh
python3.12 -m venv .venv
.venv/bin/pip install -r sim/requirements.lock gymnasium==0.29.1 cloudpickle==3.1.2 \
  Farama-Notifications==0.0.6 pyserial
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s sim/pil/tests -t . -v
```

No torch or stable-baselines3 is needed.

## Without hardware: fake MCU

The same C (pil_core + wbr_lqr + link_proto codec) compiled for the Mac,
served behind a pseudo-terminal. Full 160-case panel, both controllers:

```sh
.venv/bin/python -m sim.pil.run --fake --jobs 6 --out /tmp/pil-fake-01
```

## On the bench: Nucleo-F446RE

```sh
make -C sim/pil/firmware
cp sim/pil/firmware/build/pil_f446.bin /Volumes/NOD_F446RE/
ls /dev/cu.usbmodem*
.venv/bin/python -m sim.pil.run --port /dev/cu.usbmodemXXXX --controllers pil \
  --delays 5 --noise-seeds 5 --out /tmp/pil-nucleo-smoke-01
```

Then the full panel with `--controllers python,pil` (one MCU, so `--jobs` is
forced to 1; expect well over an hour). Wiring for rung 3: logic analyser
channel on D7 (PA8), ground on GND. PA8 is HIGH only during `wbr_lqr_step`.
LD2 toggles on every valid frame. Nothing in this firmware drives a motor or CAN.

Outputs: `summary.json` (success counts, Python-vs-PIL differences, round trip
and MCU execution statistics) and `results.json` (one row per episode).
Exit 1 if any episode ended with a link or numerical error.

`--link-delay-ticks N` applies each command N ticks late (unmodelled latency).
