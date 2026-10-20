"""Recompute frozen acceptance and physical metrics from compact raw evidence."""

import hashlib
import json
from pathlib import Path

import numpy as np

from sim.rl.environment import load_protocol


PHYSICAL = ['duration_s', 'fall_time_s', 'recovery_time_after_event_s', 'recovery_time_successes_s',
            'peak_leg_tilt_deg', 'peak_body_tilt_deg', 'peak_tilt_deg', 'peak_tilt_after_push_start_deg',
            'peak_displacement_m', 'state_rmse', 'final_window_max_abs_error',
            'command_effort_Nm2_s', 'applied_effort_Nm2_s', 'applied_mean_effort_Nm2_s',
            'peak_command_torque_Nm', 'peak_applied_torque_Nm', 'peak_applied_mean_torque_Nm',
            'command_saturation_fraction', 'command_saturation_duration_s',
            'state_squared_error_integral', 'push_impulse_Ns', 'push_duration_applied_s']


def missing_policy(reason):
    return {**dict.fromkeys(PHYSICAL), 'status': 'MISSING_POLICY', 'success': False,
            'fall_count': 0, 'training_failure_count': 1, 'numerical_failure_count': 0,
            'other_failure_count': 0, 'unrecovered_count': 1, 'penalized_recovery_s': 10.,
            'failure_reasons': [reason], 'physical_metrics_reason': 'No final policy trajectory exists',
            'control_steps': 0, 'fall_observed': None}


def trace_arrays(directory):
    directory = Path(directory)
    index = json.loads((directory / 'index.json').read_text())
    chunks = []
    segments = []
    for item in index['chunks']:
        with np.load(directory / item['path'], allow_pickle=False) as raw:
            chunks.append({k: raw[k] for k in raw.files if k not in ('segments', 'segment_offsets')})
            segments.append(raw['segments'])
    if not chunks:
        raise ValueError('No completed transitions in trace')
    return ({k: np.concatenate([c[k] for c in chunks]) for k in chunks[0]}, np.concatenate(segments))


