# Manifest driven WBR model

Run `python -m sim.wbr_model.build manifest.yaml out.xml` from the repository
root. The builder validates the manifest, compiles the generated MuJoCo XML, and
writes the output only after compilation succeeds. Install
`sim/wbr_model/requirements.txt` for full YAML support. The project's MuJoCo-only
environment also supports the documented v1 mapping and flow-value subset with
a standard-library fallback. `examples/assumed.yaml` is runnable, not calibrated.

## Model and schema

Version 1 is a documented reduction: base pitch/translation, an equivalent leg
length slider on each side, and one rolling wheel per side. It retains `l1`–`l5`
in generated XML metadata but does not model the five-bar closed loops, their
individual rods, rod masses/COM/inertias, or motor-to-linkage mapping. Rigid body
inertial properties come only from the manifest. Box, capsule, and cylinder
collision shapes approximate the assemblies; their dimensions are also manifest
values. Changing supported CAD values requires YAML edits only.

Every scalar, vector, and inertia tensor entry has `value`, SI `unit`, and
`source`. Allowed tags are exactly `team_report`, `CAD`, and `ASSUMED`. Report
provenance does not mean a value was measured, and unresolved interpretation
must remain visibly ASSUMED. COM is `[x,y,z]` in metres in each body's local
frame. The symmetric full inertia tensor is `[Ixx,Iyy,Izz,Ixy,Ixz,Iyz]` in
kg m², about that COM in the same local axes. Geometry supplies `l1`–`l5`, wheel
radius/track/width, link radius, and base half-size. Hip angle and leg extension
limits are explicit. Actuator torque and force caps are per-side output limits.

The validator checks finite values and units, source tags, positive-definite
inertia, principal-moment triangle inequalities, positive dimensions and
actuator limits, ordered joint limits, and
`total_robot = base + 2*each_leg + 2*each_wheel`. `each_leg` and `each_wheel`
mean per side. See [examples/assumed.yaml](examples/assumed.yaml) for the full
schema. Its mass allocation and tensors are illustrative ASSUMED values where
the source report does not resolve assembly ownership.

## Numbers to request from the CAD/mechanical team

Ask for one revisioned export and these exact items:

1. **Assembly membership and mass accounting:** robot total and separate base,
   left/right five-bar mechanisms, left/right wheels, motors/rotors, battery,
   electronics, bearings, fasteners, tires, and axles. State whether each report
   mass is per part, per side, or a pair, and ensure no part is counted twice.
   Give each mass in kg.
2. **For every retained rigid body:** mass in kg; COM `[x,y,z]` in m; full
   symmetric inertia `[Ixx,Iyy,Izz,Ixy,Ixz,Iyz]` in kg m² about that COM; and
   coordinate frame/axis convention. Include the base, each of the four rods
   on both mechanisms, each wheel, and any motor/housing parts to model as
   separate bodies. Export tensors in the intended assembled body frame or give
   transforms to rotate them.
3. **Linkage geometry:** pivot-center distances `l1` through `l5` for left and
   right sides in m, wheel radius (including loaded effective radius if
   available), wheel track, axle and hip locations, and assembled reference
   pose/configuration.
4. **Mechanical limits:** minimum and maximum angle in rad or extension in m
   for every motor and linkage joint. Identify hard stops versus software
   limits.
5. **Actuator data:** continuous and peak torque at motor shaft and joint/output
   in N m, peak duration, gear ratio and efficiency; for a linear actuator,
   force in N and stroke limits in m. Include signs and motor-coordinate to
   five-bar-output mapping.

`params_manifest_src.yaml` reports candidate base/leg/wheel masses, `l1`–`l5`,
and wheel radius, but assembly membership is unresolved and CAD inertia tensors
are null. Its scalar inertias are explicitly ASSUMED. Do not split rod masses,
duplicate pair masses, or promote those scalar inertias to CAD values. The
manifest is provenance, not directly executable input until the team resolves
the missing fields and mappings.

## Build and headless check

```sh
python -m sim.wbr_model.build sim/wbr_model/examples/assumed.yaml /tmp/wbr.xml
python -m unittest sim.wbr_model.tests.test_build
```

The headless test loads the MJCF in MuJoCo and advances 1000 steps, checking
finite position, velocity, and acceleration arrays. Passing means this assumed
example compiles and remains numerically finite for that short free simulation;
it does not validate CAD, five-bar kinematics, stability, contact fidelity, or
hardware capability.
