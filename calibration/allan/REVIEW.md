# Independent review of T21 — 2026-10-18

**Verdict: REQUEST-CHANGES.** The three requested implementation changes work
on the exercised finite/synthetic inputs. Review corrections and expanded
regressions are applied. An inherited profile validity bug still reports PASS
with invalid temperature evidence; its production fix is outside this ticket's
owned paths. External Raspberry Pi wording could not be independently verified
under the binding network prohibition. No hardware gate is passed.

## Ranked findings and disposition

1. **High, OPEN — false PASS with non-finite temperature evidence.**
   `tools/eval_pipeline/profile/profile.py:307` accepts any Python float/int,
   including NaN. With saved observations `[55.0, NaN]`, the maximum remains
   55.0 and missing-temperature detection remains false. The tool returns
   PASS/0; the required result is BLOCKED/2. This is inherited:
   `git diff origin/main -- tools/eval_pipeline/profile/profile.py` is empty.
   Added `test_known_defect_nonfinite_temperature_must_block` at
   `tools/eval_pipeline/profile/tests/test_profile.py:90`, explicitly marked
   expected-failure. The unsuppressed run in `tests/known-defect.log` under
   that directory demonstrates `AssertionError: 0 != 2` and the erroneous
   PASS table. T21 owns profile config/tests, not `profile.py`; COMMON.md also
   says, “if you find a real bug in one, write it up in your REPORT.md instead
   of fixing it (another ticket may touch it).” Reported in profile REPORT.md;
   an owning ticket must reject non-finite observations as missing, preserve
   any independent FAIL, and remove the expected-failure marker after repair.

2. **Medium, corrected — audit overstates profile contract compliance.**
   `docs/audits/2026-10-18-tool-consistency.md:78` calls profile validity
   compliant and the subsequent paragraph says no contract defects were found.
   Finding 1 disproves an unconditional claim. Appended a dated correction at
   line 118, preserving all historical audit text as required. Also clarified
   that the audit's full-repository aggregate table is historical, not a
   result of this independent review.

3. **Medium, OPEN verification limitation — exact Raspberry Pi wording.**
   Both `lab/power_usb/thresholds.yaml:13` and
   `tools/eval_pipeline/profile/config.json:5` cite the same official Pi 5
   article and encode 80 °C. The comparisons are inclusively failing and
   match the saved local runbook at
   `experiments/2026-10-13-pi5-env-snapshot/CODEX_INSPECTION.md:147`.
   No cached first-party article text was found locally. COMMON.md forbids
   network use beyond git, so neither the exact “reaches” wording nor the
   ticket's “soft throttling” terminology was independently checked. Retain
   this explicit limitation; local policy agreement does not verify a vendor
   quotation or deployed firmware behavior.

4. **Low, corrected — incomplete regression coverage.**
   `calibration/allan/tests/test_stats.cpp:10` originally covered only a
   backward Hardware Clock → System Time jump. Expanded it to cover forward
   jumps, equal numeric timestamps across domains, Global Time, immediate
   recovery, same-domain reversal, and independent frame counters. The stub
   now exposes and distinguishes Global Time instead of treating every
   non-hardware domain as System Time. Clockmap's new label assertions had
   omitted absolute residuals and per-segment latency; a recursive check now
   covers all four distributions, and both CLI JSON reports are checked.
   Power tests now isolate exactly 80 °C in either temperature source.

5. **Low, corrected — documentation inaccuracies.**
   `tools/clockmap/README.md:168` pointed at nonexistent
   `tools/runtime_observer/profile`; it now names the two actual directories.
   `docs/audits/2026-10-18-tool-consistency.md:105` described the *next* sample
   as establishing the baseline. An append-only correction clarifies that
   the transition sample establishes it; the next same-domain sample is
   measured. The expanded C++ test checks that distinction. Profile REPORT.md
   also now identifies its historical shared-decoder bug paragraph as stale:
   current `resource_sampler.py:24` uses the correct `FIELDS[14:]` slice.

## Requirement-by-requirement assessment