def compute_metrics(directory, scenario, numerical_failure=False, error=None):
    p = load_protocol()
    acceptance = p['acceptance']
    rows, seg = trace_arrays(directory)
    if len(set(rows['episode'])) != 1:
        raise ValueError('Evaluation metrics require exactly one episode')
    states = np.vstack([rows['truth_before'][0], rows['truth_after']])
    times = np.r_[rows['time_s'][0], rows['time_s'] + rows['actual_dt_s']]
    duration, actual_dt = float(times[-1]), float(np.sum(seg[:, 1]))
    numerical_failure = bool(numerical_failure or not np.all(np.isfinite(states)))
    if numerical_failure and not np.all(np.isfinite(states)):
        raise ValueError('Nonfinite trace must remain an explicit numerical failure')
    full = abs(duration - p['scenarios'][0]['duration_s']) < 1e-9
    inside = np.all(abs(states) <= acceptance['state_abs_tolerance'], axis=1)
    window = times >= 10. - acceptance['settle_window_s'] - 1e-9
    held = bool(full and np.any(window) and np.all(inside[window]))
    event_end = 3.15 if scenario == 'push' else 0.
    settled = np.logical_and.accumulate(inside[::-1])[::-1]
    candidates = np.flatnonzero(settled & (times >= event_end - 1e-9))
    recovery = float(times[candidates[0]] - event_end) if full and held and len(candidates) else None
    falls = np.flatnonzero(np.rad2deg(np.max(abs(states[:, 1:3]), axis=1)) >= acceptance['fall_angle_deg'])
    fall_time = float(times[falls[0]]) if len(falls) else None
    limits = np.asarray(p['plant']['torque_limits_Nm'])
    peak_torque = np.maximum(np.max(abs(seg[:, 8:10]), axis=0), np.max(abs(seg[:, 10:12]), axis=0))
    peak_mean = np.max(abs(seg[:, 12:14]), axis=0)
    commands = rows['bounded_command_Nm']
    caps = bool(np.all(np.maximum(peak_torque, peak_mean) <= limits + 1e-12) and
                np.all(abs(commands) <= limits + 1e-12))
    impulse = float(np.dot(seg[:, 19], seg[:, 1]))
    pulse_duration = float(np.sum(seg[seg[:, 19] != 0, 1]))
    pulse_ok = scenario != 'push' or (abs(impulse - .9) < 1e-10 and abs(pulse_duration - .15) < 1e-10)
    displacement = float(np.max(abs(states[:, 0])))
    checks = {'numerics': not numerical_failure, 'caps': caps, 'full_duration': full,
              'no_fall': fall_time is None, 'displacement': displacement <= acceptance['max_displacement_m'],
              'full_pulse': pulse_ok, 'held_final_window': held,
              'recovery_deadline': recovery is not None and recovery <= acceptance['recovery_deadline_s']}
    success = all(checks.values())
    integrated = np.sum(seg[:, 2:8]**2 * seg[:, 1:2], axis=0)
    saturation = np.sum((abs(commands) >= limits - 1e-12) * rows['actual_dt_s'][:, None], axis=0)
    noise = np.vstack([rows['noise_before'][0], rows['noise_after']])
    failure_reasons = [k for k, v in checks.items() if not v]
    if error:
        failure_reasons.append(error)
    post = times >= 3. - 1e-9
    result = {
        'status': 'PASS' if success else 'FAIL', 'success': success, 'checks': checks,
        'failure_reasons': failure_reasons, 'physical_metrics_reason': None,
        'duration_s': duration, 'sum_actual_dt_s': actual_dt, 'control_steps': len(rows['time_s']),
        'integration_steps': len(seg), 'final_error': states[-1].tolist(),
        'state_squared_error_integral': integrated.tolist(), 'state_rmse': np.sqrt(integrated / actual_dt).tolist(),
        'final_window_max_abs_error': np.max(abs(states[window]), axis=0).tolist() if np.any(window) else None,
        'peak_leg_tilt_deg': float(np.rad2deg(np.max(abs(states[:, 1])))),
        'peak_body_tilt_deg': float(np.rad2deg(np.max(abs(states[:, 2])))),
        'peak_tilt_deg': float(np.rad2deg(np.max(abs(states[:, 1:3])))),
        'peak_tilt_after_push_start_deg': float(np.rad2deg(np.max(abs(states[post, 1:3]))))
            if scenario == 'push' and np.any(post) else None,
        'peak_displacement_m': displacement, 'fall_count': int(fall_time is not None),
        'fall_observed': fall_time is not None, 'fall_time_s': fall_time,
        'training_failure_count': 0, 'numerical_failure_count': int(numerical_failure),
        'other_failure_count': int(not success and fall_time is None and not numerical_failure),
        'recovery_time_after_event_s': recovery, 'recovery_time_successes_s': recovery if success else None,
        'unrecovered_count': int(recovery is None), 'penalized_recovery_s': recovery if recovery is not None else 10.,
        'push_impulse_Ns': impulse, 'push_duration_applied_s': pulse_duration,
        'command_effort_Nm2_s': np.sum(commands**2 * rows['actual_dt_s'][:, None], axis=0).tolist(),
        'applied_effort_Nm2_s': np.sum(seg[:, 14:16], axis=0).tolist(),
        'applied_mean_effort_Nm2_s': np.sum(seg[:, 12:14]**2 * seg[:, 1:2], axis=0).tolist(),
        'peak_command_torque_Nm': np.max(abs(commands), axis=0).tolist(),
        'peak_applied_torque_Nm': peak_torque.tolist(), 'peak_applied_mean_torque_Nm': peak_mean.tolist(),
        'command_saturation_duration_s': saturation.tolist(),
        'command_saturation_fraction': (saturation / actual_dt).tolist(),
        'noise_stream_sha256_float64_le': hashlib.sha256(np.asarray(noise, dtype='<f8').tobytes()).hexdigest(),
        'noise_samples': len(noise),
    }
    return result
