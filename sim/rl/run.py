"""Stable CLI. Full commands expose no seed/budget/hyperparameter tuning knobs."""

import os
# Set before importing numerical packages, also inherited by spawned processes.
for _name in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_name] = '1'

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import sys
import traceback

from sim.rl.environment import load_protocol
from sim.rl.provenance import capture, manifest, new_output, write_json


def experiment(out, authorization, train_jobs, eval_jobs):
    out = new_output(out)
    capture(out, authorization, full=True)
    commands = []
    for seed in load_protocol()['training']['policy_seeds']:
        commands.append([sys.executable, '-m', 'sim.rl.run', 'train', '--seed', str(seed),
                         '--out', str(out / 'training' / f'seed-{seed}'),
                         '--authorization', str(authorization)])
    write_json(out / 'commands.json', commands)

    def worker(command):
        seed = command[command.index('--seed') + 1]
        with (out / f'training-{seed}.log').open('x') as log:
            return subprocess.call(command, stdout=log, stderr=subprocess.STDOUT)

    exits = {}
    with ThreadPoolExecutor(max_workers=train_jobs) as pool:
        futures = {pool.submit(worker, command): seed for seed, command in enumerate(commands)}
        for future in as_completed(futures):
            seed = futures[future]
            try:
                exits[seed] = future.result()
            except BaseException as exc:
                exits[seed] = 1
                (out / f'training-{seed}-launch-error.txt').write_text(str(exc))
            write_json(out / 'training-exits.json', exits)
    from sim.rl.evaluation import run_evaluation
    evaluation_exit = run_evaluation(out / 'training', out / 'evaluation', authorization, jobs=eval_jobs)
    code = int(any(exits.values()) or evaluation_exit)
    write_json(out / 'status.json', {'status': 'COMPLETE' if not code else 'COMPLETE_WITH_FAILURES',
                                   'exit_code': code, 'training_exits': exits,
                                   'evaluation_exit': evaluation_exit})
    manifest(out)
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('train', 'smoke', 'evaluate', 'run', 'verify'):
        child = sub.add_parser(name)
        child.add_argument('--out', type=Path, required=True, help='NEW external directory; no overwrite/resume')
        child.add_argument('--authorization', type=Path, required=True)
        if name in ('train', 'smoke'):
            child.add_argument('--seed', type=int, choices=range(5), default=0)
        if name == 'evaluate':
            child.add_argument('--training', type=Path, required=True)
        if name in ('evaluate', 'verify'):
            child.add_argument('--jobs', type=int, choices=range(1, 9), default=6)
        if name == 'run':
            child.add_argument('--train-jobs', type=int, choices=range(1, 6), default=5)
            child.add_argument('--eval-jobs', type=int, choices=range(1, 9), default=6)
    args = parser.parse_args()
    try:
        if args.command in ('train', 'smoke'):
            from sim.rl.training import train
            status = train(args.seed, args.out, args.authorization, smoke=args.command == 'smoke')
            print(json.dumps(status, sort_keys=True), flush=True)
            return status['exit_code']
        if args.command == 'verify':
            from sim.rl.verify import verify
            return verify(args.out, args.authorization.resolve(), args.jobs)
        if args.command == 'evaluate':
            from sim.rl.evaluation import run_evaluation
            return run_evaluation(args.training.resolve(), args.out, args.authorization.resolve(), args.jobs)
        return experiment(args.out, args.authorization.resolve(), args.train_jobs, args.eval_jobs)
    except BaseException:
        # Never erase a failed or interrupted attempt. If the target existed
        # before this invocation, leave it entirely untouched.
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
