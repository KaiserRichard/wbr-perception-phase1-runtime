"""Deck-only checks; these do not test sensors, SLAM or hardware readiness."""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
s=(root/'main.tex').read_text()
body=s.split(r'\begin{document}',1)[1]
frames=re.findall(r'\\begin\{frame\}(.*?)\\end\{frame\}',body,re.S)
assert len(frames)==45, len(frames)
assert s.count('\\note{Sources:')==45
assert all('\\note{' in f for f in frames)
for i,f in enumerate(frames,1):
    visible=f.split('\\note{')[0]
    if i<=41:
        for token in ('experiments/', 'docs/', '[F]', 'OPEN_DIAGNOSTIC', 'MEASURED', 'CALCULATED', 'sealed receipt', '\\texttt{'):
            assert token not in visible, (i,token)
assert not re.search(r'\{P(?:01|02|07|12)\}',s)
assert s.count('You should now be able to explain')==9
for name in ('P03','P04','P08','P10'):
    assert (root/'images'/f'{name}.png').read_bytes()==(root.parent/'slides_course/images'/f'{name}.png').read_bytes()
print('45 frames; 45 source notes; 9 recaps; no forbidden content tokens or images; reused assets byte-identical.')
