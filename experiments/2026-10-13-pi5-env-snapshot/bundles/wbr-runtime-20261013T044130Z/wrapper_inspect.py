#!/usr/bin/env python3
"""Camera-free wrapper file/parameter inspection; never instantiate a camera node."""
import argparse
import ast
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from validation_common import baseline_text, run, sha256, utc, write_json


def inspect(root, baseline):
    import yaml
    package = root / 'package.xml'
    launch = root / 'launch/rs_launch.py'
    names = None
    for node in ast.parse(launch.read_text()).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'configurable_parameters' for t in node.targets):
            names = {entry['name'] for entry in ast.literal_eval(node.value)}
    if names is None:
        raise ValueError('Cannot inspect wrapper launch parameter declarations')
    params = yaml.safe_load(baseline_text(baseline))['/camera/camera']['ros__parameters']
    missing = sorted(set(params) - names)
    version = ET.parse(package).getroot().findtext('version')
    return {'scope': 'STATIC_FILES_ONLY_NOT_HARDWARE_PASS', 'utc': utc(), 'version': version,
            'package_root': str(root), 'parameter_names_missing': missing,
            'source_sha256': {str(p): sha256(p) for p in (package, launch, baseline)},
            'automatic_checks_pass': not missing and version == '4.58.4',
            'limitations': 'Installed node parameter readback and opened profiles still required after N2.'}


def validate_readback(actual, expected):
    failures = []
    for name, value in expected.items():
        # D435i has IR1/IR2, so no IR0 parameter may be declared. Absence is
        # allowed only for the disabled nonexistent stream, never a raw profile.
        if name == 'enable_infra' and name not in actual and value is False:
            continue
        if name not in actual or actual[name] != value or type(actual[name]) is not type(value):
            failures.append(f'{name}: requested {value!r}; read back {actual.get(name)!r}')
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-root', type=Path, default=Path('/opt/ros/jazzy/share/realsense2_camera'))
    parser.add_argument('--baseline', type=Path, default=Path(__file__).with_name('n3_baseline.yaml'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = inspect(args.package_root, args.baseline)
    except (OSError, ValueError) as error:
        result = {'scope': 'STATIC_FILES_ONLY', 'automatic_checks_pass': False, 'failure': str(error)}
    result['package_versions'] = run(['dpkg-query', '-W', 'ros-jazzy-realsense2-camera', 'ros-jazzy-realsense2-camera-msgs'])
    write_json(args.output, result)
    print(json.dumps(result))
    return 0 if result['automatic_checks_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
