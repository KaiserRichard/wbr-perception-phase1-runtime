# T21 Allan recorder fix — 2026-10-18

**Built:** `Stats::add` counts SDK timestamp-domain changes without subtracting
stamps across the transition. The first sample in the new domain resets the
interval baseline; later same-domain samples again contribute reversal,
duplicate and max-gap diagnostics. `tests/test_stats.cpp` directly exercises
the recorder's private stats type with the local librealsense API stub.

**Verification:** `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s
calibration/allan/tests -v`; exact output is in `tests/last-run.log`. The test
compiles and runs the synthetic C++ regression when a C++17 compiler exists.

**NOT verified / risks:** no actual librealsense headers/library, Pi capture,
or device behavior was tested. The stub tests recorder logic only and does not
establish SDK ABI compatibility or a hardware gate PASS.

Proposed commit message: `fix(allan): skip timestamp intervals across domain changes`
