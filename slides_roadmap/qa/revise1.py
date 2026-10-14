from pathlib import Path
import re
root=Path('slides_roadmap')
s=(root/'qa/revision1-original/main.tex').read_text()
frames=re.findall(r'\\begin\{frame\}.*?\\end\{frame\}',s,re.S)
head=s[:s.index(r'\begin{document}')].replace(r'\textbf{Question}',r'\textbf{What}').replace(r'\textbf{Time / owner}',r'\textbf{Time}')
def frame(title,body,source='slides_roadmap/ROADMAP.md; slides_roadmap/research/R3_plan.md',note='Planning proposal only; bookings, hardware availability and acceptance remain unconfirmed.'):
    return '\\begin{frame}{'+title+'}\n'+body+'\n\\src{'+source+'}\n\\note{'+note+'}\n\\end{frame}'
def table(headers,widths,rows):
    return r'\small\renewcommand{\arraystretch}{1.18}'+'\n'+r'\begin{tabular}{@{}'+''.join('L{'+str(w)+'mm}' for w in widths)+r'@{}}\toprule'+'\n'+' & '.join(r'\textbf{'+x+'}' for x in headers)+r'\\\midrule'+'\n'+'\n'.join(' & '.join(row)+r'\\' for row in rows)+r'\bottomrule\end{tabular}'
def phase(title,gate,what,how,tools,hw,done,time,source,note):
    return frame(title,r'{\small\color{muted}'+gate+r'}\par\medskip'+'\n'+r'\phase{'+what+'}\n{'+how+'}\n{'+tools+'}\n{'+hw+'}\n{'+done+'}\n{'+time+'}',source,note)
