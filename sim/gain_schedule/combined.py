"""Thirty sampled combined corners; two nominal designs, unchanged evaluation.

This isolated study does not modify the accepted runtime, stress or schedule.
An existing output directory resumes completed receipts without repeating cases.
"""

import argparse
import csv
from dataclasses import asdict, replace
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

THREAD_VARIABLES = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
                    "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")
for _name in THREAD_VARIABLES:
    os.environ[_name] = "1"

import numpy as np

from sim.augmented import load_experiment
from sim.augmented_eval import evaluate
from sim.augmented_lqr import synthesize_augmented
from sim.gain_schedule.model import config_at_length
from sim.gain_schedule.stress import (
    CONFIG, ROOT, Condition, DesignObserverController, actual_config,
    make_runtime, utc_now,
)

CONDITIONS = {
    "nominal": dict(delay_s=.002, mass_scale=1., wheel_delta=0., push_N=6.),
    "combined_target": dict(delay_s=.006, mass_scale=1.5, wheel_delta=.167, push_N=30.),
    "stronger_sample": dict(delay_s=.008, mass_scale=2., wheel_delta=.5, push_N=36.),
}


def json_value(value):
    """JSON safe NumPy conversion; nonfinite diagnostics are unavailable, not NaN."""
    if isinstance(value, np.ndarray):
        return json_value(value.tolist())
    if isinstance(value, np.generic):
        return json_value(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(k): json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(v) for v in value]
    return value


