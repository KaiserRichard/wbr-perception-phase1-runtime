# T21 clockmap labeling fix — 2026-10-18

**Built:** Clockmap still uses NumPy's linear interpolation for its percentile
values. Every percentile object and top-level analysis report now labels the
method `numpy linear interpolation`. The README explains the difference from
the nearest-rank method used by runtime_observer/profile.

**Verification:** `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s
tools/clockmap/tests -v`; exact output is in `tests/last-run.log`. Regression
coverage checks labels on top-level, latency and fit-residual outputs.

**NOT verified / risks:** the tests use synthetic timestamps. Real Pi recorder
files, SDK/host mapping and hardware timing remain UNKNOWN; this statistical
label does not qualify a clock map or a physical gate.

Proposed commit message: `fix(clockmap): label percentile interpolation method`
