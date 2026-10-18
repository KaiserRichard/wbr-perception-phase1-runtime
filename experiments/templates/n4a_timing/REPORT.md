# T15 report — N4A controlled timing rerun package

## Built

- `run_n4a_timing.sh` and its stdlib Python helper perform a preflight, record provenance, run one reviewed EuRoC launcher invocation per repetition, attach the reviewed profiler to the exact ORB PID, stop it cleanly, and cool between runs.
- `analyze_n4a_timing.py` delegates accuracy and profile work to the reviewed tools, writes per-run accuracy/latency/temperature/throttle/VALID results, excludes invalid runs, and aggregates only VALID runs.
- `PROTOCOL.md` defines the active-cooling / 5 V / 5 A hypothesis, fixed variables, operator sequence, evidence and falsifiers. `config.json` owns package-specific numeric limits with source/rationale labels.
- Unit tests exercise a valid stub capture, a throttled run excluded from aggregation, and a preflight refusal, plus a fixture derived from the saved N4A throttle evidence.

## Verification

The exact command and output are in `tests/last-run.log`. The intended checks are:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s experiments/templates/n4a_timing/tests -v
bash -n experiments/templates/n4a_timing/run_n4a_timing.sh
bash -n experiments/templates/n4a_timing/analyze_n4a_timing.sh
```

The tests are offline fixture/stub checks. They do not establish a Pi performance result, a thermal/power result, or an N4A gate PASS.

## Not verified and open risks

- No Pi, camera, serial device, SSH session, system package installation or network access was used.
- The exact `/proc` executable/parent relationship, `vcgencmd` availability, CPUFreq paths, thermal-zone identity, cooling-device exposure, profiler overhead and accuracy-runner behavior remain unverified on the target Pi.
- `run_euroc.sh` holds the authoritative execution lock; the template's preflight lock observation is necessarily a point-in-time check before that runner reacquires it.
- The existing profile sampler's 1 Hz throttle polling and sampled sysfs values cannot prove conditions between polls. The existing tools' proposed temperature/accuracy limits remain proposed or source-supported as documented in their configs.
- A latency result requires an observer event CSV or ORB tracking CSV. The sampler alone records resources and cannot prove camera-to-pose latency or real-time factor.
- Prior historical throttle bits are deliberately treated as invalid unless the operator opts into a diagnostic exception; such runs never enter the VALID aggregate.

Existing defects found in the reviewed dependency directories were not changed, per the ticket and COMMON.md. In particular, the profiling review records a known field-mapping defect in `tools/runtime_observer/resource_sampler.py`; this package delegates to the reviewed profile tool and reports its output rather than modifying that directory.

Proposed commit message: `Add controlled N4A timing rerun package`
