"""Paired development/final G1 evaluation; deterministic policies, frozen IMU seeds."""
import argparse
import json
from pathlib import Path
import time
import numpy as np
from .environment import G1Env
from .metrics import compare, strata
from .protocol import HERE, identity, panel, write_json
from .parallel import default_jobs, jobs_count, one_thread, ordered_map


def load_policy(run, require_final=False):
    one_thread()
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    from .training import newest
    import pickle
    dest = newest(run)
    with (dest/'state.pkl').open('rb') as f:
        state = pickle.load(f)
    if state['identity'] != identity():
        raise ValueError('Evaluation source/model/protocol differs from checkpoint')
    if require_final and state['completed_steps'] != 1000000:
        raise ValueError('Final evaluation requires exactly1M completed transitions')
    raw = DummyVecEnv([lambda:G1Env()])
    norm = VecNormalize.load(dest/'normalizer.pkl', raw)
    norm.training = False; norm.norm_reward = False
    model = PPO.load(dest/'policy.zip', device='cpu')
    model.policy.set_training_mode(False)
    return model, norm, state


def _evaluate_chunk(task):
    cases, run, trace, require_final = task
    return evaluate(cases, run, trace, require_final, jobs=1)['rows']


def evaluate(cases, run=None, trace=None, require_final=False, jobs=None):
    one_thread()
    cases = list(cases)
    jobs = jobs_count(default_jobs() if jobs is None else jobs)
    if jobs > 1 and len(cases) > 1:
        started = time.monotonic()
        # Contiguous chunks preserve case/float-reduction order. Each worker
        # loads a checkpoint once and resets the environment for every case.
        size = (len(cases)+jobs-1)//jobs
        tasks = [(cases[i:i+size], run, trace, require_final)
                 for i in range(0, len(cases), size)]
        chunks = ordered_map(_evaluate_chunk, tasks, jobs)
        rows = [row for chunk in chunks for row in chunk]
        return dict(rows=rows, strata=strata(rows), elapsed_s=time.monotonic()-started)
    model = norm = None
    if run is not None:
        model, norm, _ = load_policy(run, require_final)
    env = G1Env(baseline=run is None, record=trace is not None)
    rows = []; started = time.monotonic()
    try:
        for case in cases:
            obs, _ = env.reset(options=case)
            inference = []
            while True:
                before = time.perf_counter()
                action = np.zeros(1) if model is None else model.predict(norm.normalize_obs(obs), deterministic=True)[0]
                inference.append(time.perf_counter()-before)
                obs, _, terminal, truncated, info = env.step(action)
                if terminal or truncated:
                    row = dict(case=case, **info['episode_metrics'],
                               inference_mean_s=float(np.mean(inference)), inference_max_s=max(inference))
                    rows.append(row)
                    break
            if trace is not None:
                path = Path(trace); path.mkdir(parents=True, exist_ok=True)
                np.savez_compressed(path/f"case-{case['noise_seed']}.npz",
                                    times=[r[0] for r in env.samples], errors=[r[1] for r in env.samples],
                                    requests=[r[2] for r in env.samples], torque=[r[3] for r in env.samples],
                                    actions=env.actions)
                write_json(path/f"events-{case['noise_seed']}.json", env.trace)
    finally:
        env.close()
        if norm is not None:
            norm.close()
    return dict(rows=rows, strata=strata(rows), elapsed_s=time.monotonic()-started)


def parity(case=None):
    case = panel(True)[0] if case is None else case
    a, b = G1Env(baseline=True), G1Env()
    try:
        oa,_ = a.reset(options=case); ob,_ = b.reset(options=case)
        np.testing.assert_array_equal(oa, ob)
        while True:
            ra, rb = a.step([0.]), b.step([0.])
            for x,y in zip(ra[:4],rb[:4]):
                np.testing.assert_array_equal(x,y)
            np.testing.assert_array_equal(a.runtime.truth(),b.runtime.truth())
            np.testing.assert_array_equal(a.runtime.torque(),b.runtime.torque())
            if ra[2] or ra[3]:
                break
        return dict(status='PASS', ticks=len(a.samples)-1, case=case)
    finally:
        a.close(); b.close()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--development',action='store_true')
    p.add_argument('--run',type=Path)
    p.add_argument('--seeds-root',type=Path)
    p.add_argument('--jobs',type=jobs_count,default=default_jobs(),
                   help='Case worker processes (default min(5, cpu_count//2)); 1 is serial')
    args=p.parse_args()
    cases=panel(args.development)
    if args.seeds_root:
        if args.development:
            p.error('Final comparison uses the200-case final panel')
        from .run_manifest import FINAL_SEEDS, MANIFEST
        if (args.seeds_root/MANIFEST).exists():
            from .merge_runs import validate_part
            manifest=validate_part(args.seeds_root)
            if manifest['seeds'] != FINAL_SEEDS:
                raise ValueError('Merge all seeds0..4 before final evaluation')
        baseline=evaluate(cases,jobs=args.jobs)
        policies=[]
        for seed in range(5):
            run=args.seeds_root/f'seed-{seed}'
            _,norm,state=load_policy(run,True);norm.close()
            if state['seed'] != seed:
                raise ValueError('Expected independent final seeds0..4')
            result=evaluate(cases,run,require_final=True,jobs=args.jobs)
            write_json(args.out/f'seed-{seed}.json',result);policies.append(result['rows'])
        write_json(args.out/'baseline.json',baseline)
        write_json(args.out/'comparison.json',compare(baseline['rows'],policies))
    else:
        result=evaluate(cases,args.run,require_final=not args.development and args.run is not None,jobs=args.jobs)
        write_json(args.out,result)

if __name__=='__main__':
    main()
