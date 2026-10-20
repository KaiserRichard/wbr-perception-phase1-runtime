# Parameter sources for the ASSUMED reduced WBR

Audited 2026-10-20. **No physical parameter is identified for the owner's future
robot, and no model/PPO setting changes here.** Current values below come from
[assumed_planar.json][plant] and [assumed_actuator_noise.json][noise] at lab
revision `6cae11df1ad4bfc756752adaf4aeeff72fe3e836`; assembly/axis meanings follow
[the implemented plant][implementation] and [LQR_RL_GUIDE.md](LQR_RL_GUIDE.md).
COM means center of mass; pitch is about the model's lateral axis. Wheel/leg
mass and inertia lumps and both torque inputs aggregate the two sides. Body mass
is the whole body assembly; none of these values is a per-side quantity.

Evidence labels are separate: **ASSUMED** = illustrative current setting;
**SOURCE CONSTANT** = implemented number, without measurement provenance;
**SUPPLIER SPEC** = a named component/revision's published specification;
**DERIVED** = calculation under stated shape/partition assumptions;
**UNKNOWN** = no supported mapping/value. DM links pin the requested DM-jump
commit `6855ef8c6da20246251cfd473467c04112bf800f` (DM). The manufacturer example
(ME) pins dmBots/wheel-legged `a6613d4084d354aee9967d14f69156f0084ec8eb`.
ME's SI units are interpreted from its dynamics; the inspected MATLAB text
supplies no mass-property measurement receipt. It is a separate reference model,
not a verified generator of DM's gains. DM part names do not establish exact
hardware versions or the owner's bill of materials (BOM).

