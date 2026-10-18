# T26 interface findings

No blocking interface mismatch was found in the exercised path. The existing
tools accept a standard-shaped SQLite `.db3` with hand-written CDR headers and
payloads; the DB3 exporter additionally requires 640×480 MONO8 images, so the
test uses full-sized messages. Its exported metadata correctly labels the
driver IMU combine method `UNKNOWN` when only separate gyro and accel streams
exist. The EuRoC accuracy evaluator accepts the fake `f_*.txt` trajectory,
matching EuRoC ground-truth CSV, and exported `times_ns.txt`. The perception
converter output is accepted by the existing sender and supervisor model when
transported over a PTY.

No tests are marked `expectedFailure`; there is no tool defect to report.
Synthetic results remain tooling evidence and do not establish any physical
clock, sensor, estimator, storage, link, or safety behavior.
