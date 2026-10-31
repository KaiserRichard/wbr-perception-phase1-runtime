"""G1 smoke, single development pilot, then gated parallel five-seed experiment."""
import argparse
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import numpy as np
from .protocol import HERE, identity, panel, seed_wall_cap, write_json
from .parallel import default_jobs, jobs_count, ordered_map
from .run_manifest import FINAL_SEEDS, prepare_run, seed_list, set_status


def _train_seed(task):
    from .training import train
    folder, seed, seconds, config, subprocess_envs, resume, require_complete, cap, stop_file = task
    if (folder/'failure.json').exists() or (folder/'watchdog.json').exists():
        raise RuntimeError(f'Failed seed{seed} retained; queue stopped')
    if stop_file.exists():
        raise RuntimeError(f'PARTIAL seed{seed}: queue STOP requested')
    result = train(folder, seed, seconds, resume=resume, config=config, subprocess=subprocess_envs,
                   seed_wall_cap_min=cap, stop_file=stop_file)
    if require_complete and result['status'] != 'COMPLETE':
        raise RuntimeError(f'PARTIAL seed{seed}: queue stopped')
    return result


def train_seeds(out, seeds=range(5), jobs=None, seconds=None, config=None,
                subprocess_envs=None, resume=False, require_complete=True, seed_wall_cap_min=None):
    out = Path(out)
    seed_wall_cap_min = seed_wall_cap(seed_wall_cap_min)
    jobs = jobs_count(default_jobs() if jobs is None else jobs)
    seeds = seed_list(seeds)
    if (out/'STOP').exists():
        raise RuntimeError('PARTIAL: queue STOP requested; checkpoints retained')
    manifest = prepare_run(out, seeds, config)
    if subprocess_envs is None:
        # Eight logical environments/rank streams and PPO batches are unchanged.
        # Advance them locally in concurrent seeds to avoid 5 x 8 IPC workers.
        subprocess_envs = jobs == 1
    tasks = []
    for seed in seeds:
        folder = out/f'seed-{seed}'
        folder.mkdir(parents=True, exist_ok=True)
        tasks.append((folder, seed, seconds, config, subprocess_envs,
                      resume and (folder/'checkpoints').exists(), require_complete,
                      seed_wall_cap_min, out/'STOP'))
    def stop_siblings():
        # Complete the active optimizer update/checkpoint; never kill a writer.
        for folder, *_ in tasks:
            (folder/'STOP').touch()
    set_status(out, manifest, 'TRAINING')
    try:
        results = ordered_map(_train_seed, tasks, jobs, on_error=stop_siblings)
    except BaseException:
        set_status(out, manifest, 'PARTIAL')
        raise
    set_status(out, manifest, 'TRAINED' if all(r['status'] == 'COMPLETE' for r in results) else 'PARTIAL')
    return results


