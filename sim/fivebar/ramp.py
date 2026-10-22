"""One prescribed-length nonlinear fivebar experiment; no physical extension servo.

The accepted reduced fitted family is transferred to different assumed mechanics.
The frozen XML is constructed once. Controller feedback is measured six-state,
exact prescribed L, and its own nominal command-only torque/history estimate.
"""

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
import traceback

import mujoco
import numpy as np

from sim.augmented import lag_interval
from sim.gain_schedule.fitting import evaluate_polynomial
from sim.planar import INPUT_NAMES, STATE_NAMES
from .compare import full_mass
from .geometry import GeometryError, vector
from .model import Plant

DT = .002
TAU = np.array([.005, .005])
CAPS = np.array([2., 4.])
DURATION = 15.
RAMP_END = 10.


def length_profile(t):
    """C2 quintic: hold .12 to 2s, ramp for 8s, hold .20 after 10s."""
    if not math.isfinite(t) or t < 0:
        raise ValueError('Profile time must be finite and nonnegative')
    if t <= 2.:
        return .12, 0., 0.
    if t >= RAMP_END:
        return .20, 0., 0.
    s = (t - 2.) / 8.
    return (.12 + .08 * (10*s**3 - 15*s**4 + 6*s**5),
            .08/8 * (30*s**2 - 60*s**3 + 30*s**4),
            .08/64 * (60*s - 180*s**2 + 120*s**3))


def full_duration_reached(time_s):
    """Return a JSON-safe scalar acceptance flag for the requested protocol."""
    return bool(abs(float(time_s) - DURATION) < 1e-9)


class PrescribedLength:
    """Full 8x4 tangent and native unconstrained tree mass/bias/actuator force.

    Equality-constraint forces are excluded: the geometric projection already
    eliminates ankle closure. Only the final coordinate acceleration is imposed.
    """

    def __init__(self, plant, epsilon=1e-6, profile=length_profile):
        if not math.isfinite(epsilon) or epsilon <= 0:
            raise ValueError('Projection epsilon must be positive and finite')
        self.plant, self.epsilon, self.profile = plant, epsilon, profile
        self.data = mujoco.MjData(plant.model)

    def terms(self, t, state, control):
        state, control = vector(state, 6), vector(control, 2)
        length, speed, acceleration = self.profile(t)
        q4, v4 = np.r_[state[:3], length], np.r_[state[3:], speed]
        p, data = self.plant, self.data
        tangent = p.tangent(q4, self.epsilon)
        data.qpos[:] = p.tree_position(q4)
        data.qvel[:] = tangent @ v4
        data.ctrl[:] = p.controls(q4, *control, extension_N=0.)
        mujoco.mj_forward(p.model, data)
        mass = full_mass(p.model, data)
        # Identical directional finite differences to FixedLength, now with Ldot.
        h = math.sqrt(self.epsilon) / max(1., float(np.linalg.norm(v4)))
        curvature = (p.tree_position(q4+h*v4) - 2*data.qpos +
                     p.tree_position(q4-h*v4)) / h**2
        m4 = tangent.T @ mass @ tangent
        b4 = tangent.T @ (data.qfrc_bias + mass @ curvature)
        force4 = tangent.T @ data.qfrc_actuator
        if not np.all(np.isfinite(np.r_[m4.ravel(), b4, force4])):
            raise FloatingPointError('Nonfinite projected equations')
        if any(w.number for w in data.warning):
            raise FloatingPointError('MuJoCo warning during projected evaluation')
        return m4, b4, force4, acceleration

    def evaluate(self, t, state, control):
        m4, b4, force4, lddot = self.terms(t, state, control)
        qdd = np.linalg.solve(m4[:3, :3], force4[:3] - b4[:3] - m4[:3, 3]*lddot)
        extension = float(m4[3, :3] @ qdd + m4[3, 3]*lddot + b4[3] - force4[3])
        derivative = np.r_[np.asarray(state)[3:], qdd]
        if not np.all(np.isfinite(np.r_[derivative, extension])):
            raise FloatingPointError('Nonfinite derivative or extension force')
        return derivative, extension, self.plant.closure_error(self.data), self.data.ctrl.copy()

    def derivative(self, t, state, control):
        return self.evaluate(t, state, control)[0]


