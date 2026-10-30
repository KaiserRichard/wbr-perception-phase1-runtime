# Current state
Updated 2026-10-30 +07 · C1-T11 worker, uncommitted; conductor owns integration.

## Portable cafe bundle (C1-T11)
- Scripts in `research/rl/bundle/`: networked Mac builder, offline Windows launch,
  real v2 smoke/timed seed,5-minute verified USB checkpoints and newest resume.
- Read `ops/worklog/sessions/2026-10-30-c1-t11-portable-bundle.md` for commands/results.
- Target: Chợ Mơ Training Station, Windows x64 unknown version, RTX3060 12GB,
  32GB RAM, reset-on-shutdown disk, USB evidence,2–6h sessions.
- Frozen legacy PPO v2 recipe stays CPU MuJoCo/PPO; no JAX/MJX/CUDA payload.
  Minimal v2 change moves Unix-only supervisor import out of module import.
- Validation:9 protocol +16 reporting tests PASS;6 RL modules blocked on missing
  dependencies. Packaging/hash/corrupt-checkpoint fallback checks PASS.
- Next: conductor runs builder with network, then Windows smoke/interruption/
  resume. Downloads/Windows trainer execution remain UNVERIFIED. No commit requested.

## Existing boundaries/state carried forward
- V2 historical comparison complete; no new training executed by this ticket.
- V3 seed42 FAIL remains STOPPED; no reward tuning/retry/full experiment authorized.
- New R0 plan/review are proposals; this bundle benchmarks the legacy plant only.
- Owner-only `sim/parity/student.py::gain_schedule` untouched.
- STM32 owns balance/motor safety; no motor commands/flashing/hardware deployment.
- Camera execution belongs to owner/WBR-Perception; no Pi access in this session.
- Historical detailed receipts remain under sessions/reviews and evidence archive;
  preceding CURRENT content is available from git history.
