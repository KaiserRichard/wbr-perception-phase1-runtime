#!/usr/bin/env python3
"""Create/verify a small Mac-canonical runtime bundle; no SSH or camera access."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from validation_common import sha256, utc, write_json

HERE = Path(__file__).resolve().parent
# Historical runners/results are deliberately excluded from future runtime execution.
FILES = '''validation_common.py n1_precheck.py wbr-d435i-iio-permissions.py
99-wbr-d435i.rules sdk_capture.py sdk_analysis.py sample_ir_checked.cpp camera_metadata.cpp
image_content.py health_monitor.py kernel_analysis.py storage_qualify.py
n3_metrics.py n3_observer.py n3_bag.py n3_record.py phase_gate.py
n3_baseline.yaml n3_topics.json n3_qos.yaml platform_inspect.py
bundle_runtime.py wrapper_inspect.py test_gate_tooling.py test_n2_tooling.py
test_n3_metrics.py test_takeover_tooling.py test_ros_offline.py
sdk-enumeration-full.txt sustained-sdk.log sustained-analysis.json
PHASE_A_RUNBOOK.md N3_PREPARATION.md'''.split()


def build(output):
    missing = [name for name in FILES if not (HERE / name).is_file()]
    if missing:
        raise RuntimeError('Incomplete bundle: ' + ', '.join(missing))
    output.mkdir(parents=True, exist_ok=False)
    def git(*args):
        return subprocess.check_output(['git', '-C', str(HERE), *args], text=True).strip()
    for name in FILES:
        shutil.copy2(HERE / name, output / name)
    manifest = {'scope': 'TOOL_BUNDLE_NOT_HARDWARE_PASS', 'created_utc': utc(),
                'canonical_git_revision': git('rev-parse', 'HEAD'),
                'canonical_branch': git('branch', '--show-current'),
                'canonical_worktree_status': git('status', '--short'),
                'source_sha256': {name: sha256(output / name) for name in FILES}}
    write_json(output / 'bundle-manifest.json', manifest)
    (output / 'SHA256SUMS').write_text(''.join(f'{digest}  {name}\n' for name, digest in
        {**manifest['source_sha256'], 'bundle-manifest.json': sha256(output / 'bundle-manifest.json')}.items()))
    return manifest


def verify(directory):
    manifest = json.loads((directory / 'bundle-manifest.json').read_text())
    for name, expected in manifest['source_sha256'].items():
        if Path(name).name != name or sha256(directory / name) != expected:
            raise RuntimeError('Runtime source changed: ' + name)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'verify'))
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    manifest = build(args.directory) if args.command == 'build' else verify(args.directory)
    print(json.dumps({'tooling': 'PASS', 'files': len(manifest['source_sha256']),
                      'canonical_revision': manifest['canonical_git_revision']}))


if __name__ == '__main__':
    main()
