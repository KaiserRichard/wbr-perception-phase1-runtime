"""Frozen case ordering and protocol constants from research/rl/PLAN-v2.md."""
import hashlib
import itertools
import json
import math
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DT, POLICY_DT, DURATION = .002, .01, 10.
ORDER = [0, 3, 1, 2, 4, 5]
TOL = np.array([.02, .03, np.deg2rad(1), np.deg2rad(1), .05, .05])
DELAYS = [2, 5, 6, 8, 10]
COMMANDS = [0., -.1, .1, -.2, .2]


def seed_wall_cap(value):
    """Optional cumulative per-seed minutes; omission means unlimited."""
    if value is None:
        return None
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError('--seed-wall-cap-min must be a finite positive number')
    return value


def panel(development=False):
    factors = (DELAYS, [0., .2], [5.], [-6., 6.], [0]) if development else (
        DELAYS, COMMANDS, [-5., 5.], [-6., 6.], [0, 1])
    return [dict(delay_s=d/1000, command=v, pitch_deg=p, push_N=f,
                 variant=z, noise_seed=(2000 if development else 3000)+i)
            for i, (d, v, p, f, z) in enumerate(itertools.product(*factors))]


def json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)


def reference(t, command):
    return np.array([command*(.5*t*t if t < 1 else t-.5),
                     command*min(t, 1.), 0., 0., 0., 0.])


def errors(state, t, command):
    return np.asarray(state)[ORDER]-reference(t, command)


def model_config(variant=0):
    # Separate assumed candidate, never mutate/relabel legacy results or gains.
    cfg = json.loads((HERE/'model.json').read_text())
    if variant:
        for name in ('wheel_inertia', 'leg_inertia', 'body_inertia'):
            cfg['physics'][name]['value'] *= 1.2
        cfg['physics']['body_com']['value'] *= 1.1
    return cfg


def identity():
    paths = [*HERE.glob('*.py'), HERE/'model.json', HERE/'config.json',
             HERE/'cases.json', HERE/'smoke.json', ROOT/'research/rl/PLAN-v2.md',
             ROOT/'research/rl/params_manifest.yaml', ROOT/'sim/planar.py',
             ROOT/'sim/lqr.py', ROOT/'sim/augmented.py', ROOT/'sim/augmented_lqr.py']
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)}
