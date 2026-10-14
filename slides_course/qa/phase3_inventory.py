"""Inventory the actual generated deck; original Phase-1 outline stays immutable."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
def inventory(text):
    body=text.split(r'\begin{document}',1)[1]
    pages=[]
    for m in re.finditer(r'\\begin\{frame\}(?:\[[^]]*\])?(?:\{([^}]+)\})?|\\section\{([^}]+)\}',body):
        pages.append(m[1] or ('Section: '+m[2] if m[2] else 'WBR Perception Implementation'))
    return pages
if __name__=='__main__':
    pages=inventory((ROOT/'main.tex').read_text())
    (ROOT/'qa/PHASE3_PAGE_LIST.md').write_text('\n'.join(f'{i}. {title}' for i,title in enumerate(pages,1))+'\n')
    print(f'{len(pages)} actual Phase-3 pages')
