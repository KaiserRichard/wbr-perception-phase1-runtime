# Simulation and control teaching workspace

Approved sequence: compiled DM-jump C/Python parity, reduced planar six-state
model, matched LQR, then an RL comparison. A full planar five-bar MuJoCo model
with virtual model control follows the reduced stage. The four-state proposal
is archived. All work is simulation only; no firmware or motor deployment.

Start with [milestone 1](parity/README.md). No dynamics model, linearization,
LQR synthesis or RL training is implemented yet. Physical mass, center of mass,
inertia and actuator response remain UNKNOWN. Obtain CAD/BOM/specification
estimates in parallel; unavailable hardware does not block teaching simulations.
Every future assumed parameter must have units, an ASSUMED label and provenance
in one replaceable configuration file. Mass sweeps are sensitivity studies.

## Teaching ownership

The owner writes the Python gain schedule, A/B matrices, LQR solver call and
reward function. Agents supply TODO skeletons/tests and review the owner's code;
they do not complete those core functions unless asked. Agents handle build,
simulation scaffolding, plotting and logging. Before each milestone, explain
what/why/key equation in fewer than ten lines with a primary source; afterward,
ask two understanding questions and log the milestone and pending answers.

Every documentation change is recorded in `ops/worklog/DOCUMENTATION_LOG.md`.
Controller code/config changes require Claude review before merging. Host
numerical parity is neither a balancing result nor sim-to-real validation.
