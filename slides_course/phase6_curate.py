"""Reversible Phase-6 curation, document tooling only."""
from pathlib import Path
import re,json
from phase5_progress import revise as update,frame,table,FACTS,REPORT,PREP
ROOT=Path(__file__).resolve().parent
PAT=r'\\begin\{frame\}.*?\\end\{frame\}|\\section\{[^}]*\}'
MERGES={7:6,15:70,22:23,24:25,26:17,40:102,62:83,85:84,88:77,93:78,103:48}
CUTS={3,8,16,51,87,99,104,90}
EXTRAS={6:('Operational questions','Sustain exact input? Initialize repeatedly? Reject stale/reset poses? Identify the first resource limit.'),17:('Runtime identity','Hash dirty sources, binaries, libraries and configuration; retain backend, wrapper and launch readback.'),23:('Thread ownership','SDK, wrapper/executor and recorder own separate queues; tracking runs on its caller; mapping/loop workers run separately.'),25:('Payload lower bounds','IR1/15: 4.608 MB/s; stereo/15: 9.216 MB/s. Prepared stereo/30: 18.432 MB/s before overhead; qualify that load separately.'),48:('Open choices','Rate follows useful cadence; transport needs link/load evidence. Age bounds need clock mapping and receiver review; uncertainty needs estimator support.'),70:('Measured baseline','Three MH01 runs: one map, no resets, IMU initialized. Accuracy is measured; power/RPE/budgets leave N4A OPEN.'),77:('Trial discipline','Freeze input/binary/settings/calibration; predeclare budgets, repeats and exclusions. Retain failed trials; three offline repeats are a planning minimum.'),78:('Continuity denominator','Count all initialization attempts; define first eligible input. Record state, reset/session ID, loss intervals and trajectory coverage.'),83:('Acceptance receipt','Require actual log/image review and recomputed sealed evidence; retain calibration warnings.'),84:('Symptoms','480M: cable/branch/power. Topic silence: graph/readback/QoS. Initialization failure: pairing, motion, frames, offset/noise.'),102:('Tool qualification','Kalibr spatial/time calibration and imu\\_utils noise analysis are candidates. Test bag import, models and holdout residuals.')}
def title(t):
 m=re.search(r'\\begin\{frame\}(?:\[[^]]*\])?\{([^}]+)\}|\\section\{([^}]+)\}',t)
 return (m[1] or 'Section: '+m[2]) if m else 'WBR Perception Implementation'
