"""Offline teaching-artifact scope checks; no sensor or runtime validation."""
from pathlib import Path
import hashlib, json, re, subprocess
root = Path(__file__).resolve().parents[1]
archive = root / 'qa/revision5-before'
for name, digest in json.loads((root / 'qa/revision5-before-hashes.json').read_text()).items():
    assert hashlib.sha256((archive / name).read_bytes()).hexdigest() == digest, name
old = (archive / 'main.tex').read_text()
new = (root / 'main.tex').read_text()
pattern = r'\\begin\{frame\}(.*?)\\end\{frame\}'
a = re.findall(pattern, old.split(r'\begin{document}', 1)[1], re.S)
b = re.findall(pattern, new.split(r'\begin{document}', 1)[1], re.S)
assert len(a) == len(b) == 49
assert [i + 1 for i, (x, y) in enumerate(zip(a, b)) if x != y] == [11]
assert old.split(r'\begin{document}')[0] == new.split(r'\begin{document}')[0]
assert [f.split(r'\note{', 1)[1] for f in a] == [f.split(r'\note{', 1)[1] for f in b]
question = 'If the D435i moves right, does the table corner move in the room, or only in the image?'
assert question in b[10]
assert len(list((root / 'preview').glob('page-*.png'))) == 49
changed = [i for i in range(1, 50) if (archive / f'preview/page-{i:02d}.png').read_bytes() != (root / f'preview/page-{i:02d}.png').read_bytes()]
assert changed == [11], changed
assert not re.search(r'Overfull|Underfull|Warning|^!', (root / 'main.log').read_text(), re.M)
status = subprocess.check_output(['git', 'status', '--short'], cwd=root.parent, text=True) + subprocess.check_output(['git', 'branch', '--show-current'], cwd=root.parent, text=True)
(root / 'qa/revision5-git-after.txt').write_text(status)
assert status == (root / 'qa/revision5-git-before.txt').read_text()
print('49 frames/previews; only page 11 source and rendered image changed.')
print('All source notes, theme, check question and archived inputs preserved; no TeX/layout warnings.')
print('Git status and branch unchanged. Offline teaching artifacts only.')
