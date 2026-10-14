#!/usr/bin/env python3
"""Copy timestamp-ordered ChatGPT downloads into missing P01–P12 slots.

Originals and occupied slots are never overwritten. Assignment history is stored
in assignments.json. Chronological assignment still requires visual review.
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil

STAMP = re.compile(r'ChatGPT Image ([A-Za-z]{3} \d{1,2}, \d{4}),? (\d{1,2})[_:.](\d{2})[_:.](\d{2}) ?(AM|PM)', re.I)
MONTHS = {name: n for n, name in enumerate(('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'), 1)}

def order_key(path):
    match = STAMP.search(path.stem)
    if match:
        try:
            date, hour, minute, second, meridiem = match.groups()
            month, day, year = re.fullmatch(r'([A-Za-z]{3}) (\d{1,2}), (\d{4})', date).groups()
            hour = int(hour)
            if not 1 <= hour <= 12:
                raise ValueError('Invalid 12-hour timestamp')
            hour = hour % 12 + (12 if meridiem.upper() == 'PM' else 0)
            stamp = datetime(int(year), MONTHS[month.title()], int(day), hour, int(minute), int(second)).timestamp()
            return stamp, path.name
        except (ValueError, KeyError):
            pass
    return path.stat().st_mtime, path.name

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def assign(folder, dry_run=False):
    manifest = folder / 'assignments.json'
    history = json.loads(manifest.read_text()) if manifest.exists() else []
    if not isinstance(history, list):
        raise ValueError('assignments.json must contain a list')
    used_names = {item['original'] for item in history}
    used_hashes = {item['sha256'] for item in history}
    # Recognize previously copied assets even if no manifest exists.
    occupied = {f'P{i:02}' for i in range(1, 13) if any((folder / f'P{i:02}{ext}').exists() for ext in ('.png','.jpg','.jpeg'))}
    used_hashes.update(digest(p) for p in folder.iterdir() if p.stem in occupied and p.is_file())
    downloads = sorted((p for p in folder.iterdir() if p.is_file() and p.name.startswith('ChatGPT Image ') and p.suffix.lower() == '.png'), key=order_key)
    slots = iter(f'P{i:02}' for i in range(1,13) if f'P{i:02}' not in occupied)
    changed = False
    for original in downloads:
        sha = digest(original)
        if original.name in used_names or sha in used_hashes:
            continue
        slot = next(slots, None)
        if slot is None:
            print(f'No free P-id: {original.name} (left unchanged)')
            continue
        target = folder / f'{slot}.png'
        print(f'{original.name} -> {target.name}' + (' [dry run]' if dry_run else ''))
        if not dry_run:
            # Exclusive creation prevents an overwrite if another process fills a slot.
            with target.open('xb') as output, original.open('rb') as source:
                shutil.copyfileobj(source, output)
            history.append({'original': original.name, 'assigned': target.name, 'sha256': sha, 'visual_review': 'PENDING'})
            changed = True
        used_hashes.add(sha)
    if changed:
        temporary = manifest.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(history, indent=2) + '\n')
        temporary.replace(manifest)
    if not downloads:
        print('No ChatGPT-named PNG downloads; existing slots unchanged.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    assign(args.directory.resolve(), args.dry_run)

if __name__ == '__main__':
    main()
