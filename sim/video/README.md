# Offscreen LQR illustrations

From the repository root, `python -m sim.video` renders the existing
`sim.view.Demo`. It reuses the assumed six-state planar MuJoCo plant,
delay-aware LQR, 500 Hz feedback, torque lag, seeded body IMU noise and
initial leg/body angles. It does not load policies or training outputs.

Every frame carries **ASSUMED planar WBR**, **delay-aware LQR**,
**Illustrative simulation; unscored**, and the ideal rolling/rigid leg/hardware
limitation. These clips are report/slide illustrations, not acceptance results.
The black wheel graphic does not spin. The report camera uses a closer side
view centered on the vehicle above the caption and follows its horizontal
position. This changes presentation only; the live viewer is unchanged.

The default `push` clip starts with balance recovery, then applies the existing
6 N body-COM pulse during [3.00, 3.15) s. `--scenario balance` suppresses that
pulse only in its own demo instance. No source config, plant or controller is
edited. A PNG always captures the initial state at t=0, without rollout.

## Tiny framing preview (actual B3 follow-up command)

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  nice -n 10 /private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python \
  -m sim.video --output /private/tmp/wbr-overnight-20261020/B3/preview-framed.png \
  --width 320 --height 240
```

That output and the earlier `preview-01.png` are retained; choose a new filename
to run again. The follow-up rendered **one additional real frame**, at t=0,
320x240, without rollout. Visual inspection shows the whole vehicle about
104 pixels tall within the 128-pixel scene, above the unchanged captions.
Full clips remain pending. The tests below use mocked GPU rendering and a
mocked encoder; they write real temporary PNGs/JSON and check scheduling,
caption output, overwrite/path guards and failure retention.

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  /private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python \
  -m unittest discover -s sim/video/tests -v
```

## Queued full clips (not run while PPO is active)

The active backend already provides MuJoCo, NumPy, SciPy and Pillow. **FFmpeg
with libx264 is also required for MP4; it is absent on this Mac.** No package
was installed and the backend environment was not changed. Full simulation,
rendering and actual MP4 encoding remain pending for after training or a
separate Pi render host with the dependencies available.

After training, from this checkout, with FFmpeg available:

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  nice -n 10 /private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python \
  -m sim.video --output /private/tmp/wbr-overnight-20261020/B3/lqr-push-10s.mp4 \
  --scenario push --duration 10 --fps 30 --width 640 --height 480 --delay-ms 5 --seed 1000

env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  nice -n 10 /private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python \
  -m sim.video --output /private/tmp/wbr-overnight-20261020/B3/lqr-balance-10s.mp4 \
  --scenario balance --duration 10 --fps 30 --width 640 --height 480 --delay-ms 5 --seed 1000
```

On a Pi, use its own MuJoCo-capable Python instead of the Mac backend path,
and a new output path such as `/tmp/wbr-video-B3/lqr-push-10s.mp4`. The headless
Linux GL backend is selected **before** Python starts, e.g. `MUJOCO_GL=egl` on
a host with functioning EGL support. Pi offscreen GL and encoding have not
been tried. Normal Python sufficed for the actual macOS offscreen frame; this
CLI does not open the passive viewer or require its `mjpython` launcher.

## Output contract

- Output must be a new `.png` or `.mp4` outside this repository, after resolving
  symlinks. Existing media, metadata and encoder logs are refused; FFmpeg also
  gets `-n`. Parent directories are created. Videos stay outside git.
- `<output>.json` records status, seed, delay/runtime settings, initial/pulse
  protocol, gain, versions, source hashes and actual frame tick/time mapping.
  Failed runs retain their artifacts and record the error rather than success.
  An interrupted process can leave `status: running`; this is incomplete.
- MP4 streams one RGB frame at a time to FFmpeg, using one libx264 thread,
  yuv420p and faststart. Errors go to `<output>.ffmpeg.log`. Actual encoding
  and playback compatibility still need the queued full run.
- Presentation frame `i` samples controller tick `round(i/(fps*0.002))`.
  Control/integration rates remain unchanged. At 30 fps this introduces at
  most 1 ms sampling error. A 10 s video has 300 frames, from t=0 through
  t=9.966 s, and plays for 10 s; it does not integrate the final unsampled tail.
  Nonintegral `duration*fps` rounds frame count upward. Metadata distinguishes
  requested duration, playback duration and last simulated timestamp.
- Identical code/settings/seed reproduce the simulation schedule. Cross-host
  numerical, font, GL and encoder differences can change pixels or MP4 bytes;
  no bitwise cross-platform reproducibility is claimed.

No hardware control or RL performance claim is made by this renderer.
