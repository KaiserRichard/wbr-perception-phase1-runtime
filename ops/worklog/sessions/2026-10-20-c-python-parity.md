# Milestone 1: compiled C reference and learner harness

Date: 2026-10-20 +07. Mode: Simulation / control. Agent: codex-f conductor.
Branch: `chatgpt/20261020-c-python-parity`, base `0e48cff` (merged PR #37).
Initial tree clean; current `sim/` implementation is this task's new work.
Documentation change set: DOC-20261020-4. Decisions D-20261020-16/17.

## Goal, scope and ownership

Owner authorizes the approved sequence without waiting for a physical WBR:
C/Python parity, ASSUMED reduced six-state physics, new matched LQR, RL comparison.
Physical estimates remain parallel work. No masses/inertias have been measured.
Gain-schedule function body, A/B matrices, LQR call and reward belong to the
learner. Agents own build, harness, scaffolding, plotting and logs.
Rollback: keep this feature branch and return to base; no shared checkout edits.

Architecture of this checkpoint: unchanged pinned upstream C + minimal host ABI
-> shared library -> ctypes oracle -> shared vectors -> learner function checker.
A separate native C suite checks VMC geometry, signs and torque mapping.
Affected paths: `sim/`, generic test discovery in `tools/run_all_tests.sh`, worklog.
No firmware, motor, Pi, camera or canonical gate file is modified.

## Teaching explanation supplied before implementation

The cubic schedule evaluates `K_i(L)=a3*L^3+a2*L^2+a1*L+a0`.
Compare against compiled original C before physics so ordering/sign errors are
localized. Twelve gains become wheel and virtual-hip rows of six each.
Primary source: [pinned VMC/gain implementation](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/Algorithm/VMC/VMC_calc.c#L219-L227).
The learner's `sim/parity/student.py::gain_schedule` body remains TODO.

## Implementation and provenance

SOURCE-SUPPORTED: source pin `6855ef8c6da20246251cfd473467c04112bf800f`.
Copied unchanged VMC `.c/.h`, chassisR source (initializer extraction only), MIT
LICENSE and source notices. `PROVENANCE.json` records each input's SHA-256.
Source task execution is excluded. The builder hashes inputs before compiling
original functions with clang, float32, no fast-math and no fused contraction.
Host CMSIS trig shims use libm. Minimal INS type includes only consumed fields.
Native static state is accessed sequentially. VMC is fixed-pose with initialized
history, not a transient leg-motion test. Host guards do not modify source C.

Shared fixtures include 8 scalar polynomial cases, 5 schedule lengths, 9 valid
VMC cases and invalid-input cases. Learner checker plans 13 gain cases, enforces
2x6 finite output and records hashes/status. Tolerances were declared before
exercise evaluation: absolute 2e-5, relative 2e-6. Native checks additionally use
independent symmetric circle geometry/force anchors and finite differences.

## Delegation and review receipt

Owner designated f/g/i/k Plus; subscription status is USER-REPORTED. Conductor f
was not launched as a worker (an earlier help-only invocation did not start work).
Actual delegated CLI: codex-g, ephemeral, read-only sandbox, review only.
Completed exit 0. No account credentials were read. No i/k worker was necessary.
Review output: `/private/tmp/wbr-parity-codex-g-review.md`, SHA-256
`5a026ccbd99bdc139a8877d133e07990deb4ca3955a648b73c28d9291e9f4e69`.
Findings: align BD guard 1e-7 -> documented 1e-6 m, add boundary test; add
independent VMC anchors and isolated force/torque tests. Both addressed locally;
the reviewer saw the earlier smoke artifact, not the final revised build.
This worker review does not substitute for required Claude merge review.

## Execution evidence

MEASURED on the Mac; Python 3.12, Apple clang (full version/options in receipt).

1. `/usr/local/bin/python3.12 .github/run_unittest.py sim/parity/tests`:
   initial 13/13 PASS; after review additions 15/15 PASS, exit 0, zero skipped.
   Includes source/library tamper rejection, no-overwrite contracts, C polynomial
   anchors, VMC signs/symmetry/finite differences and runner FAIL/BLOCKED controls.
   A C-backed test double verifies runner plumbing only, not a Python port.
2. `/usr/local/bin/python3.12 -m sim.parity.build_reference --out-dir /private/tmp/wbr-parity-m1-20261020-01`:
   exit 0. Artifact directory contains the shared library, generated coefficients
   and receipt. Local base HEAD is recorded together with dirty status/source hashes.
3. `/usr/local/bin/python3.12 -m sim.parity.check_student --build-dir /private/tmp/wbr-parity-m1-20261020-01 --out /private/tmp/wbr-parity-m1-20261020-01/gain-result.json`:
   **BLOCKED**, exit 2: intentional learner TODO. Stops at first TODO; not 13 passes.
4. `WBR_PARITY_BUILD=/private/tmp/wbr-parity-m1-20261020-01 /usr/local/bin/python3.12 -m unittest sim.parity.exercises.test_gain_schedule -v`:
   expected FAIL, exit 1, because gain schedule is unimplemented. Separate from CI.
5. `bash -n tools/run_all_tests.sh` and `git diff --check`: exit 0.
   Generic runner now discovers `sim/*/tests` and excludes learner exercises.
   Full repository runner started; final result will be appended below.

Artifacts outside git (temporary paths; archive before any cleanup):
- Build receipt SHA-256: `3fbed665c77c29e04233da3260ae3940a0659e865922296300391c2b89bef260`.
- Library SHA-256: `b82baf11799dae21454965f7912a96880aef71c38603b319a0c2282c9255041b`.
- Full-suite stdout/stderr: `/private/tmp/wbr-parity-full-tests-20261020.log`.

## Interpretation and next step

MEASURED: original C compiles and infrastructure checks pass. This is host-only
numerical evidence, not firmware/ARM/CMSIS, physical balance or sim-to-real evidence.
**Milestone 1 is incomplete**: Python gain TODO and Python VMC parity remain.
No MuJoCo dynamics, new LQR or RL training was run; no dependencies installed.
Recommendation: owner writes gain_schedule; review it and run the 13 cases,
then finish Python VMC parity before the reduced six-state physics milestone.

Two checkpoint questions (answers PENDING; do not claim understanding assessed):
1. What does each row of the 2x6 output represent, and why preserve coefficient order?
2. Why can a host C/Python match not establish that the real robot will balance?

## Publication and final validation

Pending receipts below; no code merge authorized. Claude must review before merge.

Staged whitespace check: new authored files pass with vendored source excluded.
The unrestricted check reports upstream trailing whitespace in unchanged VMC and
chassis files. Retained bytes intentionally to preserve verified source hashes;
do not normalize those files. Full repository runner also creates untracked host
binaries/dSYM and `tools/perception_health/c/mcu/.build/`; these are not staged.

Published implementation commit `28fea56`; push exit 0. Opened draft PR #38:
https://github.com/KaiserRichard/wbr-perception-phase1-runtime/pull/38
Attached PR to this chat. Claude review request prepared at
`ops/worklog/reviews/2026-10-20-c-python-parity.md`; review and owner merge go-ahead
remain pending. This is not a request to deploy or alter the approved research plan.

Final validation receipts:
- Full local `bash tools/run_all_tests.sh` exited 1. Only final summary failures:
  make and Python variants of existing `tools/link_bench` test_host_simulator.
  Root diagnostic: `baud 460800 not supported by termios` on macOS; teardown
  also times out waiting for the host simulator after termination. Local runner
  selected Python 3.11; targeted parity used Python 3.12. No unrelated code changed.
- New `python:sim/parity/tests` PASS in full runner, 15 tests, zero skips.
- Linux CI for exact head `bfc84bf59495dfc82388f391e07cbba5d714cbe4`: SUCCESS,
  https://github.com/KaiserRichard/wbr-perception-phase1-runtime/actions/runs/39375830118/job/118473629046
- Draft PR #38 remains unmerged. Publication receipt update only follows this
  green implementation/review head; do not imply the subsequent log commit was
  already checked. Review-request commit bfc84bf push exit 0.

Recommendation: no retry of the localized unsupported-baud failure or unrelated
test edit; use passing Linux CI for repository integration, retain the local
failure. Owner writes gain_schedule next. No extra physical measurement requested.