| Requirement | Assessment |
|---|---|
| Allan skips cross-domain dt, counts transitions and resets baseline | Met. `Stats::add` updates `last_stamp` and `domain` on the transition; no cross-domain dt is calculated. Regression compiles/runs with the local stub. |
| Inclusive temperature boundary in both tools | Met for finite observations. 79.9 °C PASS and 80.0 °C FAIL are tested in both tools; power additionally tests each source independently. |
| Cite and verify Raspberry Pi wording | Citation present in both configs and READMEs. Independent external wording verification remains UNKNOWN under the no-network rule. |
| Retain NumPy interpolation and label every percentile/report | Met. All percentile objects and both CLI reports carry `numpy linear interpolation`; numeric p50/p99 interpolation tests still pass. README distinguishes runtime_observer/profile nearest-rank. |
| Append dated “Resolved by T21” list to audit | Met. Original list retained; review adds only a dated addendum. |
| PASS/FAIL/BLOCKED fixtures and real saved evidence | Existing power/profile suites cover all statuses; power's historical partial fixture is BLOCKED and the real N4A throttle fixture is FAIL. Invalid non-finite profile evidence remains the open exception in finding 1. |
| Run added tests and imported suites; preserve commands/output | Met below. Initial and final outputs retained. No tests were skipped in the final imported suite. |
| README, REPORT, REVIEW and last-run logs | Present; reports updated with review corrections and remaining risks. |
| Hardware, network and git-write restrictions | Respected. No device capture, SSH, install, commit or push. |

## Exact commands and outputs

All commands run from `/Users/quockaiser/Desktop/Research/wbr-wt-auditfix`.
Each output path below contains verbatim stdout/stderr. Initial four-suite
commands used the same unittest invocations with `review-before.log` instead
of `last-run.log`: 13 Allan, 37 clockmap, 58 power and 13 profile tests passed.
The initial imported Python-only observer run executed 20 tests with one C++
round-trip skipped; the subsequent make target built the probe and ran all
20 without skips. The latter transcript replaces the preliminary observer log.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s calibration/allan/tests -v > calibration/allan/tests/last-run.log 2>&1
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/clockmap/tests -v > tools/clockmap/tests/last-run.log 2>&1
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s lab/power_usb/tests -v > lab/power_usb/tests/last-run.log 2>&1
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/eval_pipeline/profile/tests -v > tools/eval_pipeline/profile/tests/last-run.log 2>&1
make -C tools/runtime_observer test > tools/clockmap/tests/runtime-observer-review.log 2>&1
bash -n calibration/allan/record_allan.sh
git diff --check
```

| Final suite | Result | Exit |
|---|---|---|
| Allan | 13 tests, OK | 0 |
| Clockmap | 38 tests, OK | 0 |
| Power/USB | 59 tests, OK | 0 |
| Profile | 14 tests, 13 pass and 1 expected failure | 0 (not a clean PASS) |
| Imported runtime_observer make target | C++ recorder probe and 20 Python tests, OK | 0 |
| bash syntax and whitespace checks | No output | 0 |

The profile defect was also run with the expected-failure marker removed:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -c 'import sys, unittest; sys.path.insert(0, "tools/eval_pipeline/profile/tests"); import test_profile; test_profile.ProfileTests.test_known_defect_nonfinite_temperature_must_block.__unittest_expecting_failure__ = False; suite = unittest.TestLoader().loadTestsFromName("ProfileTests.test_known_defect_nonfinite_temperature_must_block", test_profile); result = unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(0 if result.wasSuccessful() else 1)' > tools/eval_pipeline/profile/tests/known-defect.log 2>&1
```

Exit 1; one test failed (`0 != 2`). This expected reproduction failure is
reported separately, not disguised as a successful qualification.

## Scope and remaining items

Reviewed `git diff origin/main --stat`, `git diff origin/main` by affected
path, and untracked files. HEAD initially was `05aa81e`, with audit commit
`4042342`, based on merge-base `965768b`; origin/main was `ca1a22c`.
Differences involving removed lab orchestration/platform files and perception
health integration are main-only history absent from this older branch,
not changes introduced by T21. `git diff 965768b..HEAD --name-only` confines
the two branch commits to T21/audit paths. Do not apply the broad reverse
diff as a merge patch; the conductor must preserve newer main work when
integrating. No unrelated files were edited during review.

The profile production fix and external wording verification are the remaining
items before unconditional approval. No Pi firmware, actual librealsense SDK
ABI, camera IMU, STM32 body IMU, clock mapping, sustained performance or
hardware was verified. Tests are software evidence only. All review edits
remain uncommitted.

Proposed commit message: `test: strengthen T21 regressions and record independent review findings`