| Parameter: current value, unit and assembly definition | Current provenance | Better available primary evidence, pinned revision/date | Applicability and unresolved uncertainty |
| --- | --- | --- | --- |
| Body mass `body_mass`: **2.0 kg**, lump rotating with absolute body pitch; actual part membership undefined | **ASSUMED** | **SOURCE CONSTANT:** ME [`M1=1.44` kg, labelled body mass][me]. DM [`Mg=17.658` N][mg] is a force-compensation constant. | ME does not establish our combined body assembly. DM uses `Mg` in [both][right-force] [legs][left-force]; it cannot establish body/total mass or a mass split. Owner's body mass: **UNKNOWN**. |
| Body COM `body_com`: **0.06 m above hip**, along body axis | **ASSUMED** | **SOURCE CONSTANT:** ME [`l1=0.011` m, body COM-to-pivot distance][me]. | ME's angle/sign convention and assembly differ; no matched battery, electronics, camera or motor placement. The owner's body COM and any fore/aft offset: **UNKNOWN**. |
| Leg mass `leg_mass`: **0.5 kg**, both legs replaced by one rigid equivalent leg | **ASSUMED** | **SOURCE CONSTANT:** ME [`mp1=0.045` kg, labelled rod mass][me]. **SUPPLIER SPEC:** J4310 V1.1 manual v1.3, **2026-09-14**, p.7: approximately **306 g per motor** ([pinned manufacturer PDF][joint-manual]). | A rod-model mass is not two complete five-bars. Motor mass cannot be assigned to this leg lump without mounting/rotating-part definitions. Owner's links, bearings, fasteners and leg mass: **UNKNOWN**. |
| Leg COM `leg_com`: **0.08 m above axle**, along equivalent leg | **ASSUMED** midpoint choice | **SOURCE CONSTANT:** ME [`L1=LM1=leg_length/2`][me]; DM [VMC geometry][vmc] contains lengths/kinematics, no link mass properties. | A geometric midpoint is not a mass COM. Actual distributed-link COM depends on configuration and part masses. Equivalent leg COM: **UNKNOWN**. |
| Wheel mass `wheel_mass`: **0.6 kg**, translating wheel/axle pair lump | **ASSUMED** | **SOURCE CONSTANT:** ME [`mw1=0.6` kg][me] (comments also call it rotor mass). **SUPPLIER SPEC:** H6215 manual v1.0, cover **2024-05-21**, p.12: approximately **360 g per motor** ([pinned PDF][wheel-manual]). | DM [names DM6215 wheel motors][driver]; exact hardware revision and owner's choice are unconfirmed. Complete motor mass does not specify rotating rotor/tire mass or our axle lump. Pair assembly mass: **UNKNOWN**. |
| Axle-to-hip `leg_length`: **0.16 m**, fixed equivalent leg | **ASSUMED** | **SOURCE CONSTANTS:** DM [five-bar][vmc] `l1=l4=0.075`, `l2=l3=0.14`, pivot spacing `l5=0.08` **m**; [setpoint clamps][leg-command] **0.060–0.21 m**. | These dimensions are inventoried but unused in the current rigid leg. Command limits are not measured reachable geometry. DM's `L0` is axle-to-base-midpoint distance; that midpoint's mapping to our hip is unverified. |
| Rolling radius `wheel_radius`: **0.0603 m**, ideal no-slip radius | **SOURCE CONSTANT**, config says SOURCE-SUPPORTED | DM [observer, lines 74/78][observer] multiplies angular rate by **0.0603 m**. H6215 manual p.12 lists motor outer diameter **68 mm** ([supplier][wheel-manual]). | Motor envelope is not tire rolling diameter. Tire, load and effective rolling radius on the owner's robot: **UNKNOWN**; this remains source-supported rather than measured. |
| `wheel_inertia`, `leg_inertia`, `body_inertia`: **0.0011, 0.0012, 0.018 kg·m²** respectively; combined rolling-axis inertia, equivalent-leg COM pitch inertia, body COM pitch inertia | All **ASSUMED** | **DERIVED in source:** ME [lines 24–26][me] uses a solid-disk wheel expression and rectangular-body/rod inertia expressions. Manufacturer motor masses above are **SUPPLIER SPECS**, not assembly inertia tensors. | ME's shape formulas do not validate rotor, tire, linkage or body inertia. Our wheel rolling energy is retained as `I_w/r²` armature. About-axle/hip inertias cannot replace COM inertias without axis transforms. All matching physical inertias: **UNKNOWN**. |
| Wheel input cap `wheel_torque_limit`: **±2 N·m for pair** | **ASSUMED** aggregate cap | **SOURCE CONSTANT:** DM clamps [right][right-clamp] / [left][left-clamp] wheel to **±2 N·m each**. **SUPPLIER SPEC:** H6215 manual p.12: **1 N·m rated, 2 N·m peak**, **24 V** ([PDF][wheel-manual]). | Equal numeric values have different aggregation. Peak rating is not a continuous pair limit; actual voltage, speed, thermal/current derating and tire transmission remain **UNKNOWN**. |
| Hip input cap `hip_torque_limit`: **±4 N·m for pair**, body-versus-leg virtual torque | **ASSUMED**; no five-bar actuator mapping | **SOURCE CONSTANT:** DM clamps [each joint][right-clamp] to **±7 N·m** after [VMC mapping][mapping]. **SUPPLIER SPEC:** J4310 V1.1 manual p.7: **3 N·m rated, 7 N·m peak** ([PDF][joint-manual]). | Joint limits cannot be summed into a constant virtual-hip limit: Jacobian and simultaneous axial force matter. [Protocol ranges][driver] **±10 joint / ±18 wheel N·m** are encoding ranges, not capabilities. Physical aggregate hip limit: **UNKNOWN**. |
| Control period **2 ms**; transport delay **2 ms default**, **2/3/4/5 ms** experiment | **ASSUMED**, synchronous simulation | **SOURCE CONSTANTS:** DM [chassis loop][right-timing] spaces commands with three `osDelay(CHASSR_TIME)` calls; `CHASSR_TIME=1`; [VMC call][vmc-timing] explicitly uses **0.003 s**. | Source scheduling intent does not measure sensor-to-torque latency, jitter or CAN delivery. It does not identify our delay values. Actual timing: **UNKNOWN**. |
| Wheel/hip torque time constants: **5 ms each**, first-order lag | **ASSUMED** | [H6215 manual][wheel-manual], pp.3–4 describes torque/current-loop operation; neither that description nor [DM torque sending][right-timing] identifies an assembly step response. | Torque bandwidth depends on motor/controller/load and operating point; an electrical constant or CAN bitrate is insufficient. Matching lag/order: **UNKNOWN**. |
| Body pitch noise SD **0.1°**, pitch-rate SD **0.01 rad/s**; independent zero-bias Gaussian samples at **500 Hz**; other four state coordinates ideal | **ASSUMED** sensor/estimator model | DM [reads BMI088 and runs Mahony][ins]. **SUPPLIER SPEC:** Bosch BMI088 datasheet rev. **1.9, 2024-01-05**, p.10: gyro output noise **0.1°/s RMS at 47 Hz bandwidth**, with **0.014°/s/√Hz** ([PDF][bosch]). | Raw gyro RMS/density is not fused pitch SD or IID noise at our rate. Mounting, bandwidth, bias, vibration, estimator delay/correlation and owner's sensor are **UNKNOWN**. This is the body IMU, separate from camera IMU data. |
| Gravity `gravity`: **9.81 m/s²**, uniform world −z | **ASSUMED** environment setting | ME [dynamics substitutions][me-gravity] use **9.8 m/s²**, another source-model choice. | Neither identifies local gravity; no precision gravity claim is needed or made. |