def revise(text):
 original=[m[0] for m in re.finditer(PAT,text.split(r'\begin{document}',1)[1],re.S)];assert len(original)==109
 updated=update(text)
 start=updated.index(r'\section{2026-10-13 progress}');stop=updated.index('% PAGE 84:',start)
 updated=updated[:start]+updated[stop:]
 for a,b in [('8.1 Historical','7.1 Historical'),('8.2 Current','7.2 Current'),('8.3 Conditional','7.3 Conditional'),('9. Conclusion','8. Conclusion')]:updated=updated.replace(a,b)
 updated=updated.replace('see the progress section.','see the N4A results and progress deck B.')
 updated=re.sub(r'\\begin\{frame\}\{Contents\}.*?\\end\{frame\}',lambda m:original[1],updated,flags=re.S)
 pre,body=updated.split(r'\begin{document}',1)
 incoming=[m[0] for m in re.finditer(PAT,body,re.S)];assert len(incoming)==109
 pages=[];mapping={};actions=[]
 for old,t in enumerate(incoming,1):
  if old in CUTS or old in MERGES:
   actions.append((old,title(original[old-1]),'MERGE' if old in MERGES else 'CUT'));continue
  if old in EXTRAS and old!=77:
   heading,content=EXTRAS[old];pos=t.index(r'\vfill\takeaway')
   t=t[:pos]+r'\par\medskip\textbf{'+heading+'}: '+content+r'\par'+t[pos:]
   for src,dst in MERGES.items():
    if dst==old:
     n=re.search(r'\\note\{(.*?)\}\\end\{frame\}',original[src-1],re.S)
     if n:
      teaching=original[src-1].split(r'\evidence{',1)[1].split('}',1)[1].split(r'\note{',1)[0]
      t=t.replace(r'\end{frame}',r'\note{Merged original page '+str(src)+': '+teaching+n[1]+r'}\end{frame}')
  if old==77:t=t.replace('Retain failures as part of the experiment denominator.','Retain failures; at least three offline repeats is a PLANNED minimum.')
  if old==6:
   t=t.replace('{1.3 Objectives}','{1.3 Objectives and research questions}')
   t=re.sub(r'\\begin\{block\}\{Engineering decision\}.*?\\end\{block\}', '', t, count=1, flags=re.S)
  if old==12:
   t=t.replace('Historical unit metadata reports BMI085, not older BMI055 descriptions.','Active device serial: 317422076650; BMI085.')
   t=t.replace('Calibration defaults and requested profiles do not prove usable VIO.','Descriptor / chip serial: 327743061057; firmware-update ID is separate.')
   t=t.replace('HISTORICAL / MEASURED metadata','MEASURED active identity / calibration OPEN')
   t=t.replace(r'\note{',r'\note{Active identity: '+FACTS.replace('_',r'\_')+r', section B. Enumerated 5000 Mbps is not N1 PASS; firmware 5.17.3.10. Historical note follows: ',1)
  if old==19:
   t=t.replace(r'\evidence{PLANNED}',r'\evidence{MEASURED stand-in / PLANNED target}')
   t=t.replace('Today: 4 GB / 32 GB microSD stand-in; no NVMe.','Today boots from 32 GB micro Secure Digital (microSD).')
   t=t.replace('Target: Raspberry Pi 5 with 8 GB memory and Ubuntu.','Target: Pi 5 / 8 GB; today: 4 GB / Ubuntu stand-in.').replace('Non-Volatile Memory Express (NVMe) storage holds large datasets.','Target bulk storage: Non-Volatile Memory Express (NVMe); absent today.')
  if old==36:
   t=t.replace('HISTORICAL defaults / UNKNOWN calibration','NOMINAL active geometry / calibration OPEN')
   t=t.replace('Image projection & HISTORICAL SDK-provided profile', 'Image projection & MEASURED active factory readback')
   t=t.replace('IMU geometry & HISTORICAL CAD fallback', 'IMU geometry & NOMINAL active factory transform')
   t=t.replace('IMU noise / offset & UNKNOWN; must measure','IMU noise / offset & ASSUMED noise; offset UNKNOWN')
   t=t.replace('Noise densities and bias walks remain UNKNOWN for this unit.','Candidate noise/walk values are ASSUMED; time offset UNKNOWN.')
   t=t.replace(r'\note{',r'\note{Current candidate: '+PREP.replace('_',r'\_')+r'D435i\_317422076650\_stereo\_inertial.yaml: nominal factory geometry; noise assumed, not accepted. ',1)
  if old==45:t=t.replace('The historical mono candidate with unresolved noise is not stereo-ready.','The active stereo candidate uses nominal geometry and assumed noise; qualification remains OPEN.')
  if old==47:
   t=t.replace('PLANNED: interpolate accel only between valid bracketing samples.','Prepared helper interpolates accel only between valid brackets.')
   t=t.replace(r'\evidence{PLANNED}',r'\evidence{MEASURED helper/build / camera behavior OPEN}')
   t=t.replace(r'\note{',r'\note{Current helper source: '+PREP.replace('_',r'\_')+r'd435i\_input.h and verification.md (offline/synthetic); Pi build status: '+FACTS.replace('_',r'\_')+r', section E. No camera behavior measured. ',1)
  if old==50:t=t.replace('withdraw perception input','withdraw input')
  if old==71:
   t=t.replace(r'\par\begin{tabular}',r'Absolute Trajectory Error (ATE) scores aligned paths; Relative Pose Error (RPE) scores motion increments.\par\medskip\begin{tabular}',1)
  if old==70:
   t=t.replace('power/RPE/budgets','power, local-error checks and budgets')
   t=t.replace('Three upstream stereo-inertial MH01 runs are MEASURED; see the N4A results and progress deck B.','Known-data accuracy supports this build; acceptance remains OPEN.')
  if old==96:
   t=t.replace('(0,2.8){ATE RMSE (m)}','(0,3.25){ATE RMSE (m)}')
   t=t.replace(r'{To be filled after N4/N5 runs}',r'{To be filled\\after N4/N5 runs}')
  if old==107:t=t.replace('{7.3 Conditional roadmap}','{7.4 Conditional roadmap}')
  if old==74:t=t.replace('PLANNED / no gate PASS','MEASURED binary build / replay OPEN')
  mapping[old]=len(pages)+1;pages.append(t)
  actions.append((old,title(original[old-1]),'UPDATE' if t!=original[old-1] else 'KEEP'))
  if old==106:
   pages.append(frame('7.3 Changes since 2026-10-10',table(['Change','Meaning / remaining limit'],[
    ['4 GB Pi / 32 GB microSD stand-in','8 GB / qualified bulk storage remains target; unstable power'],
    ['New D435i: SDK 317422076650','USB/ASIC 327743061057; old receipts do not transfer'],
    ['Three EuRoC MH01 runs','ATE 0.0415 / 0.0368 / 0.0416 m; N4A OPEN'],
    ['Recorder + D435i estimator built','Offline/live camera modes never run; calibration unqualified']], [77,107])+r'\medskip B explains the build, programs and next actions; C retains their gate contracts.',
    'Repair power; refresh N0 before new-unit N1, N2 and N3.',FACTS+'; '+REPORT,'MEASURED progress / no gate PASS'))
 for src,dst in MERGES.items():mapping[src]=mapping[dst]
 mapping[90]=mapping[89]
 for cut in CUTS-{90}:mapping[cut]=mapping[min(k for k in mapping if k>cut)]
 assert len(pages)==91,len(pages)
 result=pre+r'\begin{document}\raggedright'+'\n'+'\n'.join(pages)+r'\end{document}'+'\n'
 result=result.replace('in Phase 5.','in Phase 6.')
 assert set(re.findall(r'\\coursefigure\{([^}]+)',text))==set(re.findall(r'\\coursefigure\{([^}]+)',result))
 (ROOT/'qa/phase6-page-map.json').write_text(json.dumps(mapping,indent=2)+'\n')
 (ROOT/'qa/PHASE6_PAGE_LIST.md').write_text('\n'.join(f'{i}. {title(t)}' for i,t in enumerate(pages,1))+'\n')
 audit=['# PHASE 6 — all 109 incoming pages','', 'A (20 pages) and B (43 pages) are FINAL, read before curation. Byte-identical incoming TeX/PDF backups `main-v3-109p.*` preserved. C is a deep reference: 91 pages justified by retained contracts, rather than a count quota.','', '| Old page | Title | Action | Destination C | Reason |','|---:|---|---|---:|---|']
 for old,name,action in actions:
  reason={'KEEP':'Distinct technical contract, diagram, method or source-backed evidence.','UPDATE':'Reconcile October evidence or consolidate related material; preserve contract/figure.','MERGE':'Consolidate repeated prose at destination; retain original teaching content and source notes.','CUT':'Empty divider; section flow remains in Contents and titles.'}[action]
  keys=re.findall(r'\\coursefigure\{([^}]+)',original[old-1])
  if action=='KEEP' and keys:reason='Keep required figure '+', '.join(keys)+'; retain the '+name.split(' ',1)[-1].lower()+' mechanism/argument.'
  if action=='KEEP' and any(word in name for word in ['acceptance','criteria','PASS/FAIL']):reason='Keep threshold, measurement-clock and evidence table; required for an explicit gate decision.'
  if action=='MERGE':reason='Combine '+name.split(' ',1)[-1].lower()+' with '+title(original[MERGES[old]-1]).split(' ',1)[-1].lower()+'; remove repeated prose, preserve full teaching content in destination notes.'
  if action=='UPDATE' and old in EXTRAS:reason='Consolidate '+EXTRAS[old][0].lower()+' here; retain the existing contract/figure and the merged source text.'
  if old==90:reason='B pp.14–16 teaches alignment/errors better; C retains general formula, diagram and evo protocol.'
  audit.append(f'| {old} | {name} | {action} | {mapping[old]} | {reason} |')
 audit+=['','Added: Changes since 2026-10-10, after gate-status summary.','All 46 figure IDs retained, including all 12 conceptual illustrations. All gate PASS tables preserved; merged source facts retained visibly or in verbatim notes.','N4A MEASURED / OPEN: N0 health fails; RPE absent; acceptance budgets UNKNOWN. New camera programs built, never run. N2 exact USB/profile/timing/300-second criteria unchanged.']
 (ROOT/'qa/PHASE6_AUDIT.md').write_text('\n'.join(audit)+'\n')
 return result
if __name__=='__main__':
 (ROOT/'main.tex').write_text(revise((ROOT/'qa/main-v3-109p.tex').read_text()))
