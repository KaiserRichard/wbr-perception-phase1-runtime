from pathlib import Path
import json,re
r=Path(__file__).resolve().parents[1]
s=(r/'main.tex').read_text();pages=json.loads((r/'qa/revision1-pdf-text.json').read_text())
assert len(pages)==23
assert len(re.findall(r'\\begin\{frame\}',s))==23
assert len(re.findall(r'\\phase\{',s))==8
for i,p in enumerate(pages,1):
    assert f'{i}/23' in p['text']
    for term in ['CAMERA AVAILABLE','B1','source-age','fixture','entry checks','held-out','advisory']:
        assert term not in p['text'],(i,term)
for i in [4,6,8,9,10,14,15,16]:
    for label in ['What','How','Tools','Hardware','Done when','Time']:
        assert label in pages[i-1]['text'],(i,label)
assert r'\begin{tikzpicture}' in s
assert all(x in pages[6]['text'] for x in ['300-second','14.25','15.75','190','210','95','105','0.20','0.05'])
assert '5000M' in pages[5]['text']
log=(r/'main.log').read_text()
assert not re.search(r'Overfull|Underfull|Warning|Error|Missing character',log)
for candidate,values,total in [
 ('ORB',[5,3,3,2,3,2],68),('RTAB',[3,2,3,5,5,5],68),('OpenVINS',[3,4,3,3,2,2],61),
 ('Wheel/body',[2,5,2,3,2,3],56),('RGB-D',[3,3,2,2,3,2],52),('Basalt',[2,3,3,2,3,5],53),
 ('VINS',[2,3,3,1,3,2],47),('Kimera',[2,2,3,1,4,5],48)]:
 assert sum(w*v for w,v in zip([30,20,20,15,10,5],values))/5==total
for link in re.findall(r'\]\(([^)]+)\)',(r/'ROADMAP.md').read_text()):
 if '://' not in link:
  assert (r/link.split('#')[0]).exists(),link
assert len(list((r/'preview').glob('page-*.png')))==23
assert (r/'qa/main-v1.pdf').exists()
print('Document-only QA: 23 pages/footers; 8 six-row phase blocks; no prohibited visible jargon; exact raw rates/gaps/soak retained; score arithmetic and local links checked; clean LaTeX log; 23 rendered previews. No hardware validation.')
