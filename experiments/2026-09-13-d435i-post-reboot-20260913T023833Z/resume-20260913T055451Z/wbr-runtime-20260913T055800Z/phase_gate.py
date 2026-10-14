#!/usr/bin/env python3
"""Explicit N2 stage progression and reviewed acceptance; no implicit camera launch."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

import sdk_capture
from image_content import analyze as analyze_images
from sdk_analysis import analyze as analyze_csv
from validation_common import (camera_guard, evidence_hashes, provenance, receipt,
                               sha256, utc, verify_evidence, write_json)

HERE = Path(__file__).resolve().parent
STAGES = {20: 'N2_SMOKE', 105: 'N2_REPRODUCTION', 300: 'N2_SOAK'}
REVIEW_FIELDS = ('raw_logs_clean', 'images_coherent', 'startup_offsets_explained',
                 'imu_values_plausible', 'power_cooling_documented', 'calibration_warning_preserved')


def completed_capture(path, seconds, n1_digest):
    data = verify_evidence(path)
    if (data.get('stage') != STAGES[seconds] or data.get('duration_requested_seconds') != seconds
            or data.get('automatic_checks_pass') is not True or data.get('failures')
            or data.get('sdk_returncode') != 0 or data.get('sdk_orderly_shutdown') is not True
            or data.get('n1_sha256') != n1_digest):
        raise RuntimeError(f'{STAGES[seconds]} incomplete or belongs to another N1')
    timing = analyze_csv(Path(path).parent / 'frames.csv', seconds)
    if not timing['automatic_checks_pass']:
        raise RuntimeError('Recomputed whole-window timing failed')
    return data


def validate_review(review):
    if any(review.get(key) is not True for key in REVIEW_FIELDS):
        raise RuntimeError('Every required review assertion must be explicitly true')
    for key in ('reviewer', 'notes', 'power_supply', 'cooling', 'scene', 'calibration_provenance'):
        if not isinstance(review.get(key), str) or not review[key].strip():
            raise RuntimeError('Missing review field: ' + key)
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(review['utc'])).total_seconds()
    if not 0 <= age <= 7200:
        raise RuntimeError('Review UTC must be current and timezone-aware')


def accept(args):
    camera_guard(args.camera_available)
    n1 = receipt(args.n1_result, 'N1_PRECHECK')
    sdk_capture.validate_camera(n1['camera'])
    digest = sha256(args.n1_result)
    for seconds, path in ((20, args.smoke), (105, args.reproduction), (300, args.soak)):
        completed_capture(path, seconds, digest)
    images = analyze_images(args.soak.parent / 'image-content')
    if not images['automatic_checks_pass']:
        raise RuntimeError('Soak image evidence failed')
    review = json.loads(args.review.read_text())
    validate_review(review)
    for source in (args.smoke.parent, args.reproduction.parent, args.soak.parent, args.n1_result.parent):
        if args.output.resolve().is_relative_to(source.resolve()):
            raise RuntimeError('Acceptance directory must not be inside an input evidence directory')
    args.output.mkdir(parents=True, exist_ok=False)
    for name, source in [('smoke', args.smoke.parent), ('reproduction', args.reproduction.parent),
                         ('soak', args.soak.parent), ('n1', args.n1_result.parent)]:
        shutil.copytree(source, args.output / name)
    shutil.copy2(args.review, args.output / 'review.json')
    result = {'stage': 'N2_ACCEPT', 'verdict': 'PASS', 'utc_end': utc(),
              'hostname': n1['hostname'], 'boot_id': n1['boot_id'], 'camera': n1['camera'],
              'provenance': provenance(), 'failures': [],
              'scope': 'Reviewed raw transport only; VIO calibration remains unqualified',
              'evidence_sha256': evidence_hashes(args.output)}
    write_json(args.output / 'result.json', result)
    print(json.dumps({'stage': result['stage'], 'verdict': 'PASS', 'output': str(args.output)}))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    capture = sub.add_parser('n2')
    capture.add_argument('--seconds', type=int, choices=STAGES, required=True)
    capture.add_argument('--previous', type=Path)
    capture.add_argument('--image-sampler', type=Path, default=HERE / 'sample_ir_checked')
    capture.add_argument('--sdk-binary', type=Path, default=Path('/opt/ros/jazzy/bin/rs-data-collect'))
    accept_parser = sub.add_parser('accept-n2')
    for name in ('smoke', 'reproduction', 'soak', 'review'):
        accept_parser.add_argument('--' + name, type=Path, required=True)
    for command in (capture, accept_parser):
        command.add_argument('--camera-available', action='store_true')
        command.add_argument('--n1-result', type=Path, required=True)
        command.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        camera_guard(args.camera_available)
        if args.command == 'accept-n2':
            return accept(args)
        if args.seconds != 20:
            if not args.previous:
                raise RuntimeError('Previous successful stage is required')
            completed_capture(args.previous, {105: 20, 300: 105}[args.seconds], sha256(args.n1_result))
        return sdk_capture.run_capture(args)
    except (Exception, KeyboardInterrupt) as error:
        print(f'STOP: {type(error).__name__}: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
