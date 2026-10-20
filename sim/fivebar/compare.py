"""Fixed-length comparison with the unchanged reduced plant.

Default: one quick matrix snapshot. --run-dynamics explicitly enables the
queued integration/refinement experiment. No training or policy is loaded.
"""

import argparse
import json
import math
from pathlib import Path

import mujoco
import numpy as np

from sim.planar import Plant as ReducedPlant, TO_JOINT
from .geometry import GeometryError, vector
from .model import Plant


def full_mass(model, data):
    mass = np.empty((model.nv, model.nv))
    mujoco.mj_fullM(model, mass, data.qM)
    return mass


class FixedLength:
    """Exact geometric length constraint for comparing mechanics, without PD.

    The XML keeps length free. Here q_tree=f(x,theta,phi,L_fixed), so T=df/dq
    eliminates both ankle-loop and fixed-length reaction forces. This compares
    assumed rigid-body mechanics without soft-equality stabilization error.
    Finite differences remain a numerical approximation, refined by the CLI.
    """

    def __init__(self, plant, epsilon=1e-6):
        self.plant = plant
        self.length = plant.cfg['physics']['leg_length']['value']
        if not math.isfinite(epsilon) or epsilon <= 0:
            raise ValueError('Expected positive finite projection epsilon')
        self.epsilon = epsilon

    def terms(self, state, control):
        state, control = vector(state, 6), vector(control, 2)
        q, v = state[:3], state[3:]
        coordinates = np.r_[q, self.length]
        p = self.plant
        tangent = p.tangent(coordinates, self.epsilon)[:, :3]
        data = p.data(coordinates)
        data.qvel[:] = tangent @ v
        data.ctrl[:] = p.controls(coordinates, *control)
        mujoco.mj_forward(p.model, data)
        mass = full_mass(p.model, data)
        # Directional second derivative d²f(q+t*v)/dt², including all passive
        # joint curvature; omitting this term corrupts nonzero-velocity tests.
        h = math.sqrt(self.epsilon)/max(1., float(np.linalg.norm(v)))
        dv = np.r_[h*v, 0.]
        curvature = (p.tree_position(coordinates+dv)-2*data.qpos+
                     p.tree_position(coordinates-dv))/h**2
        return (tangent.T@mass@tangent,
                tangent.T@(data.qfrc_bias+mass@curvature),
                tangent.T@data.qfrc_actuator)

    def derivative(self, state, control):
        mass, bias, force = self.terms(state, control)
        return np.r_[np.asarray(state)[3:], np.linalg.solve(mass, force-bias)]


def snapshot(cfg, epsilon=1e-6):
    full, reduced = Plant(cfg), ReducedPlant(cfg)
    fixed = FixedLength(full, epsilon)
    state = np.array([0., .08, -.05, 0., 0., 0.])
    mass, bias, _ = fixed.terms(state, [0., 0.])
    r = reduced.data(state)
    reduced_mass = TO_JOINT.T@full_mass(reduced.model, r)@TO_JOINT
    reduced_bias = TO_JOINT.T@r.qfrc_bias
    full_inputs = np.column_stack([fixed.terms(state, u)[2] for u in np.eye(2)])
    reduced_inputs = []
    for u in np.eye(2):
        reduced.forward(r, u)
        reduced_inputs.append(TO_JOINT.T@r.qfrc_actuator)
    reduced_inputs = np.column_stack(reduced_inputs)
    coordinates = np.r_[state[:3], fixed.length]
    f = full.data(coordinates)
    return {'status': 'CALCULATED snapshot; no dynamics equivalence assertion',
            'coordinates': ['x_m', 'theta_rad', 'phi_rad'],
            'input_order': ['wheel_pair_Nm', 'virtual_hip_pair_Nm'],
            'mass_units': [['kg', 'kg m', 'kg m'], ['kg m', 'kg m^2', 'kg m^2'],
                           ['kg m', 'kg m^2', 'kg m^2']],
            'bias_units': ['N', 'N m', 'N m'],
            'state': state.tolist(), 'projection_epsilon': epsilon,
            'closure_m': full.closure_error(f),
            'hip_position_error_m': (f.xpos[full.model.body('chassis').id]-
                                     r.xpos[reduced.body_id]).tolist(),
            'fivebar_mass': mass.tolist(), 'reduced_mass': reduced_mass.tolist(),
            'mass_difference': (mass-reduced_mass).tolist(),
            'fivebar_bias': bias.tolist(), 'reduced_bias': reduced_bias.tolist(),
            'fivebar_input_map': full_inputs.tolist(),
            'reduced_input_map': reduced_inputs.tolist(),
            'input_difference': (full_inputs-reduced_inputs).tolist()}


