# T26 rehearsal report

## Built

Added `test_rehearsal.py`, a synthetic SQLite/hand-written CDR data generator,
the test-only `config.json`, a Makefile test target, and this directory's
README/FINDINGS. The end-to-end test invokes the existing rosbag qualifier,
stamp drift analyzer, DB3-to-EuRoC exporter and qualifier, accuracy evaluator,
health converter, sender, and supervisor model without editing those tools.

The synthetic fixture uses two 640×480 MONO8 image topics at 30 Hz and
independent gyro/accel topics at 200 Hz over a two second interval. It injects
1200 ppm affine receive-clock drift and deterministic 0.025 m per-axis
trajectory noise. The test asserts drift and ATE recovery against configured
tolerances and checks supervisor `HOLD`/`FRESH` behavior. These values are
ASSUMED synthetic inputs, not measured properties.

## Tests

Run with `make -C tests/e2e_rehearsal test`. Complete output is saved in
`tests/last-run.log`. The suite asserts PASS for the nominal pipeline, plus
FAIL and BLOCKED results from mutated/missing EuRoC export fixtures. It also
checks result-status precedence. The full CDR bag is generated in a temporary
directory and deleted after the run. No physical `.db3` fixture was found in
the shared experiments checkout.

## Not verified and risks

- No hardware, ROS graph, camera, UART, or STM32 firmware was used.
- Synthetic CDR shape is limited to fields read by these tools; it is not a
  complete ROS distribution serialization conformance test.
- The two second full-resolution fixture takes around 30–40 seconds on this
  Mac because full-sized image messages are required by the existing exporter.
- `FRESH` assumes an explicit synthetic clock exchange and independent
  `primary_fresh=True`; neither is evidence of a qualified live mapping or
  primary estimator.
- A fixture PASS demonstrates interface and arithmetic consistency only; it
  does not pass a sensor or hardware gate.

Proposed commit message: `test: add synthetic end-to-end toolchain rehearsal`
