# DM-jump firmware and documentation

**Pinned primary source.** [nguyenbinh-shark/DM-jump at
6855ef8c6da20246251cfd473467c04112bf800f](https://github.com/nguyenbinh-shark/DM-jump/tree/6855ef8c6da20246251cfd473467c04112bf800f),
commit dated 2026-09-12 in the repository audit. The pinned [LICENSE](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/LICENSE)
is MIT; retain copyright/permission notices when redistributing substantial
portions. This is source-code evidence, not proof the lab robot runs this
revision. Its flashed revision is unconfirmed. The firmware snapshot and
documentation are public; public source does not establish the hardware's
physical parameter values or reproduce the controller's original synthesis.

## What the source implements

The controller folder is not the active chassis balance controller in this
snapshot. Application call paths lead through the [right](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/chassisR_task.c)
and [left chassis tasks](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/chassisL_task.c),
[VMC implementation](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/Algorithm/VMC/VMC_calc.c),
and a separate [PID module](https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/Algorithm/PID/pid.c). The source flow is: BMI088 attitude sensing and
Mahony inertial estimation; wheel/leg kinematics and acceleration into a
velocity Kalman filter and integrated position; independent left/right six
state feedback; virtual force/hip moment into a five-bar virtual model control
(VMC) Jacobian; then joint/wheel torque clamping and staggered CAN commands.

For each side, the six feedback errors cover virtual-leg angle/rate, filtered
position/speed, body pitch, and gyro rate, with mirrored signs on the left.
Twelve gains are evaluated as cubic functions of each side's leg length:
\(K_i(L)=a_{i3}L^3+a_{i2}L^2+a_{i1}L+a_{i0}\). Wheel and virtual-hip outputs
are dot products with those scheduled gains. The coefficients are source facts;
the plant, weighting matrices, design period, fitting procedure, and valid
length interval used to generate them are not recovered. Therefore one can
reproduce the implemented feedback map from source, but not claim to reproduce
the original optimal-control derivation.

## Evidence and boundaries

**Source-supported values, not independent physical measurements:** wheel
radius 0.0603 m in the observer; five-bar link constants; software torque
clamps of +/-2 N m per wheel and +/-7 N m per joint; nominal 3 ms observer/VMC
step; and three 1 ms RTOS delays in each chassis loop. The latter imply an
intended approximately 333 Hz per-side cadence with staggered commands, not a
measured control frequency or latency. Comments, README values, configured RTOS
ticks, and executed elapsed-time behavior do not all agree; actual period,
jitter, synchronized state age, and flashed code remain unknown.

Do not infer mass from a gravity-compensation constant, motor capability from
protocol encoding ranges, or stable hardware performance from a source review.
The current lab model is an assumed reduced model, not a DM-jump reproduction.
Its limitations include fixed leg length, idealized contact, and unknown real
mass/COM/inertia and actuator dynamics. The owner-only
`sim/parity/student.py::gain_schedule` exercise is intentionally not solved or
duplicated here. Use the pinned links to inspect source; this note copies no
firmware implementation.