def benchmark(out, jobs=None, seconds=120):
    """Fresh seeds, frozen recipe, completed updates in a shared wall window."""
    out = Path(out)
    if out.exists():
        raise FileExistsError('Benchmark requires a fresh output directory')
    out.mkdir(parents=True)
    jobs = jobs_count(default_jobs() if jobs is None else jobs)
    seeds = range(min(5, jobs))
    started = time.monotonic()
    window = {}
    cancelled = threading.Event()
    def steps():
        return [json.loads((out/f'seed-{s}/progress.json').read_text())['completed_steps'] for s in seeds]
    def stop():
        for seed in seeds:
            folder = out/f'seed-{seed}'
            folder.mkdir(exist_ok=True)
            (folder/'STOP').touch()
    def measure():
        # Warm all processes through one real optimizer update before starting
        # the shared 120s window; report cold start and drain separately.
        while not all((out/f'seed-{s}/progress.json').exists() for s in seeds):
            if cancelled.wait(.1):
                return
            if time.monotonic()-started > 240:
                window['error'] = 'Workers did not become ready within240s'
                stop(); return
        before = steps(); began = time.monotonic()
        window.update(startup_s=began-started, initial_steps=before)
        if cancelled.wait(seconds):
            return
        after = steps()
        window.update(seconds=time.monotonic()-began, final_steps=after,
                      completed_steps=[b-a for a,b in zip(before,after)])
        stop()
    monitor = threading.Thread(target=measure, daemon=True)
    monitor.start()
    try:
        results = train_seeds(out, seeds=seeds, jobs=jobs, seconds=seconds+360, require_complete=False)
    finally:
        cancelled.set(); monitor.join(timeout=2)
    if 'seconds' not in window:
        raise RuntimeError('Benchmark ended before the requested measurement window')
    elapsed = time.monotonic()-started
    total = sum(r['segment_steps'] for r in results)
    result = dict(jobs=jobs, counts_as_final=False, counts_as_pilot=False,
                  window=window, aggregate_steps_per_second=sum(window['completed_steps'])/window['seconds'],
                  completed_transitions_including_warmup_and_drain=total, elapsed_s_including_startup_and_drain=elapsed,
                  end_to_end_steps_per_second=total/elapsed, seeds=results, identity=identity())
    write_json(out/'benchmark.json', result)
    print(json.dumps(result), flush=True)
    return result


def command(module, args, timeout):
    result = subprocess.run([sys.executable, '-m', module, *map(str,args)], timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'{module} exited{result.returncode}')