# Use the original provenance-rich notes for revised phase pages.
notes=[re.search(r'\\note\{(.*)\}\s*\\end\{frame\}',f,re.S).group(1) for f in frames]
sources=[re.search(r'\\src\{(.*?)\}',f,re.S).group(1) for f in frames]
out=[]
intro=frames[0].replace('ATE;','trajectory error;').replace('advisory localization','optional position information').replace('Gates still open','Validation still open')
out.append(intro)
out.append(frame('The whole road: today to a supervised robot trial',r'''\centering
\begin{tikzpicture}[stage/.style={box,text width=40mm,minimum height=21mm,font=\normalsize},hw/.style={align=center,text width=40mm,font=\small,text=muted}]
\node[stage] (a) at (0,0) {Stable power\\and storage\\\small Week 1};
\node[stage] (b) at (4.9,0) {Trustworthy\\camera data\\\small Week 1};
\node[stage] (c) at (9.8,0) {Calibrate\\the camera\\\small Week 2};
\node[stage] (d) at (14.7,0) {SLAM on our\\own recordings\\\small Weeks 2--3};
\draw[flow](a)--(b);\draw[flow](b)--(c);\draw[flow](c)--(d);
\node[hw] at (0,-1.8) {Pi, supply, cooler,\\qualified storage};
\node[hw] at (4.9,-1.8) {D435i, USB 3 cable,\\same Pi and storage};
\node[hw] at (9.8,-1.8) {Measured target, stand,\\light, workstation};
\node[hw] at (14.7,-1.8) {Saved takes, Pi,\\workstation};
\node[stage] (e) at (14.7,-3.4) {SLAM live\\on the Pi\\\small Week 3};
\node[stage] (f) at (9.8,-3.4) {Health signal\\to the STM32\\\small Weeks 3--4};
\node[stage,fill=teal!10] (g) at (4.9,-3.4) {On the robot\\\small Weeks 4--5};
\node[stage,dashed] (h) at (0,-3.4) {Repeat / repair\\\small Week 6};
\draw[flow](d.east)--++(.45,0)|-(e.east);
\draw[flow](e)--(f);\draw[flow](f)--(g);\draw[flow,dashed](g)--(h);
\node[hw] at (14.7,-5.2) {Final cooling/data path,\\marked room route};
\node[hw] at (9.8,-5.2) {STM32 board, reviewed\\link, debugger};
\node[hw] at (4.9,-5.2) {WBR, mount, power rail,\\stand, stop, tether};
\node[hw] at (0,-5.2) {Same hardware,\\backup space};
\end{tikzpicture}
\par\medskip\raggedright\small Conditional weeks from 14 October. A failed step moves the schedule; it never shortens a test.''',note='Existing gates in order: preparation; N0--N3; N4A/N4B; N4C/N5; N6; N7 supported then separately authorized motion. N6 design may overlap after controller review; acceptance follows N5. Optional navigation is after this route.'))
out.append(frame('A few terms make the plan easier to read',table(['Term','Meaning in this roadmap'],[42,142],[
('SLAM','Simultaneous localization and mapping: estimate camera position while building a map.'),
('VIO / IMU','Visual-inertial odometry combines images with an inertial measurement unit: gyroscope and accelerometer.'),
('Calibration','Measure camera geometry, camera--IMU alignment, timing offset and sensor noise.'),
('ROS / bag / replay','Robot Operating System passes messages; a bag records them; replay feeds a saved recording back into software.'),
('Pose / frame / reset','Pose is position and orientation; frame defines axes and origin; reset starts a new estimate.'),
('Health / optional input','Health reports valid, lost or old estimates. Optional position information never owns balance or motor safety.')
]),source='docs/ARCHITECTURE.md; docs/DECISIONS.md; slides_roadmap/ROADMAP.md'))
out.append(phase('Stable power and storage','Preparation; platform check N0','Make the next lab visit usable.','Confirm parts, qualify the data path, prepare the target and prove file conversion on synthetic data.','Power/storage checks; offline image and IMU conversion; checksums for exact-copy verification.','8 GB Pi, 5.1 V/5 A supply, cooler, storage, local console; camera stays idle.','Named owners for every blocker; conversion preserves pixels, counts, units and timestamps on known samples.','2--5 engineer-days; parts and workstation waits are additional.',sources[2],notes[2]))
out.append(frame('Resolve these dependencies before camera time',table(['Dependency','Current state','Next owner action'],[34,72,78],[
('Power / access','5 V/3 A still under-voltages; ordered supply arrival unknown. Wi-Fi unverified; Ethernet loose.','Confirm suitable supply/cooling and local console or verified network access.'),
('ROS / storage','Camera wrapper not installed. USB stick measured 1.09 MB/s.','Review installation separately; borrow or buy and qualify large-bag storage.'),
('Calibration tools','ROS 1 bag conversion and long stationary recorder are untested.','Prove conversion offline; confirm workstation and recorder stop/recovery.'),
('Target / people','Measured target, overnight permission and controller owner unconfirmed.','Prepare print; name controller engineer; request conditional lab slots.')
])+r'\vfill\takeaway{The owner must explicitly authorize camera work before any capture.}',sources[2],notes[2]))
out.append(phase('Trustworthy camera data','Input checks N0 → N1 → N2 → N3','Prove the same camera can stream, record and replay reliably.','Check platform, USB and raw data in order; then record ROS messages and compare full replay.','Guarded sensor checks; reviewed ROS 2 Jazzy camera driver; recording/replay comparison.','Same Pi, stable supply/cooler, D435i, direct USB 3 cable and qualified bag storage.','USB reports at least 5000M; all three raw tests meet the next page; recorded and replayed counts/fields agree.','0.5--3 engineer-days; reserve 3--4 h, with diagnosis allowed to use the slot.',sources[3],notes[3]))
out.append(frame('What a trustworthy raw recording looks like',r'{\small\color{muted}Raw-data check N2; ROS record/replay N3 follows}\par\medskip'+table(['Check','Required visible result'],[47,137],[
('Exact raw profile','IR1: Y8 grayscale, 640×480 at 15 Hz; gyroscope 200 Hz; accelerometer 100 Hz.'),
('Three stages','20 seconds, then 105 seconds, then the mandatory 300-second soak.'),
('Measured rates','Image 14.25--15.75 Hz; gyro 190--210 Hz; accel 95--105 Hz.'),
('Gaps and order','Image gaps ≤0.20 s; motion gaps ≤0.05 s; increasing timestamps/frame numbers; no missing image frames.'),
('Health and stop','All original startup, boundary, content, kernel, power and normal-stop checks reviewed; raw logs retained.')
])+r'\vfill\takeaway{A short successful take does not replace the five-minute soak.}',sources[3],notes[3]))
out.append(phase('Calibrate the camera: collect usable measurements','Calibration acquisition within N4A / N4B','Measure this unit rather than rely on example defaults.','Record three target-motion takes; separate room trials and stationary noise data; inspect the first take.','Reviewed stereo recorder; future long-duration IMU recorder; verified lossless export.','Same camera/Pi, measured rigid A0 AprilGrid target, stand, light, calipers and backup space.','Three 120 s target takes and separate 90 s room trials have usable images and ordered timing; two copies match.','1--2 engineer-days; 3--4 h target slot; separately 30 min warm-up + 15--24 h stationary data.',sources[4],notes[4]))
out.append(phase('SLAM on our own recordings','Known reference N4A; camera replay N4B','Check repeatable output before going live.','Finish the existing crash-fix build; rerun the known EuRoC dataset; calibrate and replay three own-camera takes plus unused evaluation data.','Native ORB-SLAM3; Kalibr alignment/timing solver; Allan noise analysis; trajectory plots.','8 GB Pi with stable power; confirmed ROS 1/Kalibr workstation; immutable saved takes.','Build loads; three replay results show initialization, tracking losses and resets; settings and calibration have traceable reports.','2--4 engineer-days; add 2--5 days if import/tool compatibility fails.',sources[5],notes[5]))
out.append(phase('SLAM live on the Pi','Live estimator N4C; sustained resources N5','See whether current camera position arrives in time.','Hold settings fixed; run three repeats and a proposed 30-minute load with growing map, revisits and recovery.','Headless ORB; estimate-age, queue, drop/reset, CPU/RAM, temperature and power plots.','Final Pi/camera/cooling/data path, textured marked route, operator and reviewer.','Full logs account for inputs and outputs; queues do not grow; age/resource plots stay within limits approved before testing.','1--3 engineer-days; book 2--3 h after recorded-data review.',sources[6],notes[6]))
out.append(frame('Measure how old an estimate is',r'''\deckitems{
\item Estimate age is the time from image capture to the position result being available.
\item First prove how camera and Pi clocks relate. If that relation is unknown, age is unknown.
\item Report the median and the 95th/99th percentiles: values below which 50/95/99\% of samples fall.
\item Count every missing input, queued frame, tracking loss and reset alongside CPU, memory, heat and power.
}
\vfill\takeaway{A fresh heartbeat cannot make an old camera estimate fresh.}''',sources[6],notes[6]))
rows=[('ORB-SLAM3 stereo + IMU','5','3','3','68','Default: reuse current route'),('RTAB-Map own odometry','3','2','3','68','If occupancy mapping becomes first goal'),('OpenVINS','3','4','3','61','First challenger on identical saved data'),('Wheel/body + depth; no SLAM','2','5','2','56','Only if robot exports already work'),('ORB RGB-D','3','3','2','52','Needs another qualified input path'),('Basalt','2','3','3','53','Prove Linux ARM build/adapter advantage'),('VINS-Fusion','2','3','3','47','Port effort needs a demonstrated benefit'),('Kimera-VIO','2','2','3','48','More dependencies; defer for this demo')]
out.append(frame('Algorithm comparison: keep one default, test one challenger',r'\small Scores are engineering judgments from R1b, informed by R1; not measured Pi speed.\par\smallskip'+table(['Candidate','Demo','CPU','Motion','/100','Decision'],[51,13,12,17,13,70],rows)+r'\par\smallskip\small Scale 1--5: higher = better expected fit. Total weights: demo 30\%, CPU 20\%, motion 20\%, software support 15\%, navigation 10\%, licence 5\%.',source='slides_roadmap/research/R1_algorithms.md; slides_roadmap/research/R1b_algorithms_independent.md',note='Exact R1b components D,C,R,J,N,L: ORB 5,3,3,2,3,2=68; RTAB own 3,2,3,5,5,5=68; OpenVINS 3,4,3,3,2,2=61; no SLAM 2,5,2,3,2,3=56; RGB-D 3,3,2,2,3,2=52; Basalt 2,3,3,2,3,5=53; VINS 2,3,3,1,3,2=47; Kimera 2,2,3,1,4,5=48. Total = (30D+20C+20R+15J+10N+5L)/5. RTAB external odometry 54 is a later composition, not a second local estimator. DROID/DPVO class 36 fails the CPU-only deployment constraint. Research snapshot, not new benchmarks.'))
out.append(frame('What would make us change the algorithm?',r'''\deckitems{
\item Keep ORB-SLAM3 for the first position-estimation trial: build and input work already exist, but live Pi performance is still open.
\item If trusted data and correct calibration still miss approved age or continuity limits, spend at most 2--3 days diagnosing; compare OpenVINS on identical retained recordings.
\item Switch only if the challenger meets the same approved limits and its build, input conversion and failure behavior are verified.
\item If the first goal becomes an obstacle/occupancy map, compare RTAB-Map under the complete Pi workload.
\item A demonstrated wheel/body interface could make a smaller rolling demo faster; it changes the deliverable and does not prove camera VIO.
}''',sources[7],notes[7]))
out.append(phase('Health signal to the STM32','Receiver review and acceptance N6','Tell the controller when optional position information is usable.','Review the link, clocks, axes and invalidation rules; test missing, frozen, reset and corrupt input on synthetic cases.','Proposed bounded receiver; expected-versus-actual traces; local timeout on the STM32.','Named controller engineer, confirmed STM32H7 board, reviewed link and debugger.','Traces show old/wrong/corrupt input rejected and optional input withdrawn after Pi/link loss within approved limits.','2--4 engineer-days; design may overlap after review; acceptance follows sustained Pi tests.',sources[8],notes[8]))
out.append(phase('On the robot: mounting and supported tests','Supported integration N7','Verify power, mounting and controller independence.','Review mount/axes and power rail; test with motors disabled, then separately approved supported faults.','Reviewed receiver; power, controller-loop and estimate-age traces; controlled fault tests.','WBR, controller owner, battery/converter/fuse/link, mount/cooler, rated stand and independent stop.','Logs show no unexpected actuation/reset or control-loop violation; each fault removes optional input within approved limits.','1--3 engineer-days; book 3--4 h after receiver review.',sources[9],notes[9]))
out.append(phase('On the robot: supervised slow motion','Separately authorized motion N7','Repeat a slow trial while local balance remains independent.','Baseline the controller; use approved tethered trials and bounded manual room motion; test Pi loss and repeat startup/stop.','Operator runbook; checksummed utility bundle; Pi and STM32 traces.','Approved tether/cleared route, local stop, controller owner, operator and spotter.','Retained trials meet agreed motion/stop limits; Pi loss is handled; another operator reproduces startup, stop and rollback.','1--4 engineer-days; 2--3 h motion plus a separate repeat/repair slot.',sources[10],notes[10]))
out.append(frame('Hardware and lab bookings: bench and calibration',table(['Item','Phase','Status','Book when','Prepare first'],[40,29,31,32,46],[
('8 GB Pi + D435i','Input → live','Have per notes; confirm loan','W1; retain through W6','Same unit, console, USB 3 cable'),
('5.1 V/5 A supply + cooler','All Pi work','Supply ordered; cooler confirm with lab','Before first camera slot','Confirm arrival and power checks'),
('Large-data storage','Input → live','Borrow / buy; unqualified','Before W1 input slot','Sustained-write and replay checks'),
('128 GB microSD','Calibration only','Ordered; arrival unknown','Before target slot','Confirm exception; qualify short takes'),
('A0 grid, stand, light, calipers','Calibration','Print/buy; tools confirm with lab','W2: 3--4 h','Measure grid, prove import route'),
('Quiet bench + workstation','Calibration','Lab; confirm access','W2: 30 min + 15--24 h','Test IMU recorder, backup and stop')
]),note='No inventory or reservation verified by this task. Slow 64 GB USB 2 stick is not qualified large-data storage. Card exception is calibration/VIO-only. Acquire locally on Pi. Target: 6x6, 80 mm tags, spacing 0.25; measured A0 with rigid backing.'))
out.append(frame('Hardware and lab bookings: live Pi and robot',table(['Item','Phase','Status','Book when','Prepare first'],[40,29,31,32,46],[
('Marked textured room','Live Pi','Lab; confirm route','W3: 2--3 h','Replay accepted; age/resource limits'),
('STM32H7 + link + debugger','Health signal','Lab; board/owner unknown','W3--4; after review','Confirm board, voltage, pins and link'),
('WBR + mount + battery rail','Supported robot','Lab; stock/design unknown','W4: 3--4 h','Review mount/power; receiver tests'),
('Rated stand + independent stop','Supported robot','Lab; confirm suitability','With controller owner in W4','Approve fault procedure'),
('Tether + clear route + spotter','Slow robot motion','Lab; confirm suitability','W5: 2--3 h','Supported tests; separate motion approval'),
('Repeat/repair access + backups','Handoff','Lab; confirm access','W6: 2--4 h reserve','Preserve failures; list unresolved work')
])+r'\vfill\takeaway{These are requests to plan, not confirmed inventory or bookings.}'))
out.append(frame('Software stack by phase',table(['Phase','Software / purpose','What must be ready'],[40,86,58],[
('Preparation / input','Ubuntu + ROS 2 Jazzy; RealSense SDK/driver; existing raw checks; rosbag2 recorder/replay.','Review wrapper install; verify actual profiles and complete replay.'),
('Calibration','Lossless PNG + full-precision IMU export → ROS 1 bag; Kalibr; Allan sensor-noise analysis.','Conversion/workstation and long recorder are future reviewed tools.'),
('Saved-data / live SLAM','Native ORB-SLAM3 stereo-inertial; existing adapter; trajectory and health/resource plots.','Finish existing fix; preserve versions, settings and raw evidence.'),
('STM32 health','Small reviewed Pi health adapter + bounded STM32 receiver; synthetic rejection tests.','Message, link and limits need controller approval before implementation.'),
('Robot / handoff','Same frozen stack; startup/stop/rollback runbook; checksummed runtime bundle.','No balance authority on Pi; reuse a validated controller link.')
])+r'\vfill\takeaway{Defer extra estimator ports, Pi graphics, Docker and navigation until needed.}'))
out.append(frame('Next six weeks: preparation through live Pi',table(['Week','Owner / lab','Engineering work','Visible result'],[28,50,63,49],[
('1: 14--20 Oct','Confirm parts, camera loan, storage, console and workstation; request 3--4 h bench.','Prove conversion offline; target/recorder preparation; fresh input checks after authorization.','Reviewed input/replay receipts or a precise blocker.'),
('2: 21--27 Oct','Book target 3--4 h and separate overnight; same camera/Pi.','Three target takes, unused room takes, stationary data; first-take review and backups.','Usable captures, two matching copies; calibration reports or recapture decision.'),
('3: 28 Oct--3 Nov','Workstation; reserve marked route 2--3 h; agree controller limits.','Stable-power reference; repeated own-data replay; live and sustained-load measurements.','Tracking/reset and estimate-age plots; no growing queue; accept or diagnose.')
])+r'\par\medskip\small Dates are conditional targets. Unmet prerequisites carry forward; the soak and overnight recording remain unchanged.'))
out.append(frame('Next six weeks: controller, robot and contingency',table(['Week','Owner / lab','Engineering work','Visible result'],[28,50,63,49],[
('4: 4--10 Nov','Controller owner; confirmed WBR, board, link, stand and stop; 3--4 h.','Accept receiver after live/resource review; motors-disabled then approved supported faults; mount/power checks.','Rejection/fallback traces and unchanged local control within approved limits.'),
('5: 11--17 Nov','Separate motion approval; tether, route, operator/spotter; 2--3 h.','Supervised slow motion, Pi-loss trial, repeat startup/stop and review vibration/age.','Target: mounted tracking plus verified health/fallback behavior; no navigation claim.'),
('6: 18--24 Nov','Hold 2--4 h repair/repeat slot; extend camera loan if needed.','Resolve the failing layer; freeze utility/settings bundle; second-operator repeat.','Reproduction report, verified backups and explicit remaining blockers.')
])+r'\vfill\takeaway{If week 4 slips, finish supported tests before moving the robot.}'))
# Optional scope and final source page: retain primary links, simplify visible prose.
optional=frames[11].replace('Navigation is a separate scope after N7.','Navigation is a later project.').replace('Nav2 needs reviewed continuous odometry','Nav2, a ROS navigation stack, needs reviewed continuous odometry').replace('TF graph','coordinate-frame graph')
out.append(optional)
refs=frames[14].replace('source age','estimate age').replace('ROS 1/ROS 2 conversion','recording conversion').replace('RTAB-Map ROS 2','RTAB-Map mapping').replace('thresholds beyond N1--N3','later acceptance limits')
out.append(refs)
assert len(out)==23,len(out)
# Remove duplicate definition of SLAM on opening; glossary defines it once.
out[0]=out[0].replace('WBR means wheel-biped robot. SLAM means simultaneous localization and mapping.','WBR means wheel-biped robot. Snapshot: 14 October 2026.')
# Replace jargon only in visible content; keep exact instructions/provenance in notes.
for i,f in enumerate(out):
    visible,tail=f.split(r'\src{',1)
    visible=visible.replace('held-out','unused evaluation').replace('advisory','optional position').replace('source-age','estimate-age').replace('fixture','synthetic test case').replace('entry checks','preparation checks')
    out[i]=visible+r'\src{'+tail
(root/'main.tex').write_text(head+'\\begin{document}\n\\raggedright\n\n'+'\n\n'.join(out)+'\n\\end{document}\n')
