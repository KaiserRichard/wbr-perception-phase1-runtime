"""Mac-side packaging, wheel hash lock and final payload manifest (stdlib only)."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
from email.parser import BytesParser


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def seal(out):
    paths = sorted(p for p in out.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
    (out / 'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(out).as_posix()}\n' for p in paths))


def package(root, out):
    shutil.copytree(root / 'sim', out / 'source/sim', ignore=shutil.ignore_patterns(
        '__pycache__', '*.pyc', '.DS_Store', '*.npz', '*.zip', '*.pkl'))
    for name in ('portable.py', 'launch.py', 'run.bat', 'resume.bat', 'CHECKLIST.md'):
        shutil.copy2(root / 'research/rl/bundle' / name, out / name)
    lock = []
    for wheel in sorted((out / 'wheels').glob('*.whl')):
        with zipfile.ZipFile(wheel) as z:
            metadata = BytesParser().parsebytes(z.read(next(n for n in z.namelist() if n.endswith('.dist-info/METADATA'))))
            lock.append(f"{metadata['Name']}=={metadata['Version']} --hash=sha256:{sha(wheel)}")
            for name in z.namelist():
                if 'license' in name.lower() or 'copying' in name.lower() or name.endswith('.dist-info/METADATA'):
                    if not name.endswith('/'):
                        dest = out / 'licenses' / wheel.stem / name
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(z.read(name))
    (out / 'locks/win-cpu.txt').write_text('\n'.join(lock)+'\n')
    (out / 'source/revision.txt').write_text(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True))
    (out / 'source/working.patch').write_bytes(subprocess.check_output(['git', 'diff', '--', 'sim'], cwd=root))
    (out / 'bundle.json').write_text(json.dumps({
        'ticket': 'C1-T11', 'python': '3.12.7+20241016', 'uv': '0.5.4',
        'platform': 'win_amd64/cp312', 'backend': 'cpu', 'training': 'legacy PPO v2 portability benchmark',
        'windows_validation': 'PENDING conductor', 'source_identity': 'SHA256SUMS covers copied working tree',
        'checkpoint_minutes': 5}, indent=2)+'\n')
    (out / 'licenses/UV-SOURCE.txt').write_text('uv 0.5.4: MIT OR Apache-2.0; https://github.com/astral-sh/uv/tree/0.5.4\n')
    (out / 'README.md').write_text((root / 'research/rl/bundle/CHECKLIST.md').read_text())


if __name__ == '__main__':
    if sys.argv[1] == '--seal': seal(Path(sys.argv[2]))
    else: package(Path(sys.argv[1]), Path(sys.argv[2]))
