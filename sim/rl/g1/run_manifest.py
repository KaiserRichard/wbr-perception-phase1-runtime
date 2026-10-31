"""Portable source/config identity and selected final-seed contract."""
import json
from pathlib import Path

from .protocol import HERE, identity, json_hash, write_json

FINAL_SEEDS = [0, 1, 2, 3, 4]
MANIFEST = 'run-manifest.json'


def seed_list(value):
    """CLI comma list or API integer sequence; each independent seed appears once."""
    try:
        seeds = [int(s.strip()) for s in value.split(',')] if isinstance(value, str) else list(value)
    except (ValueError, TypeError):
        raise ValueError('--seeds must be comma-separated integers from 0 to 4') from None
    if (not seeds or any(type(s) is not int or s not in FINAL_SEEDS for s in seeds)
            or len(set(seeds)) != len(seeds)):
        raise ValueError('--seeds must select distinct seeds from 0 to 4')
    return sorted(seeds)


def prepare_run(out, seeds=FINAL_SEEDS, config=None):
    out = Path(out)
    seeds = seed_list(seeds)
    config = json.loads((HERE/'config.json').read_text()) if config is None else config
    source = identity()
    manifest = dict(format=1, code_hash=json_hash(source), identity=source,
                    config=config, config_hash=json_hash(config), seeds=seeds)
    path = out/MANIFEST
    if path.exists():
        old = json.loads(path.read_text())
        if any(old.get(k) != v for k, v in manifest.items()):
            raise ValueError('Run manifest source/config/seed list mismatch; use the same part on resume')
        return old
    extra = {p.name for p in out.glob('seed-*')} - {f'seed-{s}' for s in seeds}
    if extra:
        raise ValueError(f'Run contains seeds outside selected part: {sorted(extra)}')
    manifest['status'] = 'PENDING'
    write_json(path, manifest)
    return manifest


def set_status(out, manifest, status):
    manifest = dict(manifest, status=status)
    write_json(Path(out)/MANIFEST, manifest)
    return manifest
