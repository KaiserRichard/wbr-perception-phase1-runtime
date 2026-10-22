# V3 bounded residual reward — implementation review, 2026-10-22

**For Claude: implementation review only; no pilot or WBR training launched.**
The owner delegated reward implementation, superseding the earlier owner-exercise
wording. The canonical proposal and its appended Claude review remain the spec.
[PR126](https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/126)
is intentionally left open for Claude; no PR was merged.

- New `sim/rl/v3_pilot.py` and `v3_pilot_config.json` implement
  `1/(1+beta*C) - I_physical`, beta=4.29553264604811. C is the mean completed
  post-tick Q/R cost using clipped total issued torque. Stable arithmetic retains
  positive alive rewards even for extreme finite costs; no residual penalty.
- Physical limits and timeout behavior match v2: either |angle|>=45 degrees or
  |x|>1.5 m terminates and subtracts exactly1; clean10s timeout truncates for
  bootstrap. A physical violation on the last tick wins over timeout. Nonfinite
  costs, warnings or invalid time abort rather than supply invalid rewards.
- V2 source/config/protocol/frozen reports, augmented plant, observations,
  Q/R, gamma0.99, 500Hz LQR/100Hz residual timing and caps are unchanged. V3 has
  its own residual step loop so no hooks or edits are added to frozen v2.
- Actor-output mean weights/bias alone start at zero; exploration log-std stays
  -1. Constructed and saved/reloaded normalized policies reproduce original LQR
  observations, truth, noise and commands across all four delays before learning.
  Checkpoint/evaluation operations preserve Python/NumPy/Torch RNG state.
- Pilot/diagnostic commands and all pre-declared screens are in `sim/rl/README.md`:
  seed42/eightenvs/2000-transition updates, snapshots0/100k/end, fixed16 cases,
  raw returns/lengths and additive terms before normalization, per-update log-std
  and sampled/deterministic |residual|/cap. Saved-v2 diagnostic also retains the
  residual series along one archived LQR trajectory; it was not run this session.
- Clock interpretation is explicit: elapsed budget starts after snapshot0 prep,
  includes100k evaluation and update overhead, and stops at a complete update
  meeting200k+600s or1200s. Active training/evaluation/full-wall times, stop reason,
  minimum-duration overshoot and maximum-budget overrun are recorded separately.
  The no-shorter-episodes screen compares mean lengths in the two50k windows.

Verification (existing backend, no environment changes):

```sh
PY=/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python
"$PY" -m unittest sim.rl.tests.test_v3_pilot sim.rl.tests.test_v2 -v
"$PY" -m sim.rl.v3_pilot --help
git diff --exit-code origin/main -- sim/rl/v2.py sim/rl/v2_config.json sim/rl/protocol.json sim/rl/RESULTS_2026-10-20.md sim/rl/RESULTS_V2_2026-10-20.md sim/augmented.py sim/configs/assumed_actuator_noise.json sim/parity/student.py
```

Worker18 tests passed; conductor35 tests passed in18.931s with `PPO.learn` patched to raise
throughout verification. Tests cover hand-computed states/torques, strict alive
positivity, mean-before-transform, partial holds, exact physical boundaries,
physical/timeout precedence, normalized-policy reload/plant parity, RNG isolation,
raw monitoring, worker failure cleanup and all pilot screens. Independent code
review found no blocking reward/plant/termination issue. Full CI status is on the
implementation PR. CI retains its existing64-step CartPole backend smoke; no
v3 optimizer smoke, pilot, saved-model diagnostic or WBR training was executed.

Logs: `/private/tmp/wbr-v3-bounded-reward-20261022-01/`; worker receipts are linked
from `ops/worklog/sessions/2026-10-22-v3-bounded-reward-worker.md`. The first
conductor wrapper failed because spawn cannot re-open `<stdin>`; the saved-file
wrapper corrected that harness error, and the failed log is retained.

**Limitations / recommendation for Claude:** review the isolated step loop,
reward/flags, initialization and screens before any separate pilot instruction.
Pilot orchestration has not been exercised with learning. These are engineering
screens, not significance tests, a reward-causality result or a PPO/LQR superiority
claim. Held-out1000–1019 and the primary endpoint are unchanged; a future full arm
requires its own passing pilot and at least5 seeds. Keep the pilot unlaunched.

## Claude review (2026-10-22)

**Decision: approved and merged (PR126, both CI checks green).** Read: `sim/rl/v3_pilot.py`, `v3_pilot_config.json`, the test list, README section and the CURRENT.md change, against the proposal and my additions. No runs.

**Matches the approved design.**
- Reward: `1/(1+βC)` of the mean completed-tick cost, β = 0.03/(0.97·min Q_ii t_i²) = 4.2955 computed from the protocol, no extra residual penalty. The large-cost branch is the same expression rearranged, so huge finite costs still give a strictly positive reward. A fall gives `base − 1 ∈ (−1, 0]` with `terminated=True`; the 10 s limit is `truncated` only. So any surviving step is worth more than falling. ✓
- Plant loop is a local copy of v2's with only cost instrumentation and the reward changed; a test checks identical plant/truth against v2. v2 files untouched. ✓
- Zero-init: only `action_net` weight/bias zeroed, log-std kept at −1. Parity is checked on the constructed and reloaded policy against the 500 Hz LQR for three policy steps at every delay, including capture arrays. ✓
- All three of my additions are in: v2 bias `diagnostic` (inference only), leg-rate screen plus explicit 16/16 strict at snapshot 0 and end, and per-update log-std, deterministic mean |residual|/cap and sampled noise. ✓
- Budget: 250 steps × 8 envs = 2,000 per update, so 100k is an exact update boundary and the snapshot fires. Stop rule matches the proposal; no stopping on a score. ✓

**Minor, no change needed before the pilot.**
- Final 16/16 strict already implies zero leg-rate violations in [9, 10] s (strict requires every state inside tolerance over the settle window), so the leg-rate screen is redundant when strict passes. It is still useful as a reported count.
- If 100k is not reached within 20 min, `pilot_screens` returns `pass: False` with reason "Missing/incomplete". The proposal calls that *insufficient evidence*, not a failed reward. Read it that way in the report.
- Telemetry does one extra policy forward pass per step. On a slow Mac this lowers transitions per minute inside the fixed time budget; check `progress.json` early.

**Next (needs the owner's go):** 1) run `diagnostic` (about a minute, no training); 2) if the v2 residuals show a clear non-zero mean, run the pilot once with a new output folder. The `$PY` venv in the README is under `/private/tmp` and may be gone after a reboot; recreate it from `sim/requirements.lock` + `sim/rl/requirements.txt` if so. Bring `status.json`, `development.json` files and `learning-curves.svg` back for review.
