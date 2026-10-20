"""Frozen authorization checks and portable evidence manifests; no synthesis."""

import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from sim.augmented import gain_hash
from sim.rl.environment import ROOT, PROTOCOL_PATH, load_protocol


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def new_output(path):
    path = Path(path).expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError('Evidence must be outside the repository')
    path.mkdir(parents=True, exist_ok=False)
    return path


def verify_authorization(path):
    auth = json.loads(Path(path).read_text())
    p = load_protocol()
    expected = {'sim/rl/protocol.json': auth['protocol_sha256'], **auth['runtime_sha256']}
    for name, digest in expected.items():
        if sha256(ROOT / name) != digest:
            raise ValueError(f'Authorization hash mismatch: {name}')
    if (auth['baseline'] != 'augmented_lqr' or auth['policy_seeds'] != p['training']['policy_seeds']
            or auth['steps_per_seed'] != p['training']['steps_per_seed']):
        raise ValueError('Wrong named baseline or training budget')
    result = Path(auth['baseline_evidence']) / 'result.json'
    if sha256(result) != auth['baseline_result_sha256']:
        raise ValueError('Archived baseline result mismatch')
    designs = {}
    for delay in p['plant']['fixed_delays_s']:
        spec = auth['designs'][str(round(delay * 1000))]
        if sha256(spec['path']) != spec['sha256']:
            raise ValueError('Archived LQR design mismatch')
        design = json.loads(Path(spec['path']).read_text())
        if (design['delay_s'] != delay or gain_hash(design['K_used']) != spec['K_sha256']
                or design['K_sha256'] != spec['K_sha256']):
            raise ValueError('Archived LQR matrix mismatch')
        designs[delay] = design
    return auth, designs


def versions():
    names = ['torch', 'stable-baselines3', 'gymnasium', 'numpy', 'mujoco', 'scipy']
    return {'python': sys.version, 'platform': platform.platform(),
            **{name: importlib.metadata.version(name) for name in names}}


def source_hashes():
    paths = sorted(set(ROOT.glob('sim/*.py')) | set(ROOT.glob('sim/rl/**/*.py')) |
                   set(ROOT.glob('sim/configs/*.json')) |
                   {PROTOCOL_PATH, ROOT / 'sim/rl/requirements.txt', ROOT / 'sim/requirements.lock'})
    return {str(p.relative_to(ROOT)): sha256(p) for p in paths}


def capture(out, authorization, full=False):
    auth, _ = verify_authorization(authorization)
    if full:
        changed = git('status', '--porcelain', '--untracked-files=all', '--', 'sim')
        if changed:
            raise ValueError(f'Commit simulation code before full execution: {changed}')
        pins = {'torch': '2.2.2', 'stable-baselines3': '2.3.2', 'gymnasium': '0.29.1',
                'numpy': '1.26.4', 'mujoco': '3.3.7', 'scipy': '1.15.3'}
        for name, pin in pins.items():
            if versions()[name].split('+')[0] != pin:
                raise ValueError(f'Backend version mismatch: {name}')
    hashes = source_hashes()
    for name in hashes:
        dest = out / 'source' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, dest)
    shutil.copyfile(authorization, out / 'authorization.json')
    for spec in auth['designs'].values():
        shutil.copyfile(spec['path'], out / Path(spec['path']).name)
    record = {'protocol_sha256': sha256(PROTOCOL_PATH), 'git_commit': git('rev-parse', 'HEAD'),
              'dirty_status': git('status', '--porcelain', '--untracked-files=all'),
              'source_sha256': hashes, 'model_config_sha256': hashes['sim/configs/assumed_planar.json'],
              'augmented_config_sha256': hashes['sim/configs/assumed_actuator_noise.json'],
              'authorization_sha256': sha256(authorization), 'versions': versions(),
              'command': [sys.executable, *sys.argv], 'seed_and_rng_mapping': load_protocol()['rng'],
              'baseline': auth['baseline'], 'designs': auth['designs']}
    write_json(out / 'provenance.json', record)
    return record


def manifest(out):
    hashes = {str(p.relative_to(out)): sha256(p) for p in sorted(out.rglob('*'))
              if p.is_file() and p != out / 'SHA256.json'}
    write_json(out / 'SHA256.json', hashes)
    return hashes
