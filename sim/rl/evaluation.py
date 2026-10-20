"""One held-out LQR panel and five paired deterministic final-policy panels."""

from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import multiprocessing
from pathlib import Path
import time
import traceback

import numpy as np
import torch
from stable_baselines3 import PPO

from sim.rl.environment import WbrEnv, decode_native, load_protocol
from sim.rl.metrics import PHYSICAL, compute_metrics, missing_policy
from sim.rl.provenance import capture, manifest, new_output, sha256, source_hashes, verify_authorization, write_json
from sim.rl.trace import TraceRecorder
from sim.rl.training import single_thread


_MODELS = {}


def episode(task):
    out = Path(task['out'])
    out.mkdir(parents=True, exist_ok=False)
    identity = {k: task[k] for k in ('controller', 'policy_seed', 'delay_s', 'scenario', 'noise_seed')}
    if task.get('missing_reason'):
        metrics = missing_policy(task['missing_reason'])
        write_json(out / 'metrics.json', {**identity, **metrics})
        return {**identity, **metrics, 'path': str(out)}
    recorder = TraceRecorder(out / 'trace', load_protocol())
    env = WbrEnv(recorder=recorder)
    error = None
    try:
        obs, _ = env.reset(options={k: task[k] for k in ('delay_s', 'scenario', 'noise_seed')})
        if task['controller'] == 'ppo':
            checkpoint = task['checkpoint']
            if checkpoint not in _MODELS:
                _MODELS[checkpoint] = PPO.load(checkpoint, device='cpu')
            model = _MODELS[checkpoint]
            model.policy.set_training_mode(False)
        while True:
            if task['controller'] == 'lqr':
                raw_action = -np.asarray(task['gain']) @ decode_native(obs, env.protocol) / env.limits
            else:
                with torch.no_grad():
                    tensor, _ = model.policy.obs_to_tensor(obs)
                    raw_action = model.policy(tensor, deterministic=True)[0].cpu().numpy()[0]
            obs, _, terminated, truncated, _ = env.step(raw_action)
            recorder.attach_raw(raw_action)
            if terminated or truncated:
                break
    except BaseException as exc:
        error = f'{type(exc).__name__}: {exc}'
        (out / 'error.txt').write_text(traceback.format_exc())
        if hasattr(env, 'runtime'):
            with (out / 'failure-state.npz').open('xb') as stream:
                np.savez_compressed(stream, truth=env.runtime.truth(), time_s=env.runtime.time,
                                    attempted_action=getattr(env, 'attempted_action', np.full(2, np.nan)),
                                    warnings=env.runtime.warning_counts)
    finally:
        env.close()
    if recorder.total_steps:
        metrics = compute_metrics(out / 'trace', task['scenario'], numerical_failure=error is not None, error=error)
    else:
        metrics = {**dict.fromkeys(PHYSICAL), 'status': 'EVALUATION_FAILED', 'success': False,
                   'fall_count': 0, 'training_failure_count': 0, 'numerical_failure_count': 1,
                   'other_failure_count': 0, 'unrecovered_count': 1, 'penalized_recovery_s': 10.,
                   'failure_reasons': [error or 'No transitions'], 'control_steps': 0,
                   'physical_metrics_reason': 'No completed evaluation transition'}
    metrics.update(identity)
    write_json(out / 'metrics.json', metrics)
    return {**metrics, 'path': str(out)}


def final_policies(training):
    p = load_protocol()
    policies = {}
    for seed in p['training']['policy_seeds']:
        folder = Path(training) / f'seed-{seed}'
        try:
            status = json.loads((folder / 'status.json').read_text())
            provenance = json.loads((folder / 'provenance.json').read_text())
            if (status['status'] != 'COMPLETE' or not status['counts_as_training_seed'] or
                    status['actual_env_steps'] != p['training']['steps_per_seed'] or
                    status['recorded_steps'] != p['training']['steps_per_seed'] or
                    status['sb3_env_steps'] != p['training']['steps_per_seed'] or status['seed'] != seed):
                raise ValueError(f'Incomplete full-budget seed: {status.get("failure_reasons")}')
            if provenance['source_sha256'] != source_hashes():
                raise ValueError('Evaluation source differs from the training freeze')
            checkpoint = folder / 'final.zip'
            if sha256(checkpoint) != status['checkpoint_sha256']:
                raise ValueError('Final checkpoint digest mismatch')
            policies[seed] = {'checkpoint': str(checkpoint), 'sha256': status['checkpoint_sha256'],
                              'complete': True, 'actual_env_steps': status['actual_env_steps']}
        except (OSError, ValueError, KeyError) as exc:
            policies[seed] = {'missing_reason': f'{type(exc).__name__}: {exc}', 'complete': False,
                              'actual_env_steps': None}
    return policies


