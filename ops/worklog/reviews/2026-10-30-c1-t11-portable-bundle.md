# C1-T11 implementation handoff (not a validated Windows milestone)

No PR/commit/merge by owner request. Files and exact local commands/results:
[session receipt](../sessions/2026-10-30-c1-t11-portable-bundle.md).

The builder creates an offline Windows3.12 x64 payload and ZIP. Launchers install
CPU wheels without admin, record host/GPU, smoke real legacy v2 and time a seed.
USB checkpoints save optimizer/normalizer/counters/RNG/sampler, verify copied
policy actions and counters, publish per-file hashes and retain older versions.
Resume restarts episodes and documents the discontinuity. No recipe changes.

Validation:25 existing pure tests PASS;6 RL test modules cannot import missing
simulation dependencies. Syntax/packaging/hash/recovery selection checks PASS.
No network/downloads/Windows execution, and no new training/hardware activity.
Native Windows support, pinned-wheel availability and live optimizer recovery
remain unverified. This is legacy v2 portability, not the new report-model R0
experiment or REVIEW §3's proposed paired-baseline smoke.

Recommendation to conductor: run the builder on a networked Mac, retain failures
without relaxing pins, then run Windows smoke + abrupt interruption + USB resume
in a fresh local environment before release. Confirm exact standalone/uv assets
and wheel resolution, copied-checkpoint reload, continued counters and deadline.
Claude review belongs after that completed runtime milestone.