def rk4(function, state, control, dt):
    a = function(state, control)
    b = function(state+dt*a/2, control)
    c = function(state+dt*b/2, control)
    d = function(state+dt*c, control)
    return state+dt*(a+2*b+2*c+d)/6


def rollout(cfg, dt, duration, epsilon):
    fixed = FixedLength(Plant(cfg), epsilon)
    reduced = ReducedPlant(cfg)
    state_f = np.array([0., .02, -.015, 0., 0., 0.])
    state_r = state_f.copy()
    maximum = np.zeros(6)
    completed = 0
    status = 'duration_completed'
    failure = None
    nsteps = round(duration/dt)
    for step in range(nsteps):
        # Explicit bounded open-loop inputs: first 0.1 s pulse, then zero.
        control = np.array([.02, -.05]) if step*dt < .1-1e-12 else np.zeros(2)
        try:
            next_f = rk4(fixed.derivative, state_f, control, dt)
            next_r = rk4(reduced.derivative, state_r, control, dt)
        except (GeometryError, np.linalg.LinAlgError) as exc:
            status, failure = 'workspace_or_numeric_stop', str(exc)
            break
        if not np.all(np.isfinite(np.r_[next_f, next_r])):
            status, failure = 'nonfinite_stop', 'Nonfinite candidate state'
            break
        state_f, state_r = next_f, next_r
        completed = step+1
        maximum = np.maximum(maximum, np.abs(state_f-state_r))
        if max(abs(state_f[1]), abs(state_f[2]), abs(state_r[1]), abs(state_r[2])) >= math.pi/4:
            status = '45_degree_stop'
            break
    return {'dt_s': dt, 'projection_epsilon': epsilon, 'status': status,
            'failure': failure, 'completed_steps': completed, 'time_s': completed*dt,
            'state_order': ['x_m', 'theta_rad', 'phi_rad', 'xdot_m_s', 'thetadot_rad_s', 'phidot_rad_s'],
            'max_abs_state_difference': maximum.tolist(),
            'final_fivebar_state': state_f.tolist(), 'final_reduced_state': state_r.tolist()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dynamics', action='store_true')
    parser.add_argument('--duration', type=float, default=5.)
    parser.add_argument('--timesteps', type=float, nargs='+', default=[.001, .0005, .00025])
    parser.add_argument('--epsilons', type=float, nargs='+', default=[1e-5, 3e-6, 1e-6])
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    values = [args.duration, *args.timesteps, *args.epsilons]
    if any(not math.isfinite(x) or x <= 0 for x in values):
        parser.error('Duration, timesteps and epsilons must be finite and positive')
    if any(abs(args.duration/dt-round(args.duration/dt)) > 1e-8 or
           abs(.1/dt-round(.1/dt)) > 1e-8 for dt in args.timesteps):
        parser.error('Duration and 0.1 s pulse must align with every timestep')
    if args.output and args.output.exists():
        parser.error('Output already exists; preserve it and choose a new path')
    cfg = json.loads((Path(__file__).parents[1]/'configs/assumed_planar.json').read_text())
    report = {'label': 'ASSUMED separate mechanics; no RL, controller, contact or hardware validation',
              'snapshot': snapshot(cfg), 'dynamics_actually_run': args.run_dynamics,
              'dynamics': []}
    if args.run_dynamics:
        report['dynamics'] = [rollout(cfg, dt, args.duration, eps)
                              for eps in args.epsilons for dt in args.timesteps]
    result = json.dumps(report, indent=2, allow_nan=False)+'\n'
    if args.output:
        with args.output.open('x') as stream:
            stream.write(result)
    else:
        print(result, end='')


if __name__ == '__main__':
    main()
