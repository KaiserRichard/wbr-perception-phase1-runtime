"""Offline document consistency checks; no hardware qualification."""
from pathlib import Path
import re,json,hashlib
R=Path(__file__).resolve().parents[1]
s=(R/'main.tex').read_text();old=(R/'qa/main-v3-109p.tex').read_text()
assert len(re.findall(r'\\begin\{frame\}',s.split(r'\begin{document}',1)[1]))==91
log=(R/'main.log').read_text()
assert not re.search(r'^!|Overfull|Underfull|Missing character|undefined',log,re.M)
figs=re.findall(r'\\coursefigure\{([^}]+)',s)
assert len(figs)==46 and len(set(figs))==46
assert set(figs)==set(re.findall(r'\\coursefigure\{([^}]+)',old))
assert set(figs)==set(re.findall(r'\\ref\{fig:([^}]+)',s.split(r'\begin{document}',1)[1]))
# Preservation of gate acceptance rows: compare all inherited threshold/measurement rows.
for title in ['4.2 N0: acceptance and diagnosis','4.3 N1: acceptance and diagnosis','4.5 N2: delivery criteria','4.5 N2: content, health and acceptance','4.7 N3: PASS/FAIL matrix','4.9 N4A: estimator acceptance contract','4.10 N4B: input and run criteria','4.11 N4C: live PASS/FAIL criteria','4.12 N5: measurement criteria','4.13 N6: planned acceptance table','4.14 N7: planned acceptance table']:
 def rows(text):
  frame=re.search(r'\\begin\{frame\}\{'+re.escape(title)+r'\}.*?\\end\{frame\}',text,re.S)[0]
  return re.search(r'\\begin\{tabular\}.*?\\end\{tabular\}',frame,re.S)[0]
 assert rows(s)==rows(old),title
for term in ['mandatory 300 s raw soak','14.25--15.75 Hz','190--210 Hz','95--105 Hz','0.20 s','0.05 s','5000M','CAMERA AVAILABLE','IMU Calibration is not available, default intrinsic and extrinsic will be used.','317422076650','327743061057','0.0415','0.0368','0.0416','87 / 178','To be filled after N4/N5 runs']:
 assert term in s,term
assert len(re.findall(r'^\| \d+ \|', (R/'qa/PHASE6_AUDIT.md').read_text(),re.M))==109
aux=(R/'main.aux').read_text()
nums=[int(n) for n in re.findall(r'\\newlabel\{fig:[^}]+\}\{\{(\d+)\}',aux)]
assert nums==list(range(1,47)),nums
print('OFFLINE DOCUMENT CHECK: 91 frames, 46 unique/referenced consecutive figures, 109 audit rows; all 11 gate acceptance tables byte-identical; exact N2 thresholds retained; clean TeX log.')
