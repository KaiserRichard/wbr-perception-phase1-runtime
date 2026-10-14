"""Only numeric C-page references in B; preserve all other bytes."""
from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1]
P=R.parent/'slides_progress/main.tex'
old=(R/'qa/phase6-progress-before.tex').read_text()
assert P.read_text()==old,'B changed since the inspected snapshot; stop before editing'
mapping={int(k):v for k,v in json.loads((R/'qa/phase6-page-map.json').read_text()).items()}
pat=r'(\\src\{[^\n]+\}\{)([\d, \-]+)(\})'
changes=[]
def expand(s):
 nums=[]
 for item in s.split(','):
  bits=item.strip().split('--');nums.extend(range(int(bits[0]),int(bits[-1])+1))
 return nums
def compress(nums):
 nums=sorted(set(nums));groups=[];a=b=nums[0]
 for n in nums[1:]:
  if n==b+1:b=n
  else:groups.append(str(a) if a==b else f'{a}--{b}');a=b=n
 groups.append(str(a) if a==b else f'{a}--{b}')
 return ', '.join(groups)
def replace(m):
 new=compress([mapping[p] for p in expand(m[2])])
 changes.append({'source':m[1],'old':m[2],'new':new})
 return m[1]+new+m[3]
new,n=re.subn(pat,replace,old)
assert n==43,n
assert re.sub(pat,r'\1PAGES\3',old)==re.sub(pat,r'\1PAGES\3',new)
P.write_text(new)
(R/'qa/phase6-progress-reference-changes.json').write_text(json.dumps(changes,indent=2)+'\n')
print('Updated only 43 numeric C-page reference arguments in B; other source bytes unchanged.')