def mechanical_step(mechanics, t, state, mean_torque, h):
    """RK4 holds exact lag mean for h; profile uses each actual RK stage time.

    Returns sampled reactions and RK4 extension work, with no coordinate clamps.
    Mean-torque mechanical coupling is approximate and needs step refinement.
    """
    a = mechanics.evaluate(t, state, mean_torque)
    b = mechanics.evaluate(t+h/2, state+h*a[0]/2, mean_torque)
    c = mechanics.evaluate(t+h/2, state+h*b[0]/2, mean_torque)
    d = mechanics.evaluate(t+h, state+h*c[0], mean_torque)
    stages = (a, b, c, d)
    weights = np.array([1., 2., 2., 1.]) / 6
    speeds = np.array([mechanics.profile(v)[1] for v in (t, t+h/2, t+h/2, t+h)])
    forces = np.array([v[1] for v in stages])
    nxt = state + h * sum(w*v[0] for w, v in zip(weights, stages))
    if not np.all(np.isfinite(nxt)):
        raise FloatingPointError('Nonfinite RK4 candidate')
    return nxt, {'extension_mean_N': float(weights @ forces),
                 'extension_peak_abs_N': float(max(abs(forces))),
                 'extension_work_J': float(h * (weights @ (forces*speeds))),
                 'extension_absolute_work_J': float(h * (weights @ abs(forces*speeds))),
                 'closure_max_m': max(v[2] for v in stages),
                 'native_motor_peak_abs_Nm': np.max(abs(np.array([v[3] for v in stages])), axis=0)}


class Sensor:
    """Original two independent noise streams, cached once per control tick."""

    def __init__(self, seed=0):
        self.rngs = [np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(2)]
        self.tick, self.cached, self.noise = None, None, None

    def measure(self, tick, truth):
        if tick != self.tick:
            self.cached = vector(truth, 6).copy()
            self.noise = np.array([self.rngs[0].normal()*np.deg2rad(.1),
                                   self.rngs[1].normal()*.01])
            self.cached[[2, 5]] += self.noise
            self.tick = tick
        return self.cached.copy()


class Controller:
    """No plant/actual-torque access. Own nominal 2ms delay, 5ms lag, clipped u."""

    def __init__(self, fit):
        self.fit = fit
        self.estimate, self.previous = np.zeros(2), np.zeros(2)

    def tick(self, measured, length):
        observation = np.r_[vector(measured, 6), self.estimate, self.previous]
        gain = evaluate_polynomial(self.fit, length)
        if gain.shape != (2, 10):
            raise ValueError('Expected fitted 2x10 delayed gain')
        raw = -gain @ observation
        if not np.all(np.isfinite(raw)):
            raise FloatingPointError('Nonfinite controller output')
        clipped = np.clip(raw, -CAPS, CAPS)
        # Current interval sees u_(k-1); newly chosen u_k starts next tick.
        self.estimate = lag_interval(self.estimate, self.previous, TAU, DT)[0]
        self.previous = clipped.copy()
        return observation, raw, clipped


def read_schedule(path):
    schedule = json.loads(Path(path).read_text())
    regimes = [r for r in schedule['regimes'] if r['runtime']['delay_s'] == DT]
    if len(regimes) != 1:
        raise ValueError('Expected exactly one accepted 2ms regime')
    regime, cfg = regimes[0], schedule['reference_config']
    expected = [*STATE_NAMES, 'wheel_torque_estimate_Nm', 'hip_torque_estimate_Nm',
                'previous_1_wheel_command_Nm', 'previous_1_hip_command_Nm']
    runtime = regime['runtime']
    if (schedule.get('status') != 'COMPLETE' or regime['state_order'] != expected or
            regime['input_order'] != INPUT_NAMES or regime['fit']['domain_m'] != [.12, .20] or
            runtime['motor_time_constant_s'] != TAU.tolist() or
            runtime['body_angle_std_deg'] != .1 or runtime['body_gyro_std_rad_s'] != .01 or
            cfg['simulation']['dt_s'] != DT or
            [cfg['physics'][k]['value'] for k in ('wheel_torque_limit', 'hip_torque_limit')] != CAPS.tolist()):
        raise ValueError('Schedule does not match declared family/timing/noise/order/caps')
    evaluate_polynomial(regime['fit'], [.12, .20])
    return schedule, regime


