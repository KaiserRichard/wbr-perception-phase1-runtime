#!/usr/bin/env python3
"""Offline structural checks and synthetic image-assignment fixtures only."""
from pathlib import Path
import importlib.util
import re
import tempfile
import json
import os

ROOT = Path(__file__).resolve().parents[1]
tex = (ROOT/'main.tex').read_text().split(r'\begin{document}',1)[1]
log = (ROOT/'main.log').read_text()
issues = re.findall(r'^.*(?:^!|Overfull|Underfull|Missing character|undefined).*$', log, re.M)
assert not issues, '\n'.join(issues)
assert len(re.findall(r'% PAGE \d+:',tex)) == 89, 'Preserved original-outline markers'
assert not re.search(r'Figure~.*?(?:explains the|illustrates)',tex)
assert '\t' not in tex, 'Accidental Python escape in generated TeX'
assert len(re.findall(r'\\begin\{frame\}',tex)) + len(re.findall(r'\\section\{',tex)) == 109
ids = re.findall(r'\\coursefigure\{([^}]+)\}',tex)
assert len(ids) == len(set(ids)), 'Repeated figure id'
assert set(re.findall(r'\\ref\{fig:([^}]+)\}',tex)) == set(ids)
assert len(re.findall(r'\{To be filled after N4/N5 runs\}',tex)) == 3
assert all(f'{{P{i:02}}}' in tex for i in range(1,13))
assert 'NO gate has PASSED' in (ROOT/'BRIEF.md').read_text()
for required in ['mandatory 300 s raw soak','14.25--15.75 Hz','190--210 Hz','95--105 Hz','0.20 s','0.05 s','5000M','CAMERA AVAILABLE','IMU Calibration is not available, default intrinsic and extrinsic will be used.']:
    assert required in tex, required
spec = importlib.util.spec_from_file_location('assign',ROOT/'images/assign.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
with tempfile.TemporaryDirectory(prefix='wbr-slides-synthetic-',dir=ROOT/'qa') as tmp:
    folder=Path(tmp)
    # Synthetic bytes test copy/ordering only, not image appearance or hardware.
    late=folder/'ChatGPT Image Oct 10, 2026, 03_12_45 PM.png'; late.write_bytes(b'synthetic-late')
    early=folder/'ChatGPT Image Oct 10, 2026, 09_02_01 AM.png'; early.write_bytes(b'synthetic-early')
    occupied=folder/'P01.png';occupied.write_bytes(b'preserved')
    module.assign(folder,dry_run=True)
    assert not (folder/'P02.png').exists()
    module.assign(folder)
    assert (folder/'P02.png').read_bytes()==early.read_bytes()
    assert (folder/'P03.png').read_bytes()==late.read_bytes()
    before={p.name:p.read_bytes() for p in folder.iterdir()}
    module.assign(folder)
    assert before=={p.name:p.read_bytes() for p in folder.iterdir()}
    fallback=folder/'ChatGPT Image unparseable.png'; fallback.write_bytes(b'synthetic-fallback');os.utime(fallback,(1,1))
    assert module.order_key(fallback)[0]==1
    extra=folder/'ChatGPT Image Oct 11, 2026, 01_01_01 PM.png';extra.write_bytes(b'synthetic-new')
    module.assign(folder)
    assert (folder/'P04.png').read_bytes()==fallback.read_bytes()
    assert (folder/'P05.png').read_bytes()==extra.read_bytes()
    assert occupied.read_bytes()==b'preserved'
print(f'OFFLINE TOOLING CHECK: 109 pages; {len(ids)} unique, referenced figures; clean TeX log; synthetic assignment ordering/idempotence/no-overwrite/mtime tests passed.')