def curves(run):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    path=Path(run)/'episodes.jsonl'
    rows=[json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    if not rows:
        return
    fig,axes=plt.subplots(2,1,sharex=True,figsize=(8,5))
    for ax,key,label in zip(axes,['r','l'],['Episode return','Episode length (actions)']):
        ax.plot([r['transitions'] for r in rows],[r['episode'][key] for r in rows],'.',alpha=.4)
        ax.set_ylabel(label);ax.grid(True)
    axes[-1].set_xlabel('Policy transitions');fig.tight_layout()
    fig.savefig(Path(run)/'learning-curves.png');plt.close(fig)


def smoke(out, seconds=600, jobs=None):
    from .training import train,newest
    from .evaluation import evaluate,parity
    cfg=json.loads((HERE/'smoke.json').read_text())
    started=time.monotonic();out=Path(out);out.mkdir(parents=True,exist_ok=True)
    # 60s bounded updates stop conservatively before segment deadlines.
    first=train(out/'initial',cfg['seed'],seconds=cfg['first_segment_deadline_seconds'])
    copied=out/'restored'
    shutil.copytree(out/'initial',copied)
    before=json.loads((newest(copied)/'complete.json').read_text())['steps']
    remaining=seconds-(time.monotonic()-started)-cfg['reserve_validation_seconds']
    if remaining < 120:
        raise RuntimeError('Smoke deadline exhausted before fresh-directory resume')
    second=train(copied,cfg['seed'],seconds=remaining,resume=True)
    after=json.loads((newest(copied)/'complete.json').read_text())['steps']
    paired=parity()
    # Development-only timing anchor, never consult final cases during implementation.
    jobs=jobs_count(default_jobs() if jobs is None else jobs)
    timing_cases=panel(True)[:jobs]
    evaluation=evaluate(timing_cases,jobs=jobs)
    curves(copied)
    elapsed=time.monotonic()-started
    wall=first['elapsed_s_including_checkpoints']+second['elapsed_s_including_checkpoints']
    F=(first['segment_steps']+second['segment_steps'])/wall
    ratio=1.3 if platform.system()=='Darwin' else 1.
    laptop_F=F/ratio  # Explicit owner-requested ESTIMATE: laptop takes1.3x Mac wall time.
    eval_seconds=evaluation['elapsed_s']*1200/len(timing_cases)*ratio
    receipt=dict(status='PASS' if after>before and elapsed<=seconds else 'FAIL',
                 counts_as_final=False,counts_as_pilot=False, before=before,after=after,
                 completed_transitions=first['segment_steps']+second['segment_steps'],
                 training_wall_s=wall,elapsed_s=elapsed,transitions_per_second=F,
                 max_rollout_update_s=max(first['max_rollout_update_s'],second['max_rollout_update_s']),
                 checkpoint_copy_resume='PASS' if after>before else 'FAIL',zero_action_parity=paired,
                 evaluation_case_seconds=evaluation['elapsed_s']/len(timing_cases),jobs=jobs,
                 laptop_ESTIMATE=dict(ratio_wall=ratio,transitions_per_second=laptop_F,
                     five_seed_training_hours=5000000/laptop_F/3600,
                     paired_1200_case_evaluation_minutes=eval_seconds/60,
                     throughput_gate=laptop_F>=1000000/5400,evaluation_gate=eval_seconds<=7200),
                 identity=identity(),laptop_status='NO-GO: report assembly and Windows portability unresolved; scientific pilot not run')
    write_json(out/'smoke.json',receipt)
    print(json.dumps(receipt),flush=True)
    # Exactly600s total smoke window; only wait after actual train/resume/evaluation succeeded.
    while time.monotonic()-started < seconds:
        time.sleep(min(1,seconds-(time.monotonic()-started)))
    receipt['elapsed_s']=time.monotonic()-started
    write_json(out/'smoke.json',receipt)
    if receipt['status'] != 'PASS':
        raise RuntimeError('Smoke deadline/resume gate failed')
    return receipt


def pilot(out, baseline, jobs=None):
    from .training import train
    from .evaluation import evaluate
    out=Path(out)
    receipt=train(out,42,1200)
    curves(out)
    rows=[json.loads(line) for line in (out/'episodes.jsonl').read_text().splitlines()]
    last=max(r['wall_s'] for r in rows)
    first=[r for r in rows if r['wall_s']<=300]
    final=[r for r in rows if r['wall_s']>=last-300]
    result=evaluate(panel(True),out,jobs=jobs)
    A,B=baseline['strata']['overall'],result['strata']['overall']
    learned=bool(first and final and np.mean([r['episode']['r'] for r in final])>np.mean([r['episode']['r'] for r in first]) and
                 np.mean([r['episode']['l'] for r in final])>=np.mean([r['episode']['l'] for r in first]))
    valid=bool(A['E'] is not None and B['E'] is not None and B['E']<=1.1*A['E'] and B['survival']>=A['survival']-.05-1e-12 and B['numerical_failures']==0)
    gate=dict(pass_pilot=learned and valid,learning_improved=learned,paired_precision_survival=valid,
              training=receipt,development=result,counts_as_final=False)
    write_json(out/'pilot.json',gate)
    if not gate['pass_pilot']:
        raise RuntimeError('Pilot FAIL: recipe ends; no seed/reward retries')
    return gate


def full(out, jobs=None, seed_wall_cap_min=None, seeds=FINAL_SEEDS):
    from .evaluation import evaluate,parity
    jobs=jobs_count(default_jobs() if jobs is None else jobs)
    seed_wall_cap_min=seed_wall_cap(seed_wall_cap_min)
    seeds=seed_list(seeds)
    out=Path(out);out.mkdir(parents=True,exist_ok=True);began=time.monotonic()
    prepare_run(out, seeds)
    write_json(out/f'runtime-{time.time_ns()}.json',dict(seed_wall_cap_min=seed_wall_cap_min))
    def check_stop():
        if (out/'STOP').exists():
            raise RuntimeError('PARTIAL: queue STOP requested; checkpoints retained')
    try:
        check_stop()
        smoke_path=out/'smoke/smoke.json'
        measured=json.loads(smoke_path.read_text()) if smoke_path.exists() else smoke(out/'smoke',jobs=jobs)
        if measured['identity'] != identity() or measured['status'] != 'PASS' or measured.get('jobs',1)!=jobs:
            raise RuntimeError('Retained smoke is failed or source differs; no automatic retry')
        if (seed_wall_cap_min is not None and
                measured['laptop_ESTIMATE']['transitions_per_second']*seed_wall_cap_min*60 < 1000000):
            raise RuntimeError('NO-GO: measured smoke forecast exceeds configured seed wall cap')
        if not measured['laptop_ESTIMATE']['evaluation_gate']:
            raise RuntimeError('NO-GO: measured smoke evaluation forecast exceeds120min')
        check_stop()
        # This receipt is an evidence contract, not permission to alter the model/recipe.
        readiness=out/'host-readiness.json'
        required=('report_assembly_resolved','windows_smoke_passed','offline_bundle_verified','host_and_usb_permitted')
        data=json.loads(readiness.read_text()) if readiness.exists() else {}
        if any(data.get(k) is not True for k in required):
            raise RuntimeError('NO-GO: report/Windows/offline/host prerequisites unresolved; see README')
        write_json(out/'parity.json',parity())
        baseline_path=out/'development-lqr.json'
        baseline=json.loads(baseline_path.read_text()) if baseline_path.exists() else evaluate(panel(True),jobs=jobs)
        write_json(baseline_path,baseline)
        if any(r['numerical_failure'] for r in baseline['rows']):
            raise RuntimeError('Invalid numerical development baseline')
        if all(baseline['strata'][f'{d}ms']['strict']>=.95 for d in (2,5,6,8,10)):
            raise RuntimeError('STOP: development LQR ceiling, no headroom')
        pilot_path=out/'pilot-seed42/pilot.json'
        if pilot_path.exists():
            if not json.loads(pilot_path.read_text())['pass_pilot']:
                raise RuntimeError('Retained pilot FAIL: no automatic retry')
        elif (out/'pilot-seed42').exists():
            raise RuntimeError('Interrupted development pilot retained; no automatic retry')
        else:
            check_stop()
            pilot(out/'pilot-seed42',baseline,jobs=jobs)
        check_stop()
        train_seeds(out,seeds=seeds,jobs=jobs,seed_wall_cap_min=seed_wall_cap_min,resume=True)
        for seed in seeds:
            curves(out/f'seed-{seed}')
        check_stop()
        if seeds != FINAL_SEEDS:
            write_json(out/'part-complete.json',dict(status='TRAINED',seeds=seeds,identity=identity(),
                       elapsed_s=time.monotonic()-began,final_evaluation='Merge seeds0..4, then evaluate merged root'))
            return
        command('sim.rl.g1.evaluation',['--out',out/'final','--seeds-root',out,'--jobs',jobs],7200)
        check_stop()
        write_json(out/'complete.json',dict(status='COMPLETE',elapsed_s=time.monotonic()-began,identity=identity()))
    finally:
        for seed in seeds:
            curves(out/f'seed-{seed}')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('mode',choices=['smoke','run','pilot','benchmark'])
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--jobs',type=jobs_count,default=default_jobs(),
                   help='Seed/case processes (default min(5, cpu_count//2)); 1 is serial')
    p.add_argument('--seconds',type=float,default=120,help='Benchmark measurement window only')
    p.add_argument('--seed-wall-cap-min',type=seed_wall_cap,
                   help='Cumulative final-seed wall cap in minutes (default unlimited)')
    p.add_argument('--seeds',type=seed_list,default=FINAL_SEEDS,
                   help='Final training seeds, comma-separated (default 0,1,2,3,4); subsets skip final evaluation')
    args=p.parse_args()
    if args.mode != 'run' and args.seeds != FINAL_SEEDS:
        p.error('--seeds selects final training seeds in run mode only')
    if args.mode=='smoke':smoke(args.out,jobs=args.jobs)
    elif args.mode=='run':full(args.out,jobs=args.jobs,seed_wall_cap_min=args.seed_wall_cap_min,seeds=args.seeds)
    elif args.mode=='benchmark':benchmark(args.out,args.jobs,args.seconds)
    else:
        from .evaluation import evaluate
        pilot(args.out,evaluate(panel(True),jobs=args.jobs),jobs=args.jobs)

if __name__=='__main__':main()