def run_evaluation(training, out, authorization, jobs=6):
    out = new_output(out)
    started = time.perf_counter()
    capture(out, authorization, full=True)
    _, designs = verify_authorization(authorization)
    policies, p = final_policies(training), load_protocol()
    write_json(out / 'policies.json', policies)
    tasks = []
    for controller, policy_seed in [('lqr', None), *[('ppo', s) for s in p['training']['policy_seeds']]]:
        for delay in p['plant']['fixed_delays_s']:
            for scenario in p['scenarios']:
                for noise in p['evaluation']['noise_seeds']:
                    key = f'{controller}-{policy_seed}-d{round(delay*1000)}-{scenario["name"]}-n{noise}'
                    task = {'controller': controller, 'policy_seed': policy_seed, 'delay_s': delay,
                            'scenario': scenario['name'], 'noise_seed': noise, 'out': str(out / 'episodes' / key)}
                    task.update({'gain': designs[delay]['K_used']} if controller == 'lqr' else policies[policy_seed])
                    tasks.append(task)
    outcomes = []
    # Individual task failures become explicit outcomes; other seeds continue.
    with ProcessPoolExecutor(max_workers=jobs, mp_context=multiprocessing.get_context('spawn'),
                             initializer=single_thread) as pool:
        futures = {pool.submit(episode, task): task for task in tasks}
        for future in as_completed(futures):
            task = futures[future]
            try:
                result = future.result()
            except BaseException as exc:
                result = {k: task[k] for k in ('controller', 'policy_seed', 'delay_s', 'scenario', 'noise_seed')}
                result.update({**dict.fromkeys(PHYSICAL), 'status': 'EVALUATION_FAILED', 'success': False,
                               'fall_count': 0, 'training_failure_count': 0, 'numerical_failure_count': 0,
                               'other_failure_count': 1, 'unrecovered_count': 1, 'penalized_recovery_s': 10.,
                               'control_steps': 0, 'failure_reasons': [f'{type(exc).__name__}: {exc}'],
                               'physical_metrics_reason': 'Worker failed; partial files retained',
                               'path': task['out']})
                Path(task['out']).mkdir(parents=True, exist_ok=True)
                write_json(Path(task['out']) / 'worker-failure.json', result)
            outcomes.append(result)
            write_json(out / 'progress.json', {'completed_outcomes': len(outcomes), 'expected': len(tasks),
                                               'elapsed_s': time.perf_counter() - started})
    outcomes.sort(key=lambda x: (x['controller'], -1 if x['policy_seed'] is None else x['policy_seed'],
                                 x['delay_s'], x['scenario'], x['noise_seed']))
    write_json(out / 'outcomes.json', outcomes)
    from sim.rl.aggregate import aggregate
    report = aggregate(outcomes, policies)
    report['elapsed_s'] = time.perf_counter() - started
    write_json(out / 'aggregate.json', report)
    exit_code = int(any(x['status'] == 'EVALUATION_FAILED' or x['numerical_failure_count'] for x in outcomes)
                    or not all(v['complete'] for v in policies.values()))
    write_json(out / 'status.json', {'status': 'COMPLETE' if not exit_code else 'COMPLETE_WITH_FAILURES',
                                   'exit_code': exit_code, 'outcomes': len(outcomes),
                                   'ppo_outcomes': 800, 'unique_lqr_outcomes': 160})
    manifest(out)
    return exit_code
