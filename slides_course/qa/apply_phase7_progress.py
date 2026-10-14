"""Apply only authorized Phase-7 RPE edits to B source and its generator."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from phase7_rpe import PROVENANCE
root=Path(__file__).resolve().parents[2]
body=r'''
\begin{tabular}{@{}L{27mm}L{70mm}L{70mm}@{}}\toprule
\textbf{Run} & \textbf{RPE trans. RMSE (m)} & \textbf{RPE rot. RMSE (deg)}\\\midrule
1 & 0.013295 & 0.076464\\[5pt]
2 & 0.013559 & 0.076776\\[5pt]
3 & 0.014021 & 0.074883\\\bottomrule\end{tabular}\par
\medskip SE(3); shared EuRoC clock assumed, offset 0 s; association tolerance 0.02 s (3,639 matched pose pairs per run).
\medskip One endpoint per eligible start: first later reference pose $\geq1$ s later; no interpolation. These are \texttt{traj\_eval.py} results; its pair policy differs from evo's RPE filters.
\takeaway{About 1.3 cm RPE over 1 s describes local drift; ATE scores the aligned global path.}
\note{PROVENANCE}
'''.replace('PROVENANCE',PROVENANCE)
for name in ['main.tex','build_deck.py']:
 p=root/'slides_progress'/name;s=p.read_text()
 oldstart=s.index(r'\code{\# Mac evaluation; paths are placeholders for frozen files')
 oldend=s.index("\n\\src{" if name=='main.tex' else "\n''',N+'; eval/ape",oldstart)
 s=s[:oldstart]+body.strip()+s[oldend:]
 s=s.replace('MEASURED protocol / PLANNED RPE','MEASURED ATE protocol / CALCULATED RPE')
 s=s.replace('physical transport, other sequences, RPE and healthy real-time performance.',
             'physical transport, other sequences and healthy real-time performance. N4A RPE is now CALCULATED (p. 17).')
 s=s.replace('evo & Trajectory conversion, ATE/RPE; N4A/N5 & ATE used; RPE PLANNED',
             r'evo / traj\_eval & Global ATE / local RPE; N4A/N5 & ATE used; RPE CALCULATED')
 if name=='main.tex':
  s=s.replace(r'\src{[A] REPORT.md; eval/ape\_summary.txt}{76--77}',
    r'\src{C: qa/n4a-traj-eval-summary.md; d3f9540 / PR 2, unmerged}{76, 80}')
 else:
  s=s.replace("''',N+'; eval/ape\\_summary.txt','76--77')",
    "''',r'C: qa/n4a-traj-eval-summary.md; d3f9540 / PR 2, unmerged','76, 80')")
 p.write_text(s)
