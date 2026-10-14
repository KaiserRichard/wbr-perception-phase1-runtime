"""Verify the teaching revision's scope and artifacts; no runtime checks."""
from pathlib import Path
from PIL import Image, ImageChops
import hashlib,json,re,subprocess
root=Path(__file__).resolve().parents[1]
archive=root/'qa/revision3-before'
before=json.loads((root/'qa/revision3-before-hashes.json').read_text())
for name,digest in before.items():
    assert hashlib.sha256((archive/name).read_bytes()).hexdigest()==digest,name
old=re.findall(r'\\begin\{frame\}(.*?)\\end\{frame\}',(archive/'main.tex').read_text().split(r'\begin{document}',1)[1],re.S)
new=re.findall(r'\\begin\{frame\}(.*?)\\end\{frame\}',(root/'main.tex').read_text().split(r'\begin{document}',1)[1],re.S)
assert len(old)==45 and len(new)==47
for i in range(44):
    j=i if i<41 else i+2
    assert old[i]==new[j],(i+1,j+1)
for gate in range(8):
    assert sum(f.count(r'\textbf{N'+str(gate)+'.}') for f in new[41:43])==1,gate
assert all(f.startswith('{What to learn before each gate}') for f in new[41:43])
assert len(list((root/'preview').glob('page-*.png')))==47
comparisons=[]
for i in range(44):
    j=i if i<41 else i+2
    a=Image.open(archive/f'preview/page-{i+1:02d}.png').convert('RGBA')
    b=Image.open(root/f'preview/page-{j+1:02d}.png').convert('RGBA')
    assert a.size==b.size==(1280,719)
    delta=ImageChops.difference(a,b).convert('RGB')
    # Only the total/current page numbers are allowed to differ.
    delta.paste((0,0,0),(1100,680,1280,719))
    assert delta.getbbox() is None,(i+1,j+1,delta.getbbox())
    comparisons.append({'before':i+1,'after':j+1,'content_pixels_identical':True})
(root/'qa/revision3-changed-pages.json').write_text(json.dumps({'new_pages':[42,43],'references_page':47,'unchanged_content':comparisons,'excluded_footer_rectangle':[1100,680,1280,719]},indent=2)+'\n')
log=(root/'main.log').read_text()
assert not re.search(r'Overfull|Underfull|Warning|^!',log,re.M)
status=subprocess.check_output(['git','status','--short'],cwd=root.parent,text=True)+subprocess.check_output(['git','branch','--show-current'],cwd=root.parent,text=True)
(root/'qa/revision3-git-after.txt').write_text(status)
initial=(root/'qa/revision3-git-before.txt').read_text()
assert status.splitlines()[-1]==initial.splitlines()[-1]
added=sorted(set(status.splitlines())-set(initial.splitlines()))
removed=sorted(set(initial.splitlines())-set(status.splitlines()))
print('Concurrent Git status additions:',added,'; removals:',removed)
assert not removed
titles=[re.match(r'\{([^}]*)\}',f).group(1) for f in new]
(root/'qa/page_manifest.txt').write_text(''.join(f'{i:02d} {title}\n' for i,title in enumerate(titles,1)))
print('52 archived input files unchanged; 47 frames/previews; N0–N7 each occur once in the learning tables.')
print('44 prior source frames and rendered content regions identical; new pages 42–43; updated references page 47.')
print('Compared all prior content pixels except the page-number footer; no layout warnings; Git branch unchanged; concurrent status changes reported above.')
