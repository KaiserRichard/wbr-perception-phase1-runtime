# C1-T11 portable RL cafe bundle · 2026-10-30

- Read CURRENT/profile, research rules, sim guide, PLAN, REVIEW §3, cafe strategy,
  PPO v2 trainer/config/protocol and requirements. Owner requests no commits or network.
- Added `research/rl/bundle/{build_bundle.sh,package.py,launch.py,portable.py,run.bat,resume.bat,CHECKLIST.md}`.
- Mac networked build (conductor):
  `bash research/rl/bundle/build_bundle.sh /absolute/new/path/WBR-C1-T11`.
  Downloads pinned Python3.12.7+20241016/uv0.5.4, Windows cp312 binary wheels
  from existing requirements; CPU torch2.2.2+cpu, additional Windows pandas tzdata.
  Generates transitive SHA256 wheel lock, source snapshot/patch, notices,
  payload SHA256SUMS and same-content ZIP. No download performed in this sandbox.
- V2 only source edit: defer Unix `fcntl` import to its original supervisor;
  Windows adapter imports and uses existing environment/config unchanged.
- Portable adapter retains3M budget,8 spawned environments,250 rollout steps/env,
  all original optimizer/network/reward/rate/device choices. Direct seed0 default;
  smoke seed42 separate. Ordinary CPU MuJoCo; no JAX/MJX dependency or CUDA option.
- Five-minute checkpoints after complete updates, stop/final checkpoint, copied
  policy and normalization reload verification, optimizer/counters/RNG/sampler,
  actual plant ticks, source/model/config identity, hashed completion marker.
  Corrupt/incomplete newest snapshot falls back; previous versions retained.
- Checkpoint verification restores global RNGs after SB3 reload; resumed VecEnv
  clears pending reseed before restoring samplers. Episodes reset explicitly.
  Simulator state/bitwise continuation not supported or claimed.
- Launcher verifies payload, creates/reuses user-local venv, installs offline
  hash-locked wheels, records systeminfo/nvidia-smi, real ten-minute smoke including
  setup, then timed seed. Missed deadline or update>60s fails with evidence.
  USB logs/checkpoints are durable; no paid session/training was launched here.
- Validation: shell syntax, Python compilation, git diff whitespace PASS.
  Synthetic wheel packaging/lock/license extraction/copied config/hash check PASS.
  Checkpoint selection/corrupt fallback/incomplete-marker rejection PASS.
- `python3 -m unittest discover -s sim/rl/tests -v`:
  9 protocol tests PASS;6 test modules failed import (gymnasium/mujoco/scipy missing).
  Log `/private/tmp/c1-t11-rl-tests.log`.
- `python3 -m unittest discover -s sim/rl/reporting/tests -v`:16 PASS;
  log `/private/tmp/c1-t11-report-tests.log`.
- Existing lab-ops venv also lacks torch. No dependency installation attempted
  because network is forbidden; no experiment/environment was modified.
- LIMITATION: exact remote assets/wheel availability, real Windows startup,
  optimizer resume and ten-minute smoke remain unexecuted. Conductor must build
  and exercise Windows launch/recovery before release. REVIEW's proposed new
  report-model/paired-baseline smoke is outside this frozen legacy v2 ticket.
- No commits/pushes, hardware/Pi access or owner-only schedule edits.
  No DECISIONS/DOCUMENTATION_LOG entries per sim/AGENTS.md and RESEARCH_RULES.md.