def write_json(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def run(schedule, regime, out, *, mechanics_step=.001, epsilon=1e-6, duration=DURATION):
    """Stream one seed0 run. A short duration is explicitly an incomplete check."""
    cfg = schedule['reference_config']
    plant = Plant(cfg)  # Once only; inertias, reference poses and XML stay fixed.
    mechanics = PrescribedLength(plant, epsilon)
    controller, sensor = Controller(regime['fit']), Sensor(0)
    state = np.asarray(cfg['protocol']['initial_state'], float).copy()
    torque, previous = np.zeros(2), np.zeros(2)
    p = cfg['protocol']
    times, states = [0.], [state.copy()]
    closure, peak_extension, work, absolute_work = 0., 0., 0., 0.
    peak_motor, peak_torque, peak_command = np.zeros(3), np.zeros(2), np.zeros(2)
    saturation = np.zeros(2)
    failure, status, fall_time = None, 'duration_completed', None
    noise_hash = hashlib.sha256()
    integration_steps, t, tick = 0, 0., 0
    out.joinpath('model.xml').write_text(plant.xml)
    with (out/'control.csv').open('x', newline='') as cf, (out/'intervals.csv').open('x', newline='') as sf:
        controls, segments = csv.writer(cf), csv.writer(sf)
        controls.writerow(['time_s', *STATE_NAMES, *[f'measured_{n}' for n in STATE_NAMES],
                           'estimated_Tw_Nm', 'estimated_Th_Nm', 'previous_Tw_Nm', 'previous_Th_Nm',
                           'noise_body_rad', 'noise_gyro_rad_s', 'requested_Tw_Nm', 'requested_Th_Nm',
                           'clipped_Tw_Nm', 'clipped_Th_Nm', 'actual_Tw_Nm', 'actual_Th_Nm',
                           'L_m', 'Ldot_m_s', 'Lddot_m_s2'])
        segments.writerow(['time_s', 'dt_s', *[f'end_{n}' for n in STATE_NAMES],
                           'L_end_m', 'Ldot_end_m_s', 'Lddot_end_m_s2',
                           'previous_Tw_Nm', 'previous_Th_Nm', 'mean_Tw_Nm', 'mean_Th_Nm',
                           'start_Tw_Nm', 'start_Th_Nm', 'end_Tw_Nm', 'end_Th_Nm',
                           'extension_mean_N', 'extension_peak_abs_N', 'extension_work_J',
                           'cumulative_extension_work_J', 'extension_absolute_work_J', 'closure_max_m',
                           'native_wheel_peak_Nm', 'native_motor_A_peak_Nm', 'native_motor_E_peak_Nm'])
        try:
            for tick in range(round(duration/DT)+1):
                measured = sensor.measure(tick, state)
                noise_hash.update(np.asarray(sensor.noise, dtype='<f8').tobytes())
                obs, raw, clipped = controller.tick(measured, length_profile(t)[0])
                controls.writerow([t, *state, *obs, *sensor.noise, *raw, *clipped, *torque, *length_profile(t)])
                if tick == round(duration/DT):
                    break
                peak_command = np.maximum(peak_command, abs(clipped))
                saturation += (abs(raw-clipped) > 1e-12)*DT
                for sub in range(round(DT/mechanics_step)):
                    t = tick*DT + sub*mechanics_step
                    h = mechanics_step
                    tau1, mean, _ = lag_interval(torque, previous, TAU, h)
                    next_state, info = mechanical_step(mechanics, t, state, mean, h)
                    peak_torque = np.maximum(peak_torque, np.maximum(abs(torque), abs(tau1)))
                    peak_motor = np.maximum(peak_motor, info['native_motor_peak_abs_Nm'])
                    closure = max(closure, info['closure_max_m'])
                    peak_extension = max(peak_extension, info['extension_peak_abs_N'])
                    work += info['extension_work_J']
                    absolute_work += info['extension_absolute_work_J']
                    segments.writerow([t, h, *next_state, *length_profile(t+h), *previous, *mean,
                                       *torque, *tau1, info['extension_mean_N'], info['extension_peak_abs_N'],
                                       info['extension_work_J'], work, info['extension_absolute_work_J'],
                                       info['closure_max_m'], *info['native_motor_peak_abs_Nm']])
                    state, torque, t = next_state, tau1, t+h
                    integration_steps += 1
                    times.append(t)
                    states.append(state.copy())
                    if np.rad2deg(max(abs(state[1:3]))) >= p['fall_angle_deg']:
                        status, fall_time = 'physical_fall', t
                        break
                    if abs(state[0]) > p['max_displacement_m']:
                        status = 'displacement_stop'
                        break
                previous = clipped.copy()  # u_k may drive only the next interval.
                if status != 'duration_completed':
                    break
                if tick % 500 == 0:
                    cf.flush()
                    sf.flush()
                    print(f't={t:.3f}s L={length_profile(t)[0]:.6f}m', flush=True)
        except GeometryError as exc:
            status, failure = 'geometry_stop', str(exc)
            write_json(out/'failure.json', {'time_s': t, 'tick': tick, 'error': str(exc),
                                          'traceback': traceback.format_exc()})
        except Exception as exc:
            status, failure = 'numerical_or_execution_failure', str(exc)
            write_json(out/'failure.json', {'time_s': t, 'tick': tick, 'error': str(exc),
                                          'traceback': traceback.format_exc()})
    times, states = np.asarray(times), np.asarray(states)
    tolerance = np.asarray(p['state_abs_tolerance'])
    inside = np.all(abs(states) <= tolerance, axis=1)
    settled = np.logical_and.accumulate(inside[::-1])[::-1]
    candidates = np.flatnonzero(settled & (times >= RAMP_END-1e-10))
    recovery = float(times[candidates[0]]-RAMP_END) if len(candidates) else None
    full = full_duration_reached(times[-1])
    window = times >= DURATION-p['settle_window_s']-1e-10
    checks = {'full_duration': full, 'no_fall': fall_time is None,
              'displacement': bool(np.max(abs(states[:, 0])) <= p['max_displacement_m']),
              'finite_and_no_warning': status != 'numerical_or_execution_failure',
              'geometry': status != 'geometry_stop',
              'caps': bool(np.all(np.maximum(peak_command, peak_torque) <= CAPS+1e-12)),
              'held_final_window': bool(full and np.any(window) and np.all(inside[window])),
              'recovery_after_ramp_within_5s': bool(full and recovery is not None and recovery <= p['recovery_deadline_s'])}
    metrics = {'status': 'PASS' if all(checks.values()) else 'FAIL', 'stop_reason': status,
               'checks': checks, 'failure': failure, 'failed_checks': [k for k,v in checks.items() if not v],
               'seed': 0, 'duration_s': float(times[-1]), 'requested_duration_s': duration,
               'integration_steps': integration_steps, 'final_state': state.tolist(),
               'initial_state': states[0].tolist(), 'final_window_max_abs_error':
               np.max(abs(states[window]), axis=0).tolist() if np.any(window) else None,
               'peak_displacement_m': float(np.max(abs(states[:, 0]))),
               'peak_tilt_deg': float(np.rad2deg(np.max(abs(states[:, 1:3])))),
               'fall_time_s': fall_time, 'recovery_after_ramp_s': recovery,
               'sampled_closure_max_m': closure, 'extension_peak_abs_N': peak_extension,
               'extension_work_J': work, 'extension_absolute_work_J': absolute_work,
               'native_motor_peak_abs_Nm': peak_motor.tolist(), 'motor_feasibility': 'UNKNOWN',
               'peak_physical_torque_Nm': peak_torque.tolist(), 'peak_clipped_command_Nm': peak_command.tolist(),
               'saturation_duration_s': saturation.tolist(), 'noise_sha256_float64_le': noise_hash.hexdigest(),
               'acceptance_sampling': 'all mechanical substep endpoints; closure/reaction at RK4 stages',
               'extension': 'ideal prescribed coordinate; reaction/work, not a physical servo',
               'controller_feedback': 'noisy body angle/gyro, ideal other six-state entries, exact prescribed L; own nominal command-only observer'}
    write_json(out/'metrics.json', metrics)
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--schedule', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--mechanics-step', type=float, default=.001)
    parser.add_argument('--projection-epsilon', type=float, default=1e-6)
    parser.add_argument('--duration', type=float, default=DURATION,
                        help='Short diagnostic only; cannot PASS the 15s protocol')
    args = parser.parse_args()
    if (not all(math.isfinite(x) and x > 0 for x in
                [args.mechanics_step, args.projection_epsilon, args.duration]) or
            args.duration > DURATION or args.mechanics_step > DT or
            abs(DT/args.mechanics_step-round(DT/args.mechanics_step)) > 1e-9 or
            abs(args.duration/DT-round(args.duration/DT)) > 1e-9):
        parser.error('Positive finite settings; step divides 2ms, duration divides into ticks and is <=15s')
    args.out.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[2]
    started = time.monotonic()
    metadata = {'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
                'source_status': subprocess.check_output(['git', 'status', '--short'], cwd=root, text=True).strip(),
                'command': shlex.join([sys.executable, '-m', 'sim.fivebar.ramp', *sys.argv[1:]]),
                'cwd': str(root), 'seed': 0, 'schedule_path': str(args.schedule.resolve()),
                'mechanics_step_s': args.mechanics_step, 'projection_epsilon': args.projection_epsilon,
                'actual_delay_s': DT, 'actual_lag_s': TAU.tolist(), 'controller_period_s': DT,
                'caps_Nm': CAPS.tolist(), 'requested_duration_s': args.duration,
                'profile': 'hold .12 to2s; C2 quintic .12->.20 during2..10s; hold to15s; max Ldot .01875m/s',
                'model_transfer': 'accepted .12-.20 reduced fitted family transferred to ASSUMED nonlinear fivebar; different model from previous400; no hardware claim',
                'thread_environment': {k: os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS')},
                'versions': {'python': sys.version, 'numpy': np.__version__, 'mujoco': mujoco.__version__}}
    write_json(args.out/'execution-start.json', metadata)
    code = 2
    try:
        schedule, regime = read_schedule(args.schedule)
        write_json(args.out/'schedule.json', schedule)
        write_json(args.out/'config.json', schedule['reference_config'])
        metrics = run(schedule, regime, args.out, mechanics_step=args.mechanics_step,
                      epsilon=args.projection_epsilon, duration=args.duration)
        code = 0 if metrics['status'] == 'PASS' else (2 if metrics['stop_reason'] == 'numerical_or_execution_failure' else 1)
        print(json.dumps(metrics, indent=2), flush=True)
    except KeyboardInterrupt:
        code = 130
        (args.out/'error.txt').write_text('Interrupted by SIGINT/keyboard interrupt.\n')
        traceback.print_exc()
    except Exception:
        (args.out/'error.txt').write_text(traceback.format_exc())
        traceback.print_exc()
    finally:
        write_json(args.out/'execution.json', {**metadata, 'exit_code': code, 'elapsed_s': time.monotonic()-started})
    return code


if __name__ == '__main__':
    raise SystemExit(main())
