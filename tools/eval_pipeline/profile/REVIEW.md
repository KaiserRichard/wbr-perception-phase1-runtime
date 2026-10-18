# T6 independent review

## Verdict

**APPROVE-WITH-FIXES** — the implementation covers the T6 sampler, latency
analysis, validity gate and report. Review found and fixed four correctness
issues in validity, clock and missing-resource handling.

## Ranked findings

1. **High — `profile.py:142,311-322`: unsampled throttle rows blocked every normal 10 Hz run.** The
   sampler polls VideoCore at 1 Hz but emitted `UNKNOWN` bit fields on the
   intervening rows. The validity gate treated those as failed observations,
   so a healthy run could never pass. Added `throttle_sampled` to each row and
   made validity ignore only explicitly unpolled rows; a failed poll still
   blocks. Regression coverage: `tests/test_profile.py` checks both a mixed
   sampled/unsampled PASS and a run with no poll BLOCKED.
2. **High — `profile.py:253-256`: arbitrary ClockMap output could be compared with host monotonic
   epochs.** The latency path converted source timestamps but did not check the
   mapped domain/session before calculating a realtime factor against an
   observer host span. It now requires `host_steady` and the exact observer
   session, otherwise analysis returns an error. Regression coverage supplies
   a map with the wrong target clock.
3. **High — `profile.py:291-325`: incomplete validity evidence could be mistaken for a pass or
   error.** A missing `samples.csv` raised an internal-error exit instead of a
   BLOCKED result; no throttle polls could mark the throttle criterion PASS;
   and one missing temperature row could be hidden by other valid readings.
   Missing files, missing any SoC sample, and zero throttle observations now
   produce BLOCKED criteria/results. Known throttle or temperature violations
   still produce FAIL. Regression coverage exercises each case.
4. **Medium — `profile.py:74-85,108-143`: absent proc/sys values were sometimes serialized as empty maps or
   the shared sampler's `UNAVAILABLE` label.** T6 calls for explicit UNKNOWN
   values. Empty CPU, frequency and thermal maps and RSS status are now
   normalized to `UNKNOWN`; a regression test checks missing proc/sys trees.

## Ticket requirements

- **Sampler:** stdlib process/per-core CPU, optional thread CPU, RSS/PSS,
  per-core frequency, thermal zones, cooling-device state and decoded lower
  rate throttle bits are present. Missing proc/sysfs/VideoCore values are
  represented as `UNKNOWN`. UTC and monotonic anchors are named separately.
- **Latency:** event lifecycle and existing patch CSV parsers are reused;
  nearest-rank P50/P95/P99/max, tracking and end-to-end durations, configured
  camera-period overrun count and realtime factor are reported. Cross-clock
  source stamps require a ClockMap targeting the event host session.
- **Validity/report:** PASS/FAIL/BLOCKED result contract and analyze-only mode
  are present. Thresholds live in `config.json`; reports include JSON/Markdown
  and a temperature plot when matplotlib is installed.
- **Fixtures/docs:** synthetic event and proc/sys fixtures, plus a compact
  throttle fixture derived from saved N4A resource evidence, are included.
  No per-frame timing trace was found in the two specified experiment folders;
  their saved ORB stdout does not provide the patch timing CSV. README and
  REPORT describe commands, criteria, limitations and unverified hardware.
- **Ownership:** edits are limited to `tools/eval_pipeline/profile/`. No
  commit or hardware action was performed.

## Fixes and verification

Changes are in `profile.py`, `tests/test_profile.py`, and `README.md`. Exact
commands and complete output are in `tests/last-run.log`.

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/eval_pipeline/profile/tests -v`
  — **12 tests passed**.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/runtime_observer/tests -v`
  — **20 tests passed, 1 skipped**. The skipped test requires the observer
  Makefile's C++ binary in its separately owned directory; it was not built
  during this ticket review.

## Remaining open items

- Pi 5 sampling behavior, proc/sysfs availability, `vcgencmd` cadence, thermal
  policy limit, sampling overhead, and real sustained-load latency remain
  **UNKNOWN**; fixture tests do not establish a hardware gate PASS.
- The N4A fixture is derived from actual saved throttle evidence but is not a
  full resource trace. No saved observer event trace or per-frame patch timing
  CSV was available in the ticket's referenced experiment folders.
- The Python observer suite's C++ recorder round-trip test was skipped as
  described above.
