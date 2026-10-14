from pathlib import Path
p=Path('slides_report/main.tex'); s=p.read_text()
s=s.replace('13 October 2026','14 October 2026').replace('Known baseline before\\par camera adaptation','Known baseline; first\\par camera diagnostics').replace('slides 1--16; four backups follow','slides 1--17; four backups and references follow')
s=s.replace('Built (not yet run on the camera) / PLANNED','MEASURED recording / OPEN replay / PLANNED ROS 2').replace('Built: own recorder','Tested: own recorder').replace('Both are built but have never run on the camera.','Short recorder tests succeeded; offline ORB-SLAM3 crashed on its first frame. Patch 4 rebuild and replay remain pending. Live ORB-SLAM3 is unverified.')
s=s.replace('OPEN: built; camera data absent','OPEN: first-frame crash; rebuild pending').replace('Paths in the evidence table are provenance, not invitations to open reference decks during the meeting.','Sources remain in notes. Addendum §5 supersedes the earlier built-not-run N4B status.')
s=s.replace('Temporary Pi 5 & 4 GB RAM; 32 GB microSD; 5 V / 3 A supply.\\newline Target 8 GB platform has not been measured here.','Active Pi 5 & 8 GB board; measured 7.8 GiB RAM; same 32 GB microSD.\\newline Same 5 V / 3 A supply: under-voltage still present.')
s=s.replace('three compatibility patches.\\newline Isolated Pi copy; EuRoC example and settings unchanged.','Three build patches; patch 4 applied, rebuild pending.\\newline Isolated Pi copy; historical EuRoC example/settings unchanged.')
s=s.replace('No claim that the 8 GB target builds without swap; that remains inferred.','Addendum §1 measures 7.8 GiB on the active 8 GB Pi. Patch 4 rebuild was interrupted by power loss; no completed no-swap build is claimed.')
s=s.replace('\\item New D435i pixels and motion delivery.','\\item Sustained D435i delivery on a moving take.')
def frame(title, body):
 global s
 a=s.index('\\begin{frame}{'+title+'}'); b=s.index('\\end{frame}',a)+len('\\end{frame}')
 s=s[:a]+body.strip()+s[b:]
