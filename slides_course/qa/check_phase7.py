"""Offline document checks for Phase 7; no hardware or evaluator qualification."""
from pathlib import Path
import re,json,hashlib,runpy,sys
from unittest.mock import patch
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R))
frames=lambda s:re.findall(r'\\begin\{frame\}.*?\\end\{frame\}',s.split(r'\begin{document}',1)[1],re.S)
summary=(R/'qa/n4a-traj-eval-summary.md').read_text()
values=['0.013295','0.013559','0.014021','0.076464','0.076776','0.074883']
review=[]
for label,path,count,changed in [('course',R,91,[59,60,76,80]),('progress',R.parent/'slides_progress',44,[17,19,41])]:
 text=(path/'main.tex').read_text();before=(R/f'qa/phase7-baseline/{label}-main.tex').read_text()
 f=frames(text);b=frames(before)
 assert len(f)==len(b)==count
 actual=[i for i,(x,y) in enumerate(zip(f,b),1) if x!=y]
 assert actual==changed,(label,actual)
 for v in values:assert v in text and v in summary,v
 assert 'CALCULATED' in f[80-1 if label=='course' else 17-1]
 assert 'd3f9540' in text and 'no interpolation' in text
 assert not re.search(r'^!|Overfull|Underfull|Missing character|undefined',(path/'main.log').read_text(),re.M)
 assert not re.search(r'N4A RPE (?:remain[s]? UNKNOWN|is UNKNOWN)|No RPE result was measured today|RPE PLANNED',text)
 # Compare only the authorized changed frame bodies: all other source must be identical.
 strip=lambda s: re.sub(r'\\begin\{frame\}.*?\\end\{frame\}','FRAME',s,flags=re.S)
 assert strip(text)==strip(before)
 # Capture generator outputs without rewriting historical evidence or authored files.
 captured={}
 with patch.object(Path,'write_text',lambda p,s,*a,**k:captured.__setitem__(str(p.resolve()),s)):
  runpy.run_path(str(path/'build_deck.py'))
 assert captured[str((path/'main.tex').resolve())]==text,label+' regeneration mismatch'
 old=json.loads((R/f'qa/phase7-baseline/{label}-preview-hashes.json').read_text())
 for i in range(1,count+1):
  image=path/f'preview/page-{i:02d}.png';h=hashlib.sha256(image.read_bytes()).hexdigest()
  if i not in changed:assert h==old[image.name],(label,i,'unexpected render change')
  if i in changed:review.append({'deck':label,'page':i,'title':re.search(r'\\begin\{frame\}\{([^}]+)',f[i-1])[1],'sha256':h})
 if label=='course':
  for v in ['0.018874','0.023794','0.022288','D435i accuracy UNKNOWN']:assert v in f[79]
  for x,y in zip(f,b):
   if 'acceptance' in x or 'criteria' in x:
    assert re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}',x,re.S)==re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}',y,re.S)
  assert re.findall(r'\\coursefigure\{([^}]+)',text)==re.findall(r'\\coursefigure\{([^}]+)',before)
(R/'qa/phase7-reviewed-pages.json').write_text(json.dumps(review,indent=2)+'\n')
print('PASS: C 91 / B 44 pages; exact metric values, provenance and intended source scope; gate tables / figure IDs unchanged; generator reproduction exact; all unchanged page renders byte-identical; clean logs.')
