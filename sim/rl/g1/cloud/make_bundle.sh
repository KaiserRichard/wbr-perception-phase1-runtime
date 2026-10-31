#!/usr/bin/env bash
# Bundle the current working tree, including uncommitted G1-PAR source.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/../../../.." && pwd)"
bundle_path="${1:-$script_dir/g1_code.zip}"
"${PYTHON:-python3}" - "$repo_root" "$bundle_path" <<'PY'
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

root, output = Path(sys.argv[1]), Path(sys.argv[2]).resolve()
paths = [root/p for p in (
    'sim/__init__.py', 'sim/planar.py', 'sim/lqr.py', 'sim/augmented.py',
    'sim/augmented_lqr.py', 'sim/configs/assumed_planar.json',
    'sim/requirements.lock', 'sim/rl/requirements.txt',
    'research/rl/PLAN-v2.md', 'research/rl/params_manifest.yaml',
)]
g1 = root/'sim/rl/g1'
for pattern in ('*.py', '*.json', '*.md', '*.sh', 'tests/*.py',
                'cloud/*.ipynb', 'cloud/*.md', 'cloud/*.sh'):
    paths.extend(g1.glob(pattern))
paths = sorted(set(paths))
manifest = {
    'format': 1,
    'git_head': subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
    'source': 'working tree; file hashes include uncommitted changes',
    'files': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
}
output.parent.mkdir(parents=True, exist_ok=True)
temporary = output.with_suffix(output.suffix+'.tmp')
with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in paths:
        archive.write(path, path.relative_to(root))
    archive.writestr('G1_BUNDLE_MANIFEST.json', json.dumps(manifest, indent=2)+'\n')
temporary.replace(output)
print(f'{output}: {len(paths)} source/config/test/doc files + manifest, {output.stat().st_size:,} bytes')
print('No environments, checkpoints, results, private evidence, or datasets included.')
PY
