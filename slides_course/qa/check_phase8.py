"""Offline document QA: audit coverage, unchanged thresholds, notes, figures, PDF."""
from pathlib import Path
import sys,re,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import phase8_audit as p
source=(ROOT/'main.tex').read_text()
base=p.BASE.read_text()
assert hashlib.sha256(p.BASE.read_bytes()).hexdigest()=='f96ac47afb5362c51b5219d6a6b4a329b854657f8182bbada669722fab454089'
def frames(s):return re.findall(r'\\begin\{frame\}.*?\\end\{frame\}',s.split(r'\begin{document}',1)[1],re.S)
f=frames(source);b=frames(base)
assert len(f)==78 and len(b)==91
mapping={int(k):v for k,v in json.loads((ROOT/'qa/phase8-page-map.json').read_text()).items()}
audit=(ROOT.parent/p.AUDIT).read_text()
d={int(i):x for i,x in re.findall(r'^\| (\d\d) \| .*? \| (KEEP|BACKUP|CUT) \|',audit,re.M)}
assert len(d)==91
assert set(mapping)=={i for i,x in d.items() if x!='CUT'}
assert all(mapping[i]<=38 for i,x in d.items() if x=='KEEP')
assert mapping[91]==39
assert all(mapping[i]>=40 for i,x in d.items() if x=='BACKUP' and i!=91)
assert source.index(r'\begin{frame}{References}')<source.index(r'\appendix')
visible=[]
for i,s in enumerate(f,1):
    v,n=p.separate_notes(s);visible.append(v)
    assert not re.search(r'(?:experiments/|docs/|Source register:|Evidence:|Source:|Proposed evidence|Evidence / limit)',v),(i,'visible provenance')
    assert not re.search(r'(?<!\\)[\t\x08\x0c\r]',v),(i,'escaped Python control character')
    assert not re.search(r'\\textbf\{Evidence\}',v),(i,'evidence column')
assert all('Backup:' in p.title(f[i-1]) for i in range(40,79))
assert not any(x in '\n'.join(visible[:38]) for x in ['0.013295','0.076464','0.036 m (ten-run','0.018874','CALCULATED RPE','never run'])
assert 'RPE UNVERIFIED in permitted sources' in visible[mapping[76]-1]
# Compare all first-two cells of gate/ancillary evidence tables byte-for-byte.
count=0
for old,page in mapping.items():
    if old in p.MERGES:continue
    bv,_=p.separate_notes(b[old-1])
    for t in re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}',bv,re.S):
        if not re.search(r'\\textbf\{(?:Evidence(?: / limit)?|Proposed evidence)\}',t):continue
        nv=visible[page-1]
        for line in t.splitlines():
            if ' & ' in line:
                cells=line.split(' & ')
                assert len(cells)==3
                assert ' & '.join(cells[:2]) in nv,(old,'changed requirement/clock cells',cells[:2])
        assert t in f[page-1],(old,'original evidence table missing from notes')
        count+=1
assert count==13,count
for threshold in ['14.25--15.75','190--210','95--105',r'gap $\leq$0.20 s',r'gap $\leq$0.05 s','20 / 105 / 300 s stages complete']:
    assert threshold in '\n'.join(visible)
assert 'mandatory 300-second N2 soak' in visible[34]
# Every visible figure is unique, captioned and referenced, numbered in order by TeX.
keys=re.findall(r'\\coursefigure\{([^}]+)\}', '\n'.join(visible))
assert len(keys)==len(set(keys))==53
for key in keys:assert rf'\ref{{fig:{key}}}' in '\n'.join(visible),key
log=(ROOT/'main.log').read_text()
assert not re.search(r'^!|Overfull|Underfull|Missing character|undefined',log,re.M)
text=(ROOT/'qa/phase8-pdf-text.txt').read_text()
pages=re.split(r'^PAGE \d+\n',text,flags=re.M)[1:]
assert len(pages)==78,len(pages)
for i,s in enumerate(pages,1):
    assert re.search(rf'\b{i}/78\b',s),(i,'inconsistent page footer')
    assert not any(x in s for x in ['textquotesingle','experiments/','Source register:','Evidence:'])
fig_nums=[int(x) for x in re.findall(r'Figure (\d+):',text)]
assert fig_nums==list(range(1,54)),fig_nums
# Generator must reproduce exact reviewed source; generated QA inventory is deterministic.
regen=p.build()
assert regen==source,'generator mismatch'
print('PASS: offline document QA only')
print('78 frames: 38 main, references, 39 backups; all 91 audit IDs accounted for.')
print('13 threshold/clock tables unchanged; evidence columns retained in notes.')
print('53 unique consecutive figures, all referenced; 78 consistent page footers.')
print('No visible paths/source footers, stale main RPE/paper comparison, or build diagnostics.')
print('Preserved incoming source SHA-256; exact generator reproduction. No hardware qualification.')
