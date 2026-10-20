"""Actual LQR adapter parity against the unmodified CSV evaluator, no re-design."""

from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
import csv
import multiprocessing
from pathlib import Path

import numpy as np

from sim.augmented import AugmentedRuntime, load_experiment
from sim.augmented_eval import evaluate
from sim.planar import STATE_NAMES
from sim.rl.environment import ROOT
from sim.rl.evaluation import episode
from sim.rl.metrics import trace_arrays
from sim.rl.provenance import capture, manifest, new_output, verify_authorization, write_json
from sim.rl.training import single_thread


MAPPING = {
    'duration_s': 'duration_s', 'sum_actual_dt_s': 'sum_actual_dt_s', 'control_steps': 'control_steps',
    'integration_steps': 'integration_steps', 'final_error': 'final_error',
    'final_window_max_abs_error': 'final_window_max_abs_error',
    'state_squared_error_integral': 'state_squared_error_integral',
    'state_rmse': 'state_rmse_over_actual_duration', 'peak_tilt_deg': 'peak_tilt_deg',
    'peak_tilt_after_push_start_deg': 'peak_tilt_after_push_start_deg',
    'peak_displacement_m': 'peak_displacement_m', 'fall_time_s': 'fall_time_s',
    'recovery_time_after_event_s': 'recovery_time_after_event_s', 'push_impulse_Ns': 'push_impulse_Ns',
    'push_duration_applied_s': 'push_duration_applied_s',
    'applied_effort_Nm2_s': 'torque_squared_integral_Nm2_s',
    'applied_mean_effort_Nm2_s': 'applied_mean_squared_integral_Nm2_s',
    'command_effort_Nm2_s': 'clipped_command_squared_integral_Nm2_s',
    'peak_applied_torque_Nm': 'peak_physical_torque_Nm',
    'peak_applied_mean_torque_Nm': 'peak_applied_mean_torque_Nm',
}


def parity_case(task):
    out = Path(task['root'])
    out.mkdir()
    base, _, config = load_experiment(ROOT / 'sim/configs/assumed_actuator_noise.json')
    runtime = AugmentedRuntime(base, replace(config, delay_s=task['delay_s']))
    gain = np.asarray(task['gain'])
    native = evaluate(runtime, lambda observation: -gain @ observation.vector(),
                      task['scenario'], task['noise_seed'], out / 'original')
    adapted = episode({**task, 'out': str(out / 'adapter')})
    for new, old in MAPPING.items():
        if native[old] is None:
            assert adapted[new] is None, (new, adapted[new])
        else:
            np.testing.assert_allclose(adapted[new], native[old], rtol=1e-9, atol=1e-11, err_msg=new)
    assert adapted['status'] == native['status']
    assert adapted['checks'] == native['checks']
    assert adapted['noise_stream_sha256_float64_le'] == native['noise_stream_sha256_float64_le']
    rows, _ = trace_arrays(out / 'adapter' / 'trace')
    with (out / 'original' / 'control.csv').open() as stream:
        original = list(csv.DictReader(stream))
    truth = np.asarray([[float(row[k]) for k in STATE_NAMES] for row in original])
    adapted_truth = np.vstack([rows['truth_before'][0], rows['truth_after']])
    np.testing.assert_allclose(adapted_truth, truth, rtol=1e-9, atol=1e-11)
    return {'delay_s': task['delay_s'], 'scenario': task['scenario'], 'noise_seed': task['noise_seed'],
            'status': 'PARITY_PASS', 'acceptance': adapted['status'], 'control_steps': adapted['control_steps'],
            'maximum_state_difference': float(np.max(abs(adapted_truth - truth))),
            'compared_metrics': len(MAPPING), 'noise_hash_match': True}


def verify(out, authorization, jobs=4):
    out = new_output(out)
    capture(out, authorization)
    _, designs = verify_authorization(authorization)
    tasks = [{'controller': 'lqr', 'policy_seed': None, 'delay_s': delay, 'scenario': scenario,
              'noise_seed': 77, 'gain': design['K_used'],
              'root': str(out / f'{round(delay*1000)}ms-{scenario}')}
             for delay, design in designs.items() for scenario in ('balance', 'push')]
    with ProcessPoolExecutor(max_workers=jobs, mp_context=multiprocessing.get_context('spawn'),
                             initializer=single_thread) as pool:
        results = list(pool.map(parity_case, tasks))
    write_json(out / 'parity.json', {'status': 'PASS', 'cases': results,
                                   'purpose': 'Adapter equivalence only, noise seed 77; not held-out comparison'})
    manifest(out)
    return 0
