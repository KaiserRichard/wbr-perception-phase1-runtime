from pathlib import Path
import re
r=Path('slides_roadmap');s=(r/'main.tex').read_text();old=(r/'qa/revision1-original/ROADMAP.md').read_text()
intro='''## Owner-facing route and conditional six-week plan — revision 1

The deck uses plain phase names first. Gate codes below refer to the existing acceptance checks, not new gates. “Done when” on each phase slide points to observable recordings, plots, logs or repeatable procedures. Estimate age means elapsed time from image capture to available position output; it is unknown without a validated clock relationship. Unused evaluation data means recordings not used to fit calibration. Synthetic cases test software behavior only. Optional position information never owns balance or motor safety.

| Plain phase | Existing checks | Conditional week | Hardware |
|---|---|---|---|
| Stable power and storage | Preparation / N0 | 1 | Pi, supply, cooler, qualified storage, console |
| Trustworthy camera data | N0 → N1 → N2 → N3 | 1 | D435i, direct USB 3 cable, same Pi and data path |
| Calibrate the camera | Acquisition for N4A / N4B | 2 | Measured A0 target, rigid backing/stand, light, calipers, workstation |
| SLAM on our own recordings | N4A / N4B | 2–3 | Stable-power target Pi, immutable takes, Kalibr workstation |
| SLAM live on the Pi | N4C / N5 | 3 | Final cooling/data path, marked textured room |
| Health signal to the STM32 | N6 | Design 3–4; acceptance after N5 | Confirmed MCU board, reviewed link, debugger, controller engineer |
| On the robot | N7 supported, then separately authorized motion | 4–5 | WBR, reviewed mount/rail, rated stand, independent stop, then tether/operator/spotter |
| Repeat and repair | Repeat applicable existing checks | 6 | Same hardware and backup space |

Weeks start **14 October 2026**; these are conditional targets, not reservations or promised dates. Keep the same unit/configuration and carry unmet checks into the next week. Do not shorten the mandatory 300-second N2 soak or stationary recording to fit this calendar. Base effort remains about **11–28 engineer-days**, plus **2–5 days** if conversion/tools fail and unknown parts/lab queues. Overlap requires separate staff; it does not reduce total effort.

'''
def clean(x):
    x=x.replace(r'$\to$','→').replace(r'\%','%').replace('--','–')
    x=re.sub(r'\\textbf\{([^{}]*)\}',r'\1',x)
    return x.strip()
def extract(title):
    f=next(f for f in re.findall(r'\\begin\{frame\}.*?\\end\{frame\}',s,re.S) if r'\begin{frame}{'+title+'}' in f)
    t=f.split(r'\toprule',1)[1].split(r'\bottomrule',1)[0].replace(r'\midrule','')
    return '\n'.join('| '+' | '.join(clean(c) for c in row.strip().split('&'))+' |' for row in t.split(r'\\') if row.strip())
sections=[('Hardware and lab bookings: bench and calibration',5),('Hardware and lab bookings: live Pi and robot',5),('Software stack by phase',3),('Next six weeks: preparation through live Pi',4),('Next six weeks: controller, robot and contingency',4),('Algorithm comparison: keep one default, test one challenger',6)]
for title,n in sections:
    lines=extract(title).splitlines();intro+='### '+title+'\n\n'+lines[0]+'\n|'+'---|'*n+'\n'+'\n'.join(lines[1:])+'\n\n'
intro+='''Hardware statuses reflect the dated project notes; current availability must be confirmed with the lab. No purchase or booking was made. The 128 GB card exception is calibration/VIO-only; routine large bags still need separately qualified storage. Conversion, long-duration recorder and controller message/receiver are review proposals, not completed tools.

Scores reproduce the independent [R1b decision table](research/R1b_algorithms_independent.md), with technical risks checked against [R1](research/R1_algorithms.md). Scale: 1 poor fit/high burden, 3 plausible/unverified, 5 strong fit/low burden. The displayed total also includes software/Jazzy support, navigation and licensing: `(30D + 20C + 20R + 15J + 10N + 5L) / 5`. Full component values are in R1b and slide notes. These are inferred planning aids, not measured Pi speed or acceptance thresholds. ORB and RTAB tie at 68; the immediate localization objective breaks that tie in favor of existing ORB tools. Other R1b options are RTAB with external odometry (54, later composition) and learned DROID/DPVO (36, CPU-only deployment mismatch); neither is a second immediate estimator path.

Switch after trusted input/calibration and 2–3 days bounded diagnosis only if ORB repeatedly misses approved age/continuity limits and a verified OpenVINS build meets the same limits on identical data. A mapping-first objective favors a measured RTAB comparison; a proven wheel/body export can change the first robot-demo scope. Lower-scored Basalt/VINS/Kimera need a reproducible ARM build and meaningful matched-data advantage before reopening. Core capabilities trace to [ORB-SLAM3](https://github.com/UZ-SLAMLab/ORB_SLAM3), [OpenVINS](https://github.com/rpng/open_vins) and [RTAB-Map](https://github.com/introlab/rtabmap_ros). Upstream pages were checked during revision; hardware performance was not tested.

The detailed route below retains exact raw profiles, timing thresholds, calibration warning/identity provenance and implementation-review boundaries. This revision changes presentation, not the architecture or acceptance criteria.

'''
pos=old.index('## What the evidence says now')
new=old[:pos]+intro+old[pos:]
new=new.replace('### N0 → N1 → N2 → N3 — qualify the fresh physical input','### Trustworthy camera data — N0 → N1 → N2 → N3')
new=new.replace('### N4A / N4B — known-input baseline and calibrated offline camera replay','### Calibrate the camera; SLAM on our own recordings — N4A / N4B')
new=new.replace('### N4C / N5 — live VIO and source-age/resource evidence','### SLAM live on the Pi — N4C / N5')
new=new.replace('### N6 — review a health receiver before it can authorize optional information','### Health signal to the STM32 — N6')
new=new.replace('### N7 — mounted supported tests, then separately authorized slow motion','### On the robot — N7 supported tests, then separately authorized slow motion')
new=new.replace('qa/review-final-pdf-text.json','qa/revision1-pdf-text.json')
(r/'ROADMAP.md').write_text(new)
