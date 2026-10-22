"""Twelve upright-start ramps, paired scheduled/frozen gains, ideal extension.

Reuses the accepted projection and control primitives without changing them.
Only the profile, study loop, diagnostics and receipts are new. Seed 0 only.
"""
import argparse
import csv
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

for _name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_name] = '1'

import numpy as np

from sim.augmented import lag_interval
from sim.gain_schedule.combined import attempt_directory, source_receipt, write_json
from sim.gain_schedule.stress import utc_now
from sim.planar import STATE_NAMES
from .geometry import GeometryError
from .model import Plant
from .ramp import CAPS, DT, TAU, Controller, PrescribedLength, Sensor, mechanical_step, read_schedule


@dataclass(frozen=True)
class Profile:
    initial_m: float
    final_m: float
    moving_s: float

    def __post_init__(self):
        if ({self.initial_m, self.final_m} != {.12, .20} or
                not math.isfinite(self.moving_s) or self.moving_s <= 0):
            raise ValueError('Expected .12/.20 endpoint ramp with positive finite duration')

    @property
    def end_s(self):
        return 2. + self.moving_s

    @property
    def duration_s(self):
        return self.end_s + 5.

    @property
    def max_abs_rate_m_s(self):
        return abs(self.final_m-self.initial_m)*1.875/self.moving_s

    def __call__(self, t):
        if not math.isfinite(t) or t < 0:
            raise ValueError('Finite nonnegative time required')
        if t <= 2.:
            return self.initial_m, 0., 0.
        if t >= self.end_s:
            return self.final_m, 0., 0.
        s, delta = (t-2.)/self.moving_s, self.final_m-self.initial_m
        return (self.initial_m+delta*(10*s**3-15*s**4+6*s**5),
                delta/self.moving_s*(30*s**2-60*s**3+30*s**4),
                delta/self.moving_s**2*(60*s-180*s**2+120*s**3))


def matrix():
    return [{'id': f'{direction}_{duration:g}s_{mode}', 'direction': direction,
             'profile': asdict(Profile(start, end, duration)), 'controller': mode, 'seed': 0}
            for direction, start, end in (('extend', .12, .20), ('retract', .20, .12))
            for duration in (8., 2., 1.) for mode in ('scheduled', 'frozen')]


