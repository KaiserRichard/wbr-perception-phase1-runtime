#!/bin/bash
# Networked Mac only. Never run on the cafe PC. Output must be a new directory.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT="${1:?usage: build_bundle.sh /absolute/path/WBR-G1}"
mkdir "$OUT"
OUT="$(cd "$OUT" && pwd)"
export BUNDLE_ROOT="$ROOT" BUNDLE_OUT="$OUT"
python3 -m venv "$OUT/.build-venv"
PY="$OUT/.build-venv/bin/python"
"$PY" -m pip install 'pip==24.3.1'
mkdir -p "$OUT/bin" "$OUT/python" "$OUT/wheels" "$OUT/locks" "$OUT/source" "$OUT/licenses" "$OUT/runs" "$OUT/downloads"
curl --fail --location --retry 3 'https://github.com/astral-sh/python-build-standalone/releases/download/20241016/cpython-3.12.7+20241016-x86_64-pc-windows-msvc-install_only.tar.gz' -o "$OUT/downloads/python.tar.gz"
tar -xzf "$OUT/downloads/python.tar.gz" -C "$OUT/python" --strip-components=1
curl --fail --location --retry 3 'https://github.com/astral-sh/uv/releases/download/0.5.4/uv-x86_64-pc-windows-msvc.zip' -o "$OUT/downloads/uv.zip"
"$PY" - <<'PYUV'
import os, zipfile
from pathlib import Path
out = Path(os.environ['BUNDLE_OUT'])
with zipfile.ZipFile(out / 'downloads/uv.zip') as z:
    name = next(n for n in z.namelist() if n.split('/')[-1] == 'uv.exe')
    (out / 'bin/uv.exe').write_bytes(z.read(name))
PYUV
curl --fail --location --retry 3 'https://raw.githubusercontent.com/astral-sh/uv/0.5.4/LICENSE-MIT' -o "$OUT/licenses/uv-MIT.txt"
curl --fail --location --retry 3 'https://raw.githubusercontent.com/astral-sh/uv/0.5.4/LICENSE-APACHE' -o "$OUT/licenses/uv-APACHE.txt"
# Flatten the existing exact requirements, replacing torch with its CPU variant.
"$PY" - <<'PY'
import os
from pathlib import Path
root, out = Path(os.environ['BUNDLE_ROOT']), Path(os.environ['BUNDLE_OUT'])
lines = []
def read(path):
    for row in path.read_text().splitlines():
        row = row.split('#')[0].strip()
        if row.startswith('-r '): read(path.parent / row[3:])
        elif row: lines.append('torch==2.2.2+cpu' if row == 'torch==2.2.2' else row)
read(root / 'sim/rl/requirements.txt')
# pip cross-download does not evaluate Windows environment markers on a Mac.
# pandas requires this additional timezone wheel on Windows.
lines.append('tzdata==2025.2')
(out / 'locks/requested.txt').write_text('\n'.join(lines)+'\n')
PY
"$PY" -m pip download --platform win_amd64 --python-version 312 --implementation cp --abi cp312 --only-binary=:all: --extra-index-url https://download.pytorch.org/whl/cpu -r "$OUT/locks/requested.txt" -d "$OUT/wheels"
# No JAX/MJX/CUDA payload: G1 PPO uses ordinary CPU MuJoCo + CPU torch.
"$PY" "$ROOT/research/rl/bundle/package.py" "$ROOT" "$OUT"
# The build venv is Mac-specific; keep it outside the USB payload.
mv "$OUT/.build-venv" "$OUT/../$(basename "$OUT")-mac-build-venv"
python3 "$ROOT/research/rl/bundle/package.py" --seal "$OUT"
python3 - "$OUT" <<'PYZIP'
from pathlib import Path
import shutil, sys
out = Path(sys.argv[1])
shutil.make_archive(str(out), 'zip', root_dir=out.parent, base_dir=out.name)
PYZIP
echo "Built $OUT; conductor must exercise run.bat and resume.bat on Windows before release."