frame('D435i pipeline: built and linked; never camera-run',r'''
\begin{frame}{D435i recording: short tests work; long take failed}
\evidence{MEASURED tests / INFERRED storage bottleneck / OPEN qualification}
\begin{tabular}{@{}L{43mm}L{140mm}@{}}\toprule
\textbf{Take} & \textbf{Observation}\\\midrule
20 s still & Stereo + gyro + accel delivered for 19 s.\newline One $\sim$0.7 s gap in the final second at shutdown.\\[10pt]
100 s hand-moved & Unusable: 0.3--2.9 s gaps after 22 s.\newline Card wrote 16.6 MB/s vs 18.4 MB/s image payload.\\[10pt]
15 s into RAM & IR 29.99 Hz; max gap 33 ms; zero dropped frames.\newline Gyro 200.2 Hz; accel 101 Hz; copied with checksum OK.\\\bottomrule
\end{tabular}
\vfill\takeaway{Record into RAM, then copy: the 100 s RAM take is still unverified.}
\src{14 October addendum §§2--4; smoke\_ram.sh}
\note{Session-reported tests, not new experiments for this deck. Card take: 1.66 GB in 100 s, repeated gaps every roughly 5 s; blocking is a strong inference. No kernel under-voltage or USB errors during this take, but platform power unresolved. RAM test only 15 s. /dev/shm 3.9 GB; 100 s about 1.7 GB is a budget, not a guarantee. N4 stereo profile IR1+IR2 640x480 Y8/30, gyro/200, accel/100, emitter OFF. This does not replace N2 IR1-only 15 Hz or mandatory 300 s soak.}
\end{frame}

% 13
\begin{frame}{Offline replay: first-frame crash; patch 4 awaits rebuild}
\evidence{MEASURED crash / SOURCE-SUPPORTED diagnosis / OPEN verification}
\centering\begin{tikzpicture}[font=\normalsize]
\node[box,text width=46mm,minimum height=18mm] (a) at (0,0) {First-frame query\\IMU-init elapsed time};
\node[box,draw=fault,text width=51mm,minimum height=18mm] (b) at (6.4,0) {Uninitialized current\\keyframe pointer};
\node[box,draw=fault,text width=40mm,minimum height=18mm] (c) at (12.5,0) {SIGSEGV\\Replay stops};
\draw[flow](a)--(b);\draw[faultflow](b)--(c);
\end{tikzpicture}\par\bigskip
\raggedright\textbf{Patch 4:} initialize the pointer to \texttt{nullptr}.\par\medskip
Applied in the Pi build copy; power loss interrupted the rebuild.\par\medskip
Resume build, check linkage, then retry offline replay.
\vfill\takeaway{EuRoC did not call this query; its three-run result is unchanged.}
\src{14 October addendum §5; 15 October lab runbook}
\note{gdb: main → System::GetTimeFromIMUInit → LocalMapping::GetCurrKFTime. LocalMapping::mpCurrentKeyFrame uninitialized: null check reads garbage before first keyframe. Patch: KeyFrame* mpCurrentKeyFrame = nullptr; in include/LocalMapping.h, applied/committed only in Pi build copy. Rebuild stopped after 3 of about 27 library objects. Future command cmake --build build -j4 in ~/orbslam3/ORB_SLAM3; keep logs and verify intended library linkage. No execution or upstream edit for this deck.}
\end{frame}
''')
s=s.replace('\\evidence{Updated 14 October 2026 · 8 GB Pi now in use}','\\evidence{MEASURED / ASSUMED / OPEN · 14 October 2026}')
s=s.replace('\\textbf{Not fixed.} Interim: shorter, thicker USB-C cable or powered hub for the D435i. Real fix: 5 A supply.','\\textbf{Unresolved.} Use an adequate 5 A supply; retain power logs for each diagnostic run.')
s=s.replace('Old card: worst write 17 MB/s vs 18.4 MB/s stereo stream; no margin. & \\textbf{Waiting} for the 128 GB card: clone, then a sustained-write test of at least 30 MB/s.','100 s card take dropped frames; RAM test clean for 15 s. USB stick: 1.09 MB/s. & \\textbf{Demo workaround:} RAM then checksummed copy. Qualified dataset storage still needed.')
s=s.replace('\\textbf{Partly.} Prepare data collection now; the 4-hour IMU noise recording needs clean power.','\\textbf{OPEN.} Diagnostic room plot has no ground truth; accuracy remains unverified.')
s=s.replace('4 GB Pi needed 4 GB swap to build ORB-SLAM3. & \\textbf{Fixed by the 8 GB Pi} (7.8 GiB, no swap). EuRoC rerun done; numbers pending.','8 GB Pi: 7.8 GiB RAM; RAM recording allocation 3.9 GB. & 100 s take $\\sim$1.7 GB fits the budget. Recheck free memory; full take unverified.')
a=s.index('\\note{8 GB Pi findings were relayed'); b=s.index('\\end{frame}',a)
s=s[:a]+r'''\note{14 October addendum §§1,3,4,6 supersedes previous thread findings. No new EuRoC measurement or completed no-swap build is claimed. USB 2.0 stick data untouched. RAM is a bounded diagnostic workaround, not qualified persistent storage. MicroSD stages a copied take; transfer to Mac and verify checksums. Nominal geometry, ASSUMED noise and unknown camera--IMU offset remain. Ethernet loose; 8 GB Pi Wi-Fi unverified (§7).}
'''+s[b:]
frame('Next steps: restore prerequisites in order',r'''
\begin{frame}{15 October: prepare, rebuild, record into RAM}
\evidence{PLANNED diagnostic demo / OPEN exit criteria}
\begin{tabular}{@{}L{9mm}L{55mm}L{121mm}@{}}\toprule
 & \textbf{Action} & \textbf{Exit evidence}\\\midrule
1 & Set up 8 GB Pi & Adequate power; fixed Pi/cables; secure connection.\newline Fresh N1 $\rightarrow$ N2 $\rightarrow$ N3 evidence; gates stay OPEN.\\[10pt]
2 & Resume patch 4 build & Build exits zero; intended rebuilt library is linked.\newline Retain logs and source/binary hashes.\\[10pt]
3 & Record 100 s into RAM & Smooth early translation + gentle rotation; loop; still ending.\newline Review rates, stamps, gaps, logs and copied-take checksum.\\\bottomrule
\end{tabular}
\vfill\takeaway{Each step starts only when the previous step's exit evidence exists.}
\src{15 October lab runbook; 14 October addendum §§1,4,5,7}
\note{Owner must say CAMERA AVAILABLE before camera or ORB execution. No physical command runs for this build. Camera on blue USB3 port, >=5000M; Pi/connectors stationary. Wi-Fi on 8 GB Pi unverified; match saved host key. N1 → N2 → N3 required; N2 IR1 Y8 640x480/15, gyro/200, accel/100, staged 20 → 105 → mandatory 300 s. Thresholds unchanged: IR 14.25--15.75, gyro 190--210, accel 95--105 Hz; image gap <=0.20 s, motion gap <=0.05 s; positive stamps/steps, no missing frames, clean logs/content/review. Do not put 300 s stereo soak into 3.9 GB RAM. Demo is stereo 30 Hz, 100 s; it does not replace gates. Translate within 1--2 s; 20--30 s varied motion, 10--30 cm all axes, gentle +/-15--30 degree rotations; finish 5--10 s still. Check RAM/card capacity before capture. Acquisition local to Pi; SSH control only.}
\end{frame}
''')
frame('Then: immutable offline trials before live timing',r'''
\begin{frame}{Then: replay, plot, and review before live}
\evidence{PLANNED diagnostic demo / OPEN exit criteria}
\begin{tabular}{@{}L{9mm}L{55mm}L{121mm}@{}}\toprule
 & \textbf{Action} & \textbf{Exit evidence}\\\midrule
4 & Offline replay & Hashed input/settings; initialization; sustained tracking.\newline Review one stable map, resets, queues and nonempty trajectories.\\[10pt]
5 & Plot and review & Copy evidence to Mac; verify checksums; inspect trajectory.\newline Room take has no ground truth: accuracy unverified.\\[10pt]
6 & Live, then summary & Proceed only after offline review; same binary/settings.\newline Retain power/kernel logs, counters and finalized outputs.\\\bottomrule
\end{tabular}
\vfill\takeaway{Nominal-config development runs can inform diagnosis; they cannot qualify VIO.}
\src{15 October lab runbook; 14 October addendum §§5,8}
\note{Offline --bag ... --no-viewer; live omits --bag. Only one process owns camera. Retain warning: IMU Calibration is not available. Geometry nominal, noise ASSUMED, time offset unknown. Tracking state 2 and one map are diagnostic observations, not accuracy acceptance; largest-map export may hide resets. Audit order/domains/IMU bracketing. Offline wall duration/export pose rate do not measure live processing speed. Live needs normal shutdown/finalization and reviewed health/counters. Plot helper matches evo on EuRoC run1, 0.041461 m, a tooling check not room ground truth. Everything remains diagnostic OPEN until power/calibration and gates are evidenced.}
\end{frame}
''')
s=s.replace('Summary: keep the baseline; qualify the camera next','Summary: baseline retained; camera demo still OPEN').replace('\\item D435i recorder and adapter are built, but never camera-run.','\\item Short RAM capture works; 100 s capture remains unverified.').replace('\\item Resolve power/storage, then renew N1 $\\rightarrow$ N2 $\\rightarrow$ N3.','\\item Patch 4 rebuild and successful offline replay are pending.').replace('\\item Offline stereo/calibration qualification precedes live performance.','\\item Next: RAM take $\\rightarrow$ replay $\\rightarrow$ plot/review $\\rightarrow$ live demo.')
s=s.replace('Backup: three compatibility patches in an isolated copy','Backup: three build patches; runtime patch 4 pending').replace('\\\\[13pt]','\\\\[8pt]').replace('Preserves the prior C++11 bool-increment effect.\\\\\\bottomrule','Preserves the prior C++11 bool-increment effect.\\\\[8pt]\nCurrent keyframe $\\rightarrow$ \\texttt{nullptr} & Patch 4 avoids the first-frame uninitialized-pointer query.\\newline Applied in Pi copy; rebuild and replay unverified.\\\\\\bottomrule')
s=s.replace('No fresh build or source mutation occurred for this deck.','Addendum §5: patch 4 in include/LocalMapping.h; rebuild interrupted by power loss. No fresh build or source mutation occurred for this deck.')
s=s.replace('60--90 s stereo payload & About 1.11--1.66 GB per take, before recording overhead.','100 s stereo payload & About 1.84 GB before overhead; failed take wrote only 1.66 GB.').replace('Old write probe: 17--19 MB/s & Worst case below payload; nominal result has little margin.','100 s card take: 16.6 MB/s & Repeated gaps; microSD blocking strongly inferred.').replace('32 GB card: 13 GB free & Capacity alone does not prove sustained recording throughput.','RAM: 3.9 GB allocation & 15 s test clean; 100 s $\\sim$1.7 GB budget remains unverified.').replace('128 GB: planned 95 GB data & Roughly 55--90 takes in session estimate; not qualified storage.','USB stick: 1.09 MB/s & Too slow for recording; qualified dataset storage still needed.').replace('\\src{Session facts §F; N4B prep storage budget}','\\src{14 October addendum §§3,4,6; stereo payload calculation}')
s=s.replace('Exact image-only 95 GB / 1.65888 to 1.10592 GB gives about 57--86 full takes; report retains the session\'s rounded estimate 55--90 and labels it planned.','100 s image payload 1.8432 GB; failed 1.66 GB take and 1.7 GB RAM budget are not proof of full-frame delivery. Recheck retained counts and capacity.')
# Add one note-source per revised factual frame where historical source remains.
s=s.replace('\\src{Session facts §A--C; N4A/provenance.txt}','\\src{Session facts §A--C; N4A/provenance.txt; 14 October addendum §§1,5}')
s=s.replace('\\src{Session facts §A,C--F; N4A/REPORT.md and power\\_window.log; Pi setup thread findings 2026-10-14}','\\src{14 October addendum §§1,3,4,6; N4A/REPORT.md and power\\_window.log}')
p.write_text(s)
p=Path('slides_report/preamble.tex'); p.write_text(p.read_text().replace('snapshot 2026-10-13','snapshot 2026-10-14').replace('\\date{13 October 2026}','\\date{14 October 2026}'))