class RequiredTorque(PrescribedLength):
    """Diagnostic conversion at the existing RK stages, no second physics solve.

    Fext enforces the prescribed fourth coordinate. Plant.controls maps that
    reaction AND the same-stage balance moment into A/E required torques.
    These diagnostics are not feedback or extra applied forces in the projection.
    """
    def __init__(self, *args, stage_writer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_writer = stage_writer
        self.peaks = [None, None]
        self.pair_peak = None

    def evaluate(self, t, state, control):
        derivative, extension, closure, balance = super().evaluate(t, state, control)
        q4 = np.r_[state[:3], self.profile(t)[0]]
        required = self.plant.controls(q4, *control, extension_N=extension)
        record = {'time_s': float(t), 'q4': q4.tolist(), 'balance_Tw_Th_Nm': control.tolist(),
                  'extension_N': extension, 'balance_only_A_E_Nm': balance[1:].tolist(),
                  'extension_only_A_E_Nm': (required-balance)[1:].tolist(),
                  'required_A_E_Nm': required[1:].tolist()}
        for j in range(2):
            if self.peaks[j] is None or abs(required[j+1]) > abs(self.peaks[j]['required_A_E_Nm'][j]):
                self.peaks[j] = record
        if self.pair_peak is None or sum(abs(required[1:])) > sum(abs(np.array(self.pair_peak['required_A_E_Nm']))):
            self.pair_peak = record
        if self.stage_writer is not None:
            self.stage_writer.writerow([t, *q4, *control, extension, *balance[1:], *required[1:]])
        # mechanical_step's maxima now refer to complete required joint torques.
        return derivative, extension, closure, required


def window_metrics(times, states, start, end):
    mask = (times >= start-1e-10) & (times <= end+1e-10)
    if not np.any(mask):
        return {'requested_start_s': start, 'requested_end_s': end, 'samples': 0, 'complete': False}
    t, s = times[mask], states[mask]
    return {'requested_start_s': start, 'requested_end_s': end,
            'first_sample_s': float(t[0]), 'last_sample_s': float(t[-1]), 'samples': len(t),
            'complete': bool(abs(t[0]-start)<1e-9 and abs(t[-1]-end)<1e-9),
            'leg_peak_abs_deg': float(np.rad2deg(max(abs(s[:, 1])))),
            'body_peak_abs_deg': float(np.rad2deg(max(abs(s[:, 2])))),
            'global_x_min_m': float(min(s[:, 0])), 'global_x_max_m': float(max(s[:, 0])),
            'global_x_peak_abs_m': float(max(abs(s[:, 0]))),
            'x_start_m': float(s[0, 0]), 'x_end_m': float(s[-1, 0]),
            'x_end_minus_start_m': float(s[-1, 0]-s[0, 0]),
            'x_change_from_window_start_peak_abs_m': float(max(abs(s[:, 0]-s[0, 0])))}


def run(schedule, regime, spec, out, *, h=.001, epsilon=1e-6):
    """One full declared run or explicit stop, with unchanged acceptance thresholds."""
    if h <= 0 or abs(DT/h-round(DT/h)) > 1e-9:
        raise ValueError('Mechanical step must divide 2ms')
    profile = Profile(**spec['profile'])
    cfg, mode = schedule['reference_config'], spec['controller']
    if mode not in ('scheduled', 'frozen'):
        raise ValueError('Unknown controller')
    plant, controller, sensor = Plant(cfg), Controller(regime['fit']), Sensor(spec['seed'])
    p = cfg['protocol']
    state, torque, previous = np.zeros(6), np.zeros(2), np.zeros(2)
    times, states = [0.], [state.copy()]
    t, steps = 0., 0
    closure = extension_peak = work = absolute_work = 0.
    peak_command, peak_torque, saturation, effort = [np.zeros(2) for _ in range(4)]
    stop, failure, execution_error = 'duration_completed', None, False
    noise_hash = hashlib.sha256()
    (out / 'model.xml').write_text(plant.xml)
    with (out/'control.csv').open('x', newline='') as cf, (out/'intervals.csv').open('x', newline='') as sf, (out/'stages.csv').open('x', newline='') as rf:
        controls, segments, stages = csv.writer(cf), csv.writer(sf), csv.writer(rf)
        controls.writerow(['time_s', *STATE_NAMES, *[f'measured_{n}' for n in STATE_NAMES],
                           'own_tau_w', 'own_tau_h', 'own_previous_w', 'own_previous_h',
                           'noise_body_rad', 'noise_gyro_rad_s', 'requested_Tw_Nm', 'requested_Th_Nm',
                           'clipped_Tw_Nm', 'clipped_Th_Nm', 'actual_Tw_Nm', 'actual_Th_Nm',
                           'actual_L_m', 'Ldot_m_s', 'Lddot_m_s2', 'gain_evaluation_L_m'])
        segments.writerow(['time_s', 'dt_s', *[f'end_{n}' for n in STATE_NAMES],
                           'L_end_m', 'Ldot_end_m_s', 'Lddot_end_m_s2',
                           'delayed_Tw_Nm', 'delayed_Th_Nm', 'mean_Tw_Nm', 'mean_Th_Nm',
                           'start_Tw_Nm', 'start_Th_Nm', 'end_Tw_Nm', 'end_Th_Nm',
                           'extension_mean_N', 'extension_peak_abs_N', 'extension_work_J',
                           'cumulative_extension_work_J', 'extension_absolute_work_J', 'closure_max_m',
                           'required_wheel_peak_Nm', 'required_motor_A_peak_Nm', 'required_motor_E_peak_Nm'])
        stages.writerow(['time_s', 'x_m', 'leg_rad', 'body_rad', 'L_m', 'Tw_Nm', 'Th_Nm',
                         'extension_N', 'balance_only_A_Nm', 'balance_only_E_Nm',
                         'required_A_Nm', 'required_E_Nm'])
        mechanics = RequiredTorque(plant, epsilon, profile=profile, stage_writer=stages)
        try:
            for tick in range(round(profile.duration_s/DT)+1):
                measured = sensor.measure(tick, state)
                noise_hash.update(np.asarray(sensor.noise, dtype='<f8').tobytes())
                actual_length = profile(t)[0]
                gain_length = actual_length if mode == 'scheduled' else profile.initial_m
                obs, raw, clipped = controller.tick(measured, gain_length)
                # Reporting only: preserve profile/controller/physics times above.
                controls.writerow([tick*DT, *state, *obs, *sensor.noise, *raw, *clipped, *torque,
                                   *profile(t), gain_length])
                if tick == round(profile.duration_s/DT):
                    break
                peak_command = np.maximum(peak_command, abs(clipped))
                for sub in range(round(DT/h)):
                    t = tick*DT+sub*h
                    tau1, mean, squared_integral = lag_interval(torque, previous, TAU, h)
                    nxt, info = mechanical_step(mechanics, t, state, mean, h)
                    peak_torque = np.maximum(peak_torque, np.maximum(abs(torque), abs(tau1)))
                    saturation += (abs(raw-clipped)>1e-12)*h
                    effort += squared_integral
                    closure = max(closure, info['closure_max_m'])
                    extension_peak = max(extension_peak, info['extension_peak_abs_N'])
                    work += info['extension_work_J']
                    absolute_work += info['extension_absolute_work_J']
                    segments.writerow([t, h, *nxt, *profile(t+h), *previous, *mean, *torque, *tau1,
                                       info['extension_mean_N'], info['extension_peak_abs_N'],
                                       info['extension_work_J'], work, info['extension_absolute_work_J'],
                                       info['closure_max_m'], *info['native_motor_peak_abs_Nm']])
                    state, torque, t = nxt, tau1, t+h
                    steps += 1
                    times.append(t)
                    states.append(state.copy())
                    if np.rad2deg(max(abs(state[1:3]))) >= p['fall_angle_deg']:
                        stop = 'physical_fall'
                        break
                    if abs(state[0]) > p['max_displacement_m']:
                        stop = 'displacement_stop'
                        break
                previous = clipped.copy()
                if stop != 'duration_completed':
                    break
                if tick % 500 == 0:
                    cf.flush(); sf.flush(); rf.flush()
                    print(f"{spec['id']} t={t:.3f}/{profile.duration_s:g}s", flush=True)
        except (GeometryError, FloatingPointError, np.linalg.LinAlgError) as exc:
            stop, failure = ('geometry_stop' if isinstance(exc, GeometryError) else 'numerical_stop'), str(exc)
            write_json(out/'failure.json', {'time_s': t, 'error': failure, 'traceback': traceback.format_exc()})
        except Exception as exc:
            stop, failure, execution_error = 'execution_error', str(exc), True
            write_json(out/'failure.json', {'time_s': t, 'error': failure, 'traceback': traceback.format_exc()})
    times, states = np.asarray(times), np.asarray(states)
    full = bool(abs(times[-1]-profile.duration_s)<1e-9)
    inside = np.all(abs(states) <= np.asarray(p['state_abs_tolerance']), axis=1)
    settled = np.logical_and.accumulate(inside[::-1])[::-1]
    candidates = np.flatnonzero(settled & (times >= profile.end_s-1e-10))
    recovery = float(times[candidates[0]]-profile.end_s) if len(candidates) else None
    final = times >= profile.duration_s-p['settle_window_s']-1e-10
    checks = {'full_duration': full, 'no_fall': stop != 'physical_fall',
              'displacement': bool(max(abs(states[:, 0])) <= p['max_displacement_m']),
              'finite_and_no_warning': stop not in ('numerical_stop', 'execution_error'),
              'geometry': stop != 'geometry_stop',
              'caps': bool(np.all(np.maximum(peak_command, peak_torque) <= CAPS+1e-12)),
              'held_final_window': bool(full and np.any(final) and np.all(inside[final])),
              'recovery_after_ramp_within_5s': bool(full and recovery is not None and recovery <= p['recovery_deadline_s'])}
    metrics = {'status': 'ERROR' if execution_error else 'PASS' if all(checks.values()) else 'FAIL',
               'stop_reason': stop, 'failure': failure, 'checks': checks,
               'failed_checks': [k for k, v in checks.items() if not v],
               'specification': spec, 'initial_state': states[0], 'final_state': states[-1],
               'duration_s': times[-1], 'requested_duration_s': profile.duration_s,
               'moving_start_s': 2., 'moving_end_s': profile.end_s,
               'profile_max_abs_rate_m_s': profile.max_abs_rate_m_s,
               'integration_steps': steps, 'mechanics_step_s': h, 'projection_epsilon': epsilon,
               'windows': {name: window_metrics(times, states, start, end)
                           for name, start, end in (('before', 0., 2.), ('moving', 2., profile.end_s),
                                                   ('after', profile.end_s, profile.duration_s))},
               'window_boundaries': 'inclusive endpoints; shared boundary sample belongs to both adjacent windows',
               'recovery_after_ramp_s': recovery,
               'final_window_max_abs_error': np.max(abs(states[final]), axis=0) if np.any(final) else None,
               'peak_command_Nm': peak_command, 'peak_physical_torque_Nm': peak_torque,
               'saturation_duration_s': saturation, 'torque_squared_integral_Nm2_s': effort,
               'closure_max_m': closure, 'extension_peak_abs_N': extension_peak,
               'extension_work_J': work, 'extension_absolute_work_J': absolute_work,
               'required_motor_A_peak_stage': mechanics.peaks[0],
               'required_motor_E_peak_stage': mechanics.peaks[1],
               'required_motor_sum_abs_peak_stage': mechanics.pair_peak,
               'motor_feasibility': 'UNKNOWN; assumed-model required joint torques; no motor/gear/current limits known; 4Nm cap is virtual hip pair only',
               'noise_sha256_float64_le': noise_hash.hexdigest(),
               'acceptance_sampling': 'true mechanical endpoints; required joint torques and reactions at existing RK stages'}
    write_json(out/'metrics.json', metrics)
    return metrics


def compare_pair(scheduled_path, frozen_path):
    a, b = [np.genfromtxt(p/'control.csv', delimiter=',', names=True) for p in (scheduled_path, frozen_path)]
    _, ia, ib = np.intersect1d(a['time_s'], b['time_s'], return_indices=True)
    noise_names = ('noise_body_rad', 'noise_gyro_rad_s')
    da = np.column_stack([a[n][ia] for n in STATE_NAMES])
    db = np.column_stack([b[n][ib] for n in STATE_NAMES])
    return {'matched_sensor_samples': len(ia),
            'last_common_time_s': float(a['time_s'][ia[-1]]) if len(ia) else None,
            'identical_noise_at_matched_times': bool(len(ia) and all(np.array_equal(a[n][ia], b[n][ib]) for n in noise_names)),
            'matched_state_difference_max_abs': np.max(abs(da-db), axis=0) if len(ia) else None,
            'matched_samples_note': 'comparison uses exact shared sensor timestamps; per-window peaks separately use finer true endpoints'}


def refinement(schedule):
    """One targeted moving/nonzero-torque segment, not another full panel."""
    profile = Profile(.12, .20, 1.)
    initial = np.array([.002, .07, -.05, .03, -.06, .04])
    incoming, command = np.array([.4, -.7]), np.array([-1.2, 1.5])
    start, duration = 2.35, .02  # nonzero Ldot AND Lddot on the fastest profile
    variants = []
    for h, epsilon in ((.001, 1e-6), (.0005, 1e-6), (.00025, 1e-6), (.001, 5e-7)):
        mechanics = RequiredTorque(Plant(schedule['reference_config']), epsilon, profile=profile)
        state, torque, work, reaction = initial.copy(), incoming.copy(), 0., 0.
        for step in range(round(duration/h)):
            torque_next, mean, _ = lag_interval(torque, command, TAU, h)
            state, info = mechanical_step(mechanics, start+step*h, state, mean, h)
            work += info['extension_work_J']
            reaction += h*info['extension_mean_N']
            torque = torque_next
        variants.append({'h_s': h, 'epsilon': epsilon, 'final_state': state, 'final_torque_Nm': torque,
                         'mean_reaction_N': reaction/duration, 'work_J': work,
                         'motor_A_peak_stage': mechanics.peaks[0], 'motor_E_peak_stage': mechanics.peaks[1]})
    reference = variants[2]
    for v in variants:
        v['state_abs_difference_from_finest'] = abs(v['final_state']-reference['final_state'])
        v['reaction_difference_from_finest_N'] = v['mean_reaction_N']-reference['mean_reaction_N']
        v['work_difference_from_finest_J'] = v['work_J']-reference['work_J']
    return {'profile': asdict(profile), 'start_s': start, 'duration_s': duration,
            'initial_state': initial, 'initial_torque_Nm': incoming, 'held_command_Nm': command,
            'variants': variants, 'limitation': 'local numerical sensitivity, not full-trajectory or hardware accuracy; state entries have mixed units'}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--schedule', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    out = args.out.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    source = source_receipt('sim.fivebar.ramp_panel', argv)
    schedule, regime = read_schedule(args.schedule)
    declaration = {'matrix': matrix(), 'schedule_path': str(args.schedule.resolve()),
                   'schedule': schedule, 'initial_state': [0.]*6, 'seed': 0,
                   'dt_s': DT, 'delay_s': DT, 'lag_s': TAU.tolist(), 'caps_Nm': CAPS.tolist(),
                   'mechanics_step_s': .001, 'projection_epsilon': 1e-6,
                   'profile': 'hold2s; C2 quintic over8/2/1s; hold5s; max abs Ldot=.08*1.875/duration',
                   'acceptance': 'accepted ramp thresholds with requested end=2+moving_duration+5; true endpoints',
                   'limit': '12 full runs maximum; sampled seed0 comparators only; ideal extension and assumed mechanics; no hardware feasibility or statistical claim'}
    if (out/'manifest.json').exists():
        saved = json.loads((out/'manifest.json').read_text())
        if saved['declaration'] != declaration or saved['source']['git_commit'] != source['git_commit']:
            raise ValueError('Resume requires identical declared source and configuration')
    else:
        if list(out.iterdir()):
            raise ValueError('Fresh output must be empty or have matching manifest')
        write_json(out/'manifest.json', {'declaration': declaration, 'source': source, 'declared_utc': utc_now()})
    execution = attempt_directory(out/'executions')
    receipt = {'status': 'RUNNING', 'source': source, 'pid': os.getpid(), 'started_utc': utc_now()}
    write_json(execution/'run.json', receipt)
    started, code = time.monotonic(), 1
    try:
        rows = []
        for spec in declaration['matrix']:
            case = out/'cases'/spec['id']
            if (case/'result.json').exists():
                row = json.loads((case/'result.json').read_text())
                if row['specification'] != spec:
                    raise ValueError('Completed receipt differs from declared case')
                print(f"{spec['id']} REUSED {row['status']}", flush=True)
            else:
                path = attempt_directory(case)
                row = {'specification': spec, 'status': 'RUNNING', 'started_utc': utc_now(),
                       'artifact_directory': str(path.relative_to(out))}
                write_json(path/'receipt.json', row)
                start = time.monotonic()
                try:
                    metrics = run(schedule, regime, spec, path)
                    row.update(status=metrics['status'], metrics=metrics)
                except Exception:
                    (path/'error.txt').write_text(traceback.format_exc())
                    row.update(status='ERROR', error=traceback.format_exc())
                row.update(ended_utc=utc_now(), elapsed_wall_s=time.monotonic()-start)
                write_json(path/'receipt.json', row)
                write_json(case/'result.json', row)
                print(f"{spec['id']} {row['status']} wall={row['elapsed_wall_s']:.3f}s", flush=True)
            rows.append(row)
            write_json(out/'cases.json', rows)
        pairs = []
        for a, b in zip(rows[::2], rows[1::2]):
            if a['status'] == 'ERROR' or b['status'] == 'ERROR':
                pairs.append({'scheduled': a['specification']['id'], 'frozen': b['specification']['id'], 'status': 'ERROR'})
                continue
            pairs.append({'scheduled': a['specification']['id'], 'frozen': b['specification']['id'],
                          **compare_pair(out/a['artifact_directory'], out/b['artifact_directory'])})
        write_json(out/'comparisons.json', pairs)
        if not (out/'refinement.json').exists():
            write_json(out/'refinement.json', refinement(schedule))
        counts = {s: sum(r['status'] == s for r in rows) for s in ('PASS', 'FAIL', 'ERROR')}
        complete = not counts['ERROR'] and all(p.get('identical_noise_at_matched_times', False) for p in pairs)
        write_json(out/'summary.json', {'status': 'COMPLETE' if complete else 'INCOMPLETE',
                   'counts': counts, 'source': source, 'cases': rows, 'comparisons': pairs})
        code = 0 if complete else 1
    except Exception:
        (execution/'error.txt').write_text(traceback.format_exc())
        traceback.print_exc()
    finally:
        receipt.update(status='EXITED', exit_code=code, ended_utc=utc_now(), elapsed_wall_s=time.monotonic()-started)
        write_json(execution/'run.json', receipt)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