Mapping requires **computer-aided design (CAD), BOM and an assembly definition**.
DM's [pinned tree][dm-tree] has no matched CAD/BOM or link mass-property
report in the inspected paths; its [shaft notes][shaft] are general analysis.
The manufacturer [reference repository][manufacturer-tree] has separate printed
and machined variants, including CAD/BOM paths; only its tree and small MATLAB
text were inspected, not those assemblies. Their existence does not establish
the owner's design or a mass/COM estimate.

Five-bar pivot lengths locate joints, not material. Missing cross-sections,
densities, hardware, motor housing/rotor ownership and operating pose prevent a
mass-weighted COM or parallel-axis inertia calculation for our body/leg/wheel
partition. Even with those inputs, a changing linkage's kinetic energy need not
match one rigid equivalent leg over its motion. Supplier component weights
therefore remain components, and the source-model constants remain reference
choices. **No replacement physical point estimate or range is established.**
LQR gains do not identify mass/COM without the original model/design conventions;
the existing [Claude mass sweeps][claude] test sensitivity, not identification.
This audit does not alter the ASSUMED-model comparison or implement a research plan.

[plant]: https://github.com/KaiserRichard/wbr-perception-phase1-runtime/blob/6cae11df1ad4bfc756752adaf4aeeff72fe3e836/sim/configs/assumed_planar.json
[noise]: https://github.com/KaiserRichard/wbr-perception-phase1-runtime/blob/6cae11df1ad4bfc756752adaf4aeeff72fe3e836/sim/configs/assumed_actuator_noise.json
[implementation]: https://github.com/KaiserRichard/wbr-perception-phase1-runtime/blob/6cae11df1ad4bfc756752adaf4aeeff72fe3e836/sim/planar.py#L76-L126
[me]: https://github.com/dmBots/wheel-legged/blob/a6613d4084d354aee9967d14f69156f0084ec8eb/%E7%A1%AC%E4%BB%B6/%E6%89%93%E5%8D%B0%E4%BB%B6%E7%89%88/%E4%BB%BF%E7%9C%9F/simulation/get_k_length.m#L3-L35
[me-gravity]: https://github.com/dmBots/wheel-legged/blob/a6613d4084d354aee9967d14f69156f0084ec8eb/%E7%A1%AC%E4%BB%B6/%E6%89%93%E5%8D%B0%E4%BB%B6%E7%89%88/%E4%BB%BF%E7%9C%9F/simulation/get_k_length.m#L43-L47
[mg]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/chassisR_task.h#L52
[right-force]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/chassisR_task.c#L342
[left-force]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/chassisL_task.c#L240
[vmc]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/Algorithm/VMC/VMC_calc.c#L24-L71
[leg-command]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/ps2_task.c#L271-L280
[observer]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/observe_task.c#L72-L78
[right-clamp]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/chassisR_task.c#L211-L249
[left-clamp]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/chassisL_task.c#L156-L194
[mapping]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/Algorithm/VMC/VMC_calc.c#L160-L175
[driver]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/Devices/DM_Motor/dm4310_drv.h#L33-L55
[right-timing]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/chassisR_task.c#L55-L84
[vmc-timing]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/chassisR_task.c#L182
[ins]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/User/APP/INS_task.c#L68-L91
[joint-manual]: https://github.com/dmBots/DM-J4310-2EC/blob/2da08d236aa06743f85cde409811c005fbae0d5c/manual/DM-J4310-2EC%20V1.1%20Geared%20Motor%20User%20Manual%20V1.3%202026-09-14.pdf#page=7
[wheel-manual]: https://github.com/dmBots/DM-H6215/blob/c250cf84c27cb49c11a7be6c741599280352c717/manual/DM-H6215%E8%BD%AE%E6%AF%82%E7%94%B5%E6%9C%BA%E8%AF%B4%E6%98%8E%E4%B9%A6V1.0-20240607.pdf#page=12
[bosch]: https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi088-ds001.pdf#page=10
[dm-tree]: https://github.com/nguyenbinh-shark/DM-jump/tree/6855ef8c6da20246251cfd473467c04112bf800f
[shaft]: https://github.com/nguyenbinh-shark/DM-jump/blob/6855ef8c6da20246251cfd473467c04112bf800f/docs/mechanical/shaft_analysis_notes.md
[manufacturer-tree]: https://github.com/dmBots/wheel-legged/tree/a6613d4084d354aee9967d14f69156f0084ec8eb
[claude]: https://github.com/KaiserRichard/wbr-perception-phase1-runtime/blob/6cae11df1ad4bfc756752adaf4aeeff72fe3e836/ops/worklog/reviews/2026-10-20-lqr-mujoco.md#claude-review
