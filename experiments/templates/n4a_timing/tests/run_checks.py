#!/usr/bin/env python3
"""Run the ticket and dependency suites, writing only inside the owned path or tempdirs."""
from pathlib import Path
import os
import shlex
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SUITES = ['experiments/templates/n4a_timing/tests', 'tools/eval_pipeline/accuracy/tests',
          'tools/eval_pipeline/profile/tests', 'tools/clockmap/tests']
commands = [[sys.executable, '-m', 'unittest', 'discover', '-s', suite, '-v'] for suite in SUITES]
commands.append([sys.executable, '-c', '''import pathlib, subprocess, sys, tempfile, unittest
sys.path.insert(0, str(pathlib.Path('tools/runtime_observer/tests').resolve()))
import test_observer
with tempfile.TemporaryDirectory(dir='experiments/templates/n4a_timing/tests') as tmp:
    executable = pathlib.Path(tmp).resolve() / 'test_recorder'
    command = ['c++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-pedantic', '-pthread', 'tools/runtime_observer/tests/test_recorder.cpp', '-o', str(executable)]
    print('C++ build:', command, flush=True)
    subprocess.run(command, check=True)
    subprocess.run([str(executable)], check=True)
    test_observer.__file__ = str(executable.parent / 'test_observer.py')
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_observer))
sys.exit(0 if result.wasSuccessful() else 1)'''])
# The existing trajectory suite defaults to writing under its own tools/ path.
# Redirect only its scratch constant; leave all tests and source unchanged.
commands.append([sys.executable, '-c', '''import pathlib, sys, tempfile, unittest
sys.path.insert(0, str(pathlib.Path('tools/trajectory_eval').resolve()))
import test_traj_eval
shared = pathlib.Path('/Users/quockaiser/Desktop/Research/wbr-perception-phase1-runtime')
if (shared / 'experiments/2026-10-13-n4a-euroc-mh01/eval/gt_data.csv').is_file():
    test_traj_eval.REPO = shared  # Only read-only historical input paths use this constant.
with tempfile.TemporaryDirectory(dir='experiments/templates/n4a_timing/tests') as tmp:
    test_traj_eval.SCRATCH = pathlib.Path(tmp)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_traj_eval))
sys.exit(0 if result.wasSuccessful() else 1)'''])
commands.extend([['bash', '-n', path] for path in [
    'experiments/templates/n4a_timing/run_n4a_timing.sh',
    'experiments/templates/n4a_timing/analyze_n4a_timing.sh',
    'tools/eval_pipeline/accuracy/run_euroc.sh']])
commands.append(['git', 'diff', '--check', '--', 'experiments/templates/n4a_timing'])
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
failed = False
with (HERE / 'last-run.log').open('w') as log:
    for command in commands:
        label = '$ PYTHONDONTWRITEBYTECODE=1 ' + shlex.join(command) + '\n'
        print(label, end='', flush=True); log.write(label); log.flush()
        proc = subprocess.run(command, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(proc.stdout, end='', flush=True); log.write(proc.stdout)
        log.write(f'EXIT CODE: {proc.returncode}\n\n'); log.flush()
        failed |= proc.returncode != 0
raise SystemExit(1 if failed else 0)
