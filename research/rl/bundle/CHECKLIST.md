# C1-T11 · Chợ Mơ Training Station · USB checklist

Legacy PPO v2 **portability/throughput benchmark**, unchanged assumed plant and
recipe; CPU MuJoCo + CPU PPO. RTX 3060 does not accelerate this physics backend.
Windows x64, Python 3.12; actual Windows version/driver/runtime compatibility is
unverified until tested. No JAX/MJX, WSL, driver installation or admin required.

1. **Before leaving (conductor, networked Mac):** run
   `bash research/rl/bundle/build_bundle.sh /path/to/WBR-C1-T11`.
   Any missing exact Windows wheel is a build failure: keep the error, do not
   relax pins. Copy the entire completed output to USB; keep a second copy.
   Layout: `python/`, `bin/uv.exe`, `locks/`, `wheels/`, `source/sim/`,
   `licenses/`, `SHA256SUMS`, launchers, `runs/`. Windows execution and interrupted
   recovery must be exercised before declaring this bundle release-ready.
   Allow roughly 5 GB local + 10 GB USB initially; actual size is measured after
   build, allow additional space for retained versioned checkpoints. Use exFAT/NTFS.
2. **At the seat:** insert USB; photograph Windows version (`winver`), Task
   Manager CPU/RAM and GPU/driver. Record shutdown time. Keep USB connected.
   Reserve the last 30 minutes for copying evidence. No top-up/payment implied.
3. **Start:** open Command Prompt in the bundle folder, run `run.bat 80` for
   a two-hour visit (80 = timed seed minutes after smoke/setup). For longer visits
   select minutes leaving setup + 10-minute smoke + final 30 minutes. Default80.
   Runtime and venv use `%LOCALAPPDATA%\WBR-C1-T11`; to use USB instead, first set
   `set "WBR_WORK=E:\WBR-work"` using the actual drive letter. No activation.
   The launcher verifies payload hashes, installs only offline hashed wheels,
   saves `nvidia-smi.txt`, then runs the real v2 smoke and a fresh direct seed0.
4. **Watch smoke:** seed42 trains, checkpoints/reloads, restarts subprocesses,
   restores optimizer/counters/RNG/sampler, continues an update and verifies
   copied policy/normalizer. The ten-minute window includes setup; missing its deadline fails smoke.
   Rollout/update duration above60 seconds stops with a retained checkpoint. This is the legacy v2 smoke, not the new
   report-model/paired-baseline smoke proposed in REVIEW §3. No smoke data enters
   the timed seed. Photograph the USB checkpoint PASS and wall seconds/100k.
   A missing runtime/blocked executable is an infrastructure failure; retain
   `runs/launch-error.txt` and the console, ask staff about their permitted runtime.
5. **During seed:** checkpoints go directly to USB every5 wall minutes at a
   completed update, and at timed/final stop. Prior verified versions remain.
   `segment-*/progress.*` are optimizer logs; receipt records wall time including
   USB writes. Create an empty `STOP` file inside the seed folder for a controlled
   stop after the current update; remove it before resuming. Do not pull the USB
   or close the window while saving. Abrupt interruption loses work since last save.
6. **Recover after wipe/interruption:** copy nothing off the cafe disk; run
   `resume.bat 80` from the same USB. It recreates the offline venv and resumes
   the newest hash-verified complete snapshot across seed folders.
   Source/model/config mismatch rejects resume; corrupt/incomplete snapshots
   are skipped. Episode state is reset (explicit trajectory discontinuity);
   saved sampler and Python/NumPy/CPU torch RNG streams and normalizers resume.
   Full simulator continuation/bitwise future trajectories are not claimed.
7. **Before shutdown:** photograph final PARTIAL/COMPLETE counter and any error;
   retain **all `runs/`**, `bundle.json`, `SHA256SUMS`, source revision/patch and
   locks. Every `complete.json` contains per-file hashes and copied-policy reload
   PASS; confirm a final completion marker exists. Copy runs to a second
   owner-controlled drive if available, verify its file hashes, then safely eject.
   A timed PARTIAL seed is valid throughput evidence, never a full-budget result.

The exact v2 target remains3M transitions,8 environments,250 steps/environment,
10 epochs, original network/rewards/rates and CPU device. This ticket does not
run the final160-case evaluation or claim a new policy-performance result.
