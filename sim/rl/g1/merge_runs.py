"""Verify complete independent G1 parts and copy seeds 0..4 into a fresh root.

Use only your own trusted run folders (checkpoints contain Python pickle files).
No training, checkpoint rewriting or evaluation is performed by merging.
"""
import argparse
import json
from pathlib import Path
import pickle
import shutil
import uuid

from .protocol import identity, json_hash, write_json
from .run_manifest import FINAL_SEEDS, MANIFEST, seed_list


def validate_part(part):
    from .training import newest
    part = Path(part)
    manifest = json.loads((part/MANIFEST).read_text())
    seeds = seed_list(manifest['seeds'])
    if manifest.get('format') != 1 or manifest.get('status') != 'TRAINED':
        raise ValueError(f'Incomplete part: {part}')
    if (manifest['code_hash'] != json_hash(manifest['identity'])
            or manifest['identity'] != identity()):
        raise ValueError(f'Code hash mismatch (part/current source): {part}')
    if manifest['config_hash'] != json_hash(manifest['config']):
        raise ValueError(f'Config hash mismatch: {part}')
    if {p.name for p in part.glob('seed-*')} != {f'seed-{s}' for s in seeds}:
        raise ValueError(f'Seed directories differ from manifest: {part}')
    for seed in seeds:
        run = part/f'seed-{seed}'
        if any((run/name).exists() for name in ('failure.json', 'watchdog.json')):
            raise ValueError(f'Failed seed retained: {run}')
        declaration = json.loads((run/'declaration.json').read_text())
        receipt = json.loads((run/'receipt.json').read_text())
        dest = newest(run)
        marker = json.loads((dest/'complete.json').read_text())
        required = {'policy.zip', 'normalizer.pkl', 'state.pkl'}
        if not required.issubset(marker['files']):
            raise ValueError(f'Checkpoint missing required files: {run}')
        with (dest/'state.pkl').open('rb') as stream:
            state = pickle.load(stream)
        for record in (declaration, state):
            if (record['identity'] != manifest['identity'] or record['seed'] != seed
                    or record['config'] != manifest['config']):
                raise ValueError(f'Checkpoint/declaration source/config/seed mismatch: {run}')
        budget = manifest['config']['transitions']
        if (receipt['status'] != 'COMPLETE' or receipt['seed'] != seed
                or receipt['source_identity'] != manifest['identity']
                or any(steps != budget for steps in
                       (receipt['completed_steps'], state['completed_steps'], marker['steps']))):
            raise ValueError(f'Incomplete or mismatched seed: {run}')
    return manifest


def merge_runs(parts, out):
    parts = [Path(p).resolve() for p in parts]
    out = Path(out).resolve()
    if out.exists():
        raise FileExistsError(f'Merge requires a fresh output root: {out}')
    if not parts or any(out.is_relative_to(p) for p in parts):
        raise ValueError('Provide parts and an output root outside every input part')
    manifests = [validate_part(p) for p in parts]
    first = manifests[0]
    covered = []
    for manifest in manifests:
        if manifest['code_hash'] != first['code_hash']:
            raise ValueError('Code hash mismatch across parts')
        if manifest['config'] != first['config']:
            raise ValueError('Training config mismatch across parts')
        covered.extend(manifest['seeds'])
    if sorted(covered) != FINAL_SEEDS:
        raise ValueError(f'Merge requires each seed 0..4 exactly once; got {sorted(covered)}')
    # Validate everything before copying. Publish only a fully verified fresh root;
    # if an I/O failure occurs, retain staging evidence rather than delete data.
    staging = out.with_name(out.name+'.merging-'+uuid.uuid4().hex[:8])
    staging.mkdir(parents=True)
    provenance = []
    for i, (part, manifest) in enumerate(zip(parts, manifests)):
        for seed in manifest['seeds']:
            shutil.copytree(part/f'seed-{seed}', staging/f'seed-{seed}')
        # Preserve smoke/pilot/readiness and cloud receipts alongside each source
        # manifest, without making duplicate copies of the final checkpoints.
        shutil.copytree(part, staging/'parts'/f'part-{i}',
                        ignore=lambda folder, names: [n for n in names if
                            Path(folder) == part and n.startswith('seed-')])
        provenance.append(dict(source=str(part), seeds=manifest['seeds'],
                               manifest_hash=json_hash(manifest)))
    merged = dict(first, seeds=FINAL_SEEDS, parts=provenance)
    write_json(staging/MANIFEST, merged)
    validate_part(staging)
    staging.rename(out)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parts', type=Path, nargs='+', required=True,
                        help='Extracted part roots containing run-manifest.json and seed-N/')
    parser.add_argument('--out', type=Path, required=True, help='Fresh merged seeds-root')
    args = parser.parse_args()
    print(merge_runs(args.parts, args.out))


if __name__ == '__main__':
    main()
