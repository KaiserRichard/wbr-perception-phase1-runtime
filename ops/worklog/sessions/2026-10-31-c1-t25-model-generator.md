# C1-T25 manifest-driven model generator

- Inspected the interrupted `sim/wbr_model/` draft, `params_manifest_src.yaml`, and `sim/twin3d/model.py`; left twin3d and the source manifest unchanged.
- Kept the reduced slider-leg model, documented that it is not a five-bar loop model, and made dimensions, masses, COMs, full inertia tensors, joint limits, and per-side actuator caps manifest-driven.
- Added source-tagged schema/example, validation for positive-definite inertia, principal-moment triangle inequality and mass sum, CLI, CAD request list, and headless MuJoCo test.
- First MuJoCo test exposed an inertialess moving hip body. Combined hip and extension joints on the inertial leg body; rerun passed.
- The specified venv lacked PyYAML and network access blocked installation. Added a constrained standard-library fallback for the documented manifest subset; retained PyYAML as the full YAML dependency.
- Commands: `~/Desktop/Research/wbr-lab-ops/.venv/bin/python -m unittest sim.wbr_model.tests.test_build` (3 tests PASS); `~/Desktop/Research/wbr-lab-ops/.venv/bin/python -m sim.wbr_model.build sim/wbr_model/examples/assumed.yaml /tmp/wbr-c1-t25.xml` (compiled and wrote XML).
- Limits: example values remain illustrative ASSUMED data; report assembly scope is unresolved; no CAD calibration or five-bar closed-loop validation. No commit made per ticket.
