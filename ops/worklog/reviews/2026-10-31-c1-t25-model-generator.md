# C1-T25: manifest-driven WBR model generator

## Result

Added `sim/wbr_model/`, a YAML-driven MuJoCo MJCF generator with schema/example,
source tags, validation, CLI, CAD data request instructions, and a headless test.
The first version uses a documented equivalent-slider leg representation. It
keeps both five-bar link length sets as manifest values and XML metadata but
does not implement the closed loops.

## Evidence

- `~/Desktop/Research/wbr-lab-ops/.venv/bin/python -m unittest sim.wbr_model.tests.test_build` — 3 tests PASS; generated MJCF advanced 1000 steps with finite state/acceleration; invalid inertia and mass sum rejected; triangle inequality rejected.
- `~/Desktop/Research/wbr-lab-ops/.venv/bin/python -m sim.wbr_model.build sim/wbr_model/examples/assumed.yaml /tmp/wbr-c1-t25.xml` — MuJoCo compilation and XML write PASS.

## Limitations and next inputs

The example is illustrative and is not a calibrated robot. `params_manifest_src.yaml`
has unresolved mass assembly ownership and null CAD inertia tensors, so it is
not directly buildable. CAD/mechanical team must provide per-body mass, COM,
full inertia and frames, assembly membership, left/right linkage geometry and
joint limits, plus actuator limits and motor-to-linkage mapping. The report's
scalar inertias remain ASSUMED. The fallback YAML parser supports the documented
v1 mapping/flow-value subset; install `sim/wbr_model/requirements.txt` for full
YAML parsing.

No commit was made, per ticket.