def write_json(path, value):
    """Atomic receipts, including NumPy booleans, with no partial JSON on interrupt."""
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(json_value(value), indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def source_receipt(module, argv):
    return {
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "git_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
        "command": [sys.executable, "-m", module, *argv], "cwd": str(Path.cwd()),
        "python": sys.version, "platform": platform.platform(),
        "packages": {p: importlib.metadata.version(p) for p in ("numpy", "scipy", "mujoco")},
        "threads": {name: os.environ.get(name) for name in THREAD_VARIABLES},
    }


def matrix():
    return [{"id": f"L{round(length*100):02d}_{name}_seed{seed}",
             "length_m": length, "name": name,
             "condition": asdict(Condition(**values, seed=seed))}
            for length in (.12, .20) for name, values in CONDITIONS.items() for seed in range(5)]


def attempt_directory(case):
    """Keep interrupted attempts; a retry gets a new directory, never overwrites traces."""
    case.mkdir(parents=True, exist_ok=True)
    index = 1
    while (case / f"attempt-{index:03d}").exists():
        index += 1
    path = case / f"attempt-{index:03d}"
    path.mkdir()
    return path


def noise_pairing(rows, out):
    """Compare exact timestamp/noise bytes over common observed ticks after stops."""
    groups = []
    for seed in range(5):
        members = [r for r in rows if r['condition']['seed'] == seed and r['status'] != 'ERROR']
        arrays = []
        for row in members:
            data = np.genfromtxt(out / row['artifact_directory'] / 'rollout/control.csv',
                                 delimiter=',', names=True)
            arrays.append(np.column_stack([data[n] for n in
                ('time_s', 'body_angle_noise_rad', 'body_gyro_noise_rad_s')]))
        count = min((len(a) for a in arrays), default=0)
        groups.append({'seed': seed, 'case_ids': [r['id'] for r in members],
                       'common_samples': count,
                       'matched_timestamp_noise_prefix': bool(count and all(
                           np.array_equal(a[:count], arrays[0][:count]) for a in arrays)),
                       'prefix_sha256_float64_le': hashlib.sha256(
                           np.asarray(arrays[0][:count], dtype='<f8').tobytes()).hexdigest() if count else None})
    return groups


def run_case(spec, nominal, effects, gain, out):
    case = out / 'cases' / spec['id']
    if (case / 'result.json').exists():
        saved = json.loads((case / 'result.json').read_text())
        if saved['specification'] != spec:
            raise ValueError('Completed case differs from declared matrix')
        print(f"{spec['id']} REUSED {saved['status']}", flush=True)
        return saved
    path = attempt_directory(case)
    row = {**spec, 'specification': spec, 'status': 'RUNNING', 'started_utc': utc_now(),
           'artifact_directory': str(path.relative_to(out))}
    condition = Condition(**spec['condition'])
    radius = nominal['physics']['wheel_radius']['value']
    write_json(path / 'condition.json', {
        **spec, 'actual_config': actual_config(nominal, condition),
        'actual_runtime': asdict(replace(effects, delay_s=condition.delay_s)),
        'wheel_map': [1/radius, -1+condition.wheel_delta, -condition.wheel_delta],
        'design': f"design-L{round(spec['length_m']*100):02d}.json",
        'controller_feedback': 'measured six-state; own 2ms/5ms clipped-command reconstruction only',
    })
    write_json(path / 'receipt.json', row)
    start = time.monotonic()
    print(f"{spec['id']} RUNNING", flush=True)
    try:
        runtime = make_runtime(nominal, effects, condition)
        (path / 'actual_model.xml').write_text(runtime.plant.xml)
        with (path / 'observer.csv').open('x', newline='') as stream:
            audit = csv.writer(stream)
            audit.writerow(['tick', *nominal['controller']['state_order'], 'own_tau_w',
                            'own_tau_h', 'own_previous_w', 'own_previous_h',
                            'raw_w', 'raw_h', 'clipped_w', 'clipped_h'])
            controller = DesignObserverController(gain, runtime.limits, audit)
            metrics = evaluate(runtime, controller, 'push', condition.seed, path / 'rollout')
        row.update(status=metrics['status'], metrics=metrics, failed_checks=metrics['failed_checks'])
    except Exception:
        (path / 'error.txt').write_text(traceback.format_exc())
        row.update(status='ERROR', error=traceback.format_exc())
    row.update(ended_utc=utc_now(), elapsed_wall_s=time.monotonic()-start)
    write_json(path / 'receipt.json', row)
    write_json(case / 'result.json', row)
    print(f"{spec['id']} {row['status']} {row.get('failed_checks')} wall={row['elapsed_wall_s']:.3f}s", flush=True)
    return row


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args(argv)
    out = args.out.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    source = source_receipt('sim.gain_schedule.combined', argv)
    manifest_path = out / 'manifest.json'
    nominal, experiment, effects = load_experiment(CONFIG)
    declaration = {'matrix': matrix(), 'reference_config': nominal, 'effects': asdict(effects),
                   'design_policy': 'exactly two fresh nominal 2ms DARE designs, one per known length; frozen across all errors/seeds',
                   'acceptance': 'unchanged augmented_eval.evaluate; 10s or physical/numerical stop',
                   'limitation': 'sampled combined endpoint cases, not bounds or same gains as old .16 stress'}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if manifest['declaration'] != declaration or manifest['source']['git_commit'] != source['git_commit']:
            raise ValueError('Resume requires identical declared source and configuration')
    else:
        if list(out.iterdir()):
            raise ValueError('Fresh output must be empty or have a matching manifest')
        write_json(manifest_path, {'declaration': declaration, 'source': source, 'declared_utc': utc_now()})
    receipt = {'status': 'RUNNING', 'source': source, 'started_utc': utc_now(), 'pid': os.getpid()}
    run_path = attempt_directory(out / 'executions')
    write_json(run_path / 'run.json', receipt)
    started, code = time.monotonic(), 1
    try:
        # Both nominal designs exist BEFORE any actual perturbed rollout.
        designs = {}
        for length in (.12, .20):
            cfg = config_at_length(nominal, length)
            design_path = out / f'design-L{round(length*100):02d}.json'
            if design_path.exists():
                design = json.loads(design_path.read_text())
                gain = np.asarray(design['K_used'])
            else:
                gain, design = synthesize_augmented(cfg, effects, experiment['frozen_nominal']['K'])
                design.update(nominal_config=cfg, source=source,
                              design='fresh nominal known-length 2ms DARE; fixed across all actual perturbations',
                              limitation='controller never sees actual delay, torque, history, mass or inertia')
                write_json(design_path, design)
            designs[length] = cfg, gain
        rows = []
        for spec in declaration['matrix']:
            cfg, gain = designs[spec['length_m']]
            rows.append(run_case(spec, cfg, effects, gain, out))
            write_json(out / 'cases.json', rows)
        counts = {s: sum(r['status'] == s for r in rows) for s in ('PASS', 'FAIL', 'ERROR')}
        pairing = noise_pairing(rows, out)
        complete = not counts['ERROR'] and all(r['matched_timestamp_noise_prefix'] for r in pairing)
        write_json(out / 'summary.json', {'status': 'COMPLETE' if complete else 'INCOMPLETE',
                   'counts': counts, 'noise_pairing': pairing, 'cases': rows, 'source': source})
        code = 0 if complete else 1
    except Exception:
        (run_path / 'error.txt').write_text(traceback.format_exc())
        traceback.print_exc()
    finally:
        receipt.update(status='EXITED', exit_code=code, ended_utc=utc_now(),
                       elapsed_wall_s=time.monotonic()-started)
        write_json(run_path / 'run.json', receipt)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
