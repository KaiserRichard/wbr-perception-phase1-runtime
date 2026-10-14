"""Phase-7 document-only update from the supplied calculated trajectory summary."""
import re

PROVENANCE = r'''Evidence: slides\_course/qa/n4a-traj-eval-summary.md; tools/trajectory\_eval/README.md. CALCULATED using traj\_eval.py from claude/project-thread-upkfjv, commit d3f9540, PR 2; tool not yet merged. Tool validation passed per its README, not rerun by this deck task. Flags: --t-max-diff 0.02 --t-offset 0 --align-both --rotation-ate --rpe-delta 1 --rpe-unit s. Shared EuRoC clock assumed; offset zero; active body-to-world poses in imu\_body, metres. 3,639 timestamp-associated pose pairs per run. For each eligible start, choose the first later reference timestamp at least 1 s later; no interpolation. SE(3) rigid alignment cancels in RPE. The tool's SE(3) ATE reproduces saved evo scores; its RPE pair policy differs from evo filters. Sim(3) additionally fits scale and is diagnostic, not the stereo-inertial paper comparator. Does not establish frames, extrinsics, synchronization, sensor readiness or gate PASS. No new camera, Pi or ORB execution.'''

ACCURACY = r'''\begin{frame}{5.8 Accuracy results}\evidence{MEASURED ATE / CALCULATED RPE / SOURCE-SUPPORTED paper}
N4A: MH01 body poses; SE(3) rigid alignment, 0.02 s association tolerance. [1,8]\par\medskip
\coursefigure{D76}{\begin{minipage}[c]{.46\linewidth}\centering
\begin{tikzpicture}[x=.90cm,y=.85cm,font=\normalsize]
\draw[flow] (0,0)--(8,0);\draw[flow] (0,0)--(0,2.5);
\foreach \y/\lab in {0/0,.9/0.02,1.8/0.04}{\draw (0,\y)--(-.1,\y);\node[anchor=east] at (-.15,\y){\lab};}
\node[anchor=west] at (0,3.25){ATE RMSE (m)};
\foreach \x/\y/\val/\run in {1.6/1.8675/0.0415/1,4/1.656/0.0368/2,6.4/1.872/0.0416/3}{\fill[teal] (\x,\y) circle (3pt);\node[above=2mm] at (\x,\y){\val};\node[below] at (\x,0){Run \run};}
\draw[dashed,navy] (0,1.62)--(8,1.62);
\node[anchor=west,text=navy] at (0,-.9){Paper: 0.036 m (ten-run median)};
\end{tikzpicture}\end{minipage}\hfill
\begin{minipage}[c]{.50\linewidth}\centering
\textbf{CALCULATED SE(3) RPE at 1 s}\par\medskip
\begin{tabular}{@{}L{15mm}L{35mm}L{35mm}@{}}\toprule
Run & Trans. RMSE (m) & Rot. RMSE (deg)\\\midrule
1 & 0.013295 & 0.076464\\[5pt]
2 & 0.013559 & 0.076776\\[5pt]
3 & 0.014021 & 0.074883\\\bottomrule
\end{tabular}\par\medskip
First later reference pose $\geq 1$ s; no interpolation.
\end{minipage}}{N4A global ATE and local RPE; the dashed ATE line is published.}
\par\medskip Sim(3) ATE: 0.018874 / 0.023794 / 0.022288 m (CALCULATED). It also fits scale; use SE(3) for the stereo-inertial paper comparison.
\par\medskip ATE mean: 0.040 m (three runs). D435i accuracy UNKNOWN.
\vfill\takeaway{Figure~\ref{fig:D76} supports this MH01 build; N4A remains OPEN.}
\note{Evidence: experiments/2026-10-13-n4a-euroc-mh01/REPORT.md; Campos et al., arXiv:2007.11898v2 Table II, verified in Phase 6. PROVENANCE}\end{frame}'''.replace('PROVENANCE', PROVENANCE)

def revise(text):
    text,n=re.subn(r'\\begin\{frame\}\{5\.8 Accuracy results\}.*?\\end\{frame\}',lambda _:ACCURACY,text,flags=re.S)
    assert n==1
    text=text.replace('Accuracy is measured; power, local-error checks and budgets leave N4A OPEN.',
                      'ATE is MEASURED; RPE is CALCULATED. Power and budgets leave N4A OPEN.')
    text=text.replace('N4A also lacks stable-power reruns and RPE.',
                      'N4A RPE is CALCULATED; stable-power reruns and reviewed budgets remain missing.')
    start=text.index(r'\begin{frame}{5.3 RPE and pair policy}')
    end=text.index(r'\end{frame}',start)+len(r'\end{frame}')
    frame=text[start:end].replace('PLANNED / no gate PASS','CALCULATED N4A / no gate PASS')
    frame=frame.replace(r'\note{Source:',r'\note{'+PROVENANCE+r' Source:',1)
    return text[:start]+frame+text[end:]
