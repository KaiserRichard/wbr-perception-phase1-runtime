"""Phase-5 progress layer over the reviewed Phase-3/4 deck. No runtime actions."""
import re

FACTS='experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md'
REPORT='experiments/2026-10-13-n4a-euroc-mh01/REPORT.md'
PREP='experiments/2026-10-13-n4b-d435i-prep/'
ENV='experiments/2026-10-13-pi5-env-snapshot/'
BUILD='experiments/2026-10-13-orbslam3-pi-build/'
def esc(s):
    return s.replace('_',r'\_').replace('%',r'\%').replace('&',r'\&')
def note(s):return r'\note{'+esc(s)+'}'
def items(*lines):return r'\deckitems{'+''.join(r'\item '+s for s in lines)+'}'
def block(title,text):return r'\begin{block}{'+title+'}'+text+r'\end{block}'
def cols(a,b):return r'\begin{columns}[T,onlytextwidth]\begin{column}{.48\textwidth}'+a+r'\end{column}\begin{column}{.48\textwidth}'+b+r'\end{column}\end{columns}'
def table(headers,rows,widths):
    return (r'\par\begin{tabular}{@{}'+''.join('L{'+str(w)+'mm}' for w in widths)+r'@{}}\toprule'+' & '.join(r'\textbf{'+h+'}' for h in headers)+r'\\\midrule\n'+''.join(' & '.join(row)+r'\\[6pt]' for row in rows)+r'\bottomrule\end{tabular}\par').replace(r'\n','\n')
def fig(key,code,caption):return r'\par\medskip\coursefigure{'+key+r'}{\begin{tikzpicture}[x=.90cm,y=.85cm,font=\normalsize,box/.append style={font=\normalsize}]'+code+r'\end{tikzpicture}}{'+caption+r'}\par'
def frame(title,body,take,source,status):
    keys=re.findall(r'\\coursefigure\{([^}]+)\}',body)
    if keys:take+=' (Figure~'+r'\ref{fig:'+keys[0]+'})'
    return r'\begin{frame}{'+title+r'}\evidence{'+status+'}\n'+body+r'\vfill\takeaway{'+take+'}'+note('Evidence: '+source+'. Deck authoring only; no camera, Pi or ORB program was executed in Phase 5.')+r'\end{frame}'
def replace_frame(text,title,new):
    pattern=r'\\begin\{frame\}\{'+re.escape(title)+r'\}.*?\\end\{frame\}'
    text,n=re.subn(pattern,lambda m:new,text,flags=re.S)
    assert n==1,(title,n)
    return text

def revise(text):
    text=text.replace('10 October 2026','13 October 2026')
    text=text.replace('% result, or a PUBLISHED figure from another setup. Nothing here is a Pi/STM32 measurement.', '% result, PUBLISHED figure, or explicitly sourced Pi MEASUREMENT; no STM32 measurement.')
    # Keep target hardware and historical evidence; update present-tense qualification claims.
    text=text.replace('Published reference trajectories support algorithm evaluation.','Published reference trajectories support evaluation; N4A now has measured trials.')
    text=text.replace('KNOWN published dataset / PLANNED baseline','KNOWN dataset / MEASURED N4A evidence')
    text=text.replace('No dataset download, build or ORB execution is authorized by this deck task.','The 2026-10-13 N4A report now records three historical executions; no execution is authorized by deck authoring.')
    text=text.replace('Document actual supply, cooling, memory and storage anew.','Today: 4 GB / 32 GB microSD stand-in; no NVMe.')
    text=text.replace('The active-cooler illustration is conceptual.', 'The active-cooler illustration is conceptual. Today: Pi 5 4 GB, 32 GB microSD, 5 V/3 A; source: '+esc(FACTS)+'.')
    text=text.replace('N4A EuRoC\\\\PLANNED','N4A EuRoC\\\\MEASURED / OPEN')
    text=text.replace('N4B offline stereo\\\\PLANNED','N4B offline stereo\\\\BUILT / OPEN')
    text=text.replace('N4C live stereo\\\\PLANNED','N4C live stereo\\\\BUILT / OPEN')
    text=text.replace('No Pi gate has passed; all execution still requires its explicit authorization.','N4A has measured evidence; no Pi gate has passed. New execution requires authorization.')
    text=text.replace('PLANNED stereo adapter','ROS stereo adapter: PLANNED')
    text=text.replace('planned stereo adapter','planned ROS stereo adapter')
    # Existing contracts remain intact; attach new evidence rather than silently change budgets.
    text=text.replace('The repo mono build example must be adapted explicitly to the pinned stereo target.','Three upstream stereo-inertial MH01 runs are MEASURED; see the progress section.')
    text=text.replace(r'\begin{frame}{4.9 N4A: camera-independent EuRoC baseline}\evidence{PLANNED / no gate PASS}',r'\begin{frame}{4.9 N4A: camera-independent EuRoC baseline}\evidence{MEASURED trials / gate OPEN}')
    text=text.replace('No accepted numeric budget means no performance PASS.','No accepted numeric budget means no performance PASS. N4A also lacks stable-power reruns and RPE.')
    text=text.replace('A EuRoC result validates the algorithm path; it says nothing about this camera transport.','MH01 accuracy is measured; N0 power health and this contract remain incomplete.')
    # N4B: retain acceptance table and provenance illustration, replace outdated converter path.
    text=replace_frame(text,'4.10 N4B: offline D435i stereo',frame('4.10 N4B: offline D435i stereo',
        block('Entry remains conditional',r'N3 plus reviewed IR2 stereo extension, accepted calibration and qualified data storage. The direct SDK candidate does not bypass these gates.')+
        block('Prepared candidate',r'\texttt{d435i\_record} writes stereo/motion to \texttt{stereo\_imu.db3} and \texttt{timestamps.csv}. The patched D435i example reads it with \texttt{--bag FILE --no-viewer}.')+
        r'\medskip Both binaries are built; neither has run on this camera. Native SDK replay is the present candidate; a separate ROS stereo conversion path remains PLANNED.',
        'Build and linkage establish executable readiness, not N4B input or estimator acceptance.',FACTS+'; '+PREP+'n4b_plan.md','MEASURED build / camera run OPEN'))
    text=replace_frame(text,'4.11 N4C: live stereo scheduling',frame('4.11 N4C: live stereo scheduling',
        cols(block('Entry / purpose',r'Accepted N4B evidence, renewed N1--N3 under stereo load, unchanged settings/calibration. Isolate live scheduling from input defects.'),block('Prepared candidate',r'The same patched \texttt{stereo\_inertial\_realsense\_D435i} binary reads the camera when \texttt{--bag} is omitted. \texttt{--no-viewer} disables the display.'))+
        r'\medskip Built, never run on this camera. Queue bounds, initialization/loss traces, valid time domains and source age remain unmeasured. A ROS live bridge is still PLANNED.',
        'A working executable cannot establish live freshness or sustained throughput.',FACTS+'; '+PREP+'n4b_plan.md','MEASURED build / live run OPEN'))
    # Fill measured results in their original pages; do not draw unavailable distributions.
    text=replace_frame(text,'5.8 Accuracy results',frame('5.8 Accuracy results',
        r'N4A: MH01, rigid alignment, body poses; 0.02 s association tolerance. [1,8]\par\medskip'+
        fig('D76',r'''
\draw[flow] (0,0)--(8,0);\draw[flow] (0,0)--(0,2.5);
\foreach \y/\lab in {0/0,.9/0.02,1.8/0.04}{\draw (0,\y)--(-.1,\y);\node[anchor=east] at (-.15,\y){\lab};}
\node[anchor=west] at (0,2.8){ATE RMSE (m)};
\foreach \x/\y/\val/\run in {1.6/1.8675/0.0415/1,4/1.656/0.0368/2,6.4/1.872/0.0416/3}{\fill[teal] (\x,\y) circle (3pt);\node[above=2mm] at (\x,\y){\val};\node[below] at (\x,0){Run \run};}
\draw[dashed,navy] (0,1.62)--(8,1.62);\node[anchor=west] at (8.3,1.62){Paper: 0.036 m};
\draw[flow] (12,0)--(17,0);\draw[flow] (12,0)--(12,2.5);\node[anchor=west] at (12,2.8){RPE (m): UNKNOWN};
\node[text width=49mm,align=center,text=muted] at (14.5,1.3){To be filled after N4/N5 runs};
''','N4A measured ATE; the dashed line is published, not our measurement.')+
        r'\medskip Mean: 0.040 m (4.0 cm). Paper Table II: 0.036 m, median of ten trials. D435i accuracy and N4A RPE remain UNKNOWN.',
        'Similar magnitude on MH01 supports the build; it does not qualify the robot.',REPORT+'; Campos et al., arXiv:2007.11898v2 Table II (verified 2026-10-13)','MEASURED N4A / SOURCE-SUPPORTED paper'))
    text=replace_frame(text,'5.9 Timing results',frame('5.9 Timing results',
        r'N4A wall durations: 301 / 282 / 284 s for 184 s of dataset time. These include vocabulary load; live under-voltage invalidates a speed verdict.\par\medskip'+
        fig('D77',r'''
\foreach \x/\lab in {0/Latency (ms),6/Queue (messages),12/Loss (frames)}{\draw[flow] (\x,0)--(\x+4.7,0);\draw[flow] (\x,0)--(\x,1.5);\node[anchor=south west] at (\x,1.7){\lab};}
\node[text=muted] at (8,-.8){To be filled after N4/N5 runs};
''','Wall duration is observed; per-frame latency, queues and loss remain unmeasured.')+
        r'\medskip Do not convert wall duration into P50/P95/P99 processing latency. Separate startup, steady tracking and shutdown on a stable-power rerun.',
        'Offline completion and real-time processing answer different questions.',REPORT,'MEASURED wall durations / timing qualification OPEN'))
    text=replace_frame(text,'5.10 Resource results',frame('5.10 Resource results',
        table(['N4A observed summary','Value / interpretation'],[
          ['Peak process RSS, runs 1 / 2 / 3','823 / 828 / 828 MiB'],
          ['Live under-voltage / throttling','87 / 178 five-second samples = 49\%'],
          ['Maximum sampled temperature',r'63 $^\circ$C; not a thermal time series']], [83,101])+
        r'\medskip'+fig('D78',r'''
\foreach \x/\lab in {0/CPU load (\%),6/Frequency (Hz),12/Queue depth}{\draw[flow] (\x,0)--(\x+4.7,0);\draw[flow] (\x,0)--(\x,1.0);\node[anchor=south west] at (\x,1.1){\lab};}
\node[text=muted] at (8,-.7){To be filled after N4/N5 runs};
''','Summaries have evidence; missing joined time-series panels stay empty.'),
        'Stable power is required before interpreting processor performance.',REPORT,'MEASURED N4A summaries / missing series UNKNOWN'))
    # Progress section: 12 content pages plus one divider. Keep existing method pages.
    pages=[]
    def add(title,body,take,source,status):pages.append(frame('7.'+str(len(pages)+1)+' '+title,body,take,source,status))
    add('What changed today',cols(block('Temporary platform',r'Pi 5: 4 GB, Ubuntu 24.04.4, ROS 2 Jazzy. Boot/data: 32 GB microSD; no NVMe. Supply: 5 V / 3 A.'),block('Two distinct milestones',r'Native ORB-SLAM3 build and three measured MH01 runs. D435i recorder and estimator binaries built; camera execution still OPEN.'))+
        r'\medskip Target remains 8 GB with qualified bulk storage. Under-voltage appeared in 87/178 run samples (49\%). No Pi gate has passed.',
        'An accuracy baseline and two built programs advance preparation, not camera acceptance.',FACTS+'; '+REPORT,'MEASURED evidence / all gates OPEN')
    add('New camera identity',table(['Identity field','Active unit / use'],[
        ['SDK device serial','317422076650: ROS serial\_no and gate selection'],
        ['USB descriptor serial','327743061057: udev / IIO device matching'],
        ['ASIC serial (separate field)','327743061057: same value, distinct provenance'],
        ['Firmware / USB enumeration','5.17.3.10 / 5000 Mbps; streaming unqualified']], [70,114])+
        r'\medskip Old unit: SDK 243322073847 / USB 251843061466. Its N1/N2 and calibration evidence do not transfer. New N1 stopped at the clock prerequisite; time was later synchronized.',
        'Enumerating 5000 Mbps once cannot replace new-unit gates or the 300 s soak.',FACTS+'; '+ENV+'ADDENDUM_CAMERA_SWAP.md','MEASURED enumeration / transport gate OPEN')
    add('Native build and compatibility patches',table(['Patch in isolated Pi copy','Why needed / limit'],[
        ['C++17; remove -march=native','Pangolin v0.9.1 compatibility; avoid host-specific architecture flags'],
        ['Disable Sophus unit-test targets','GCC 13/aarch64 array-bounds warning fails test -Werror; header use retained'],
        [r'\texttt{bool++} becomes \texttt{= true}','C++17 forbids bool increment; preserves its prior true-after-increment behavior']], [81,103])+
        r'\medskip Pinned upstream: 4452a3c. Build: about 71 min, --parallel 2, 4 GB RAM + 4 GB temporary swap. Checkout untouched; test-target exclusion is recorded, not a clean upstream test claim.',
        'These compatibility changes need known-data regression evidence before camera adaptation.',FACTS+'; '+BUILD+'build_orbslam3.sh','MEASURED build / INFERRED compatibility scope')
    add('EuRoC MH01 and ground truth',
        r'EuRoC is a public micro aerial vehicle benchmark; MH01 is an easy machine-hall flight. Stereo: 20 Hz; IMU: 200 Hz [2].'+
        fig('P5GT',r'''
\node[box,text width=32mm] (drone) at (0,0){Recorded drone\\MH01 flight};
\node[box,text width=42mm] (sensor) at (5.5,1.3){Stereo images + IMU\\3,682 pairs / 184 s};
\node[box,text width=42mm] (track) at (5.5,-1.3){Laser tracker\\independent position};
\node[box,text width=42mm] (orb) at (12,1.3){ORB-SLAM3 on Pi\\estimated trajectory};
\node[box,text width=42mm] (gt) at (12,-1.3){Dataset reference\\ground-truth trajectory};
\draw[flow] (drone.east)--(sensor.west);\draw[flow] (drone.east)--(track.west);\draw[flow] (sensor)--(orb);\draw[flow] (track)--(gt);
''','Two paths describe the same flight; only one uses our estimator.')+
        r'\medskip Ground truth is the independent reference, not the ORB output. Machine Hall uses laser position tracking; Vicon-room sequences use motion capture. Reference coverage and synchronization still need review.',
        'Known sensor data and an independent answer isolate the estimator from our D435i.',REPORT+'; ETH EuRoC official dataset page, verified 2026-10-13','KNOWN dataset / MEASURED local trial input')
    add('From recorded flight to an error number',table(['Step actually reported','Why it matters'],[
        ['Three headless upstream example runs','Same MH01, vocabulary and upstream EuRoC.yaml'],
        ['Export body/IMU trajectory','3,678 poses each; nanoseconds converted to seconds'],
        ['Convert reference to TUM format','Same body frame; xyz and quaternion order audited'],
        [r'\texttt{evo\_ape tum gt.tum est.tum -a}',r'Rigid alignment; add \texttt{--t\_max\_diff 0.02}']], [85,99])+
        r'\medskip TUM files contain time, xyz and quaternion qx qy qz qw. Compare poses at associated dataset epochs; Mac evaluation time is not a sensor epoch.',
        'Units, frames and time association must agree before a centimetre claim is meaningful.',REPORT,'MEASURED procedure / frame association audit')
    add('Why ATE needs alignment',
        r'The estimator chooses a map origin and heading. Special Euclidean group SE(3) alignment fits one rotation $R$ and translation $t$; scale stays fixed [1,8].'+
        fig('P5ATE',r'''
\node at (3,3.1){Before: different coordinates};\node at (12,3.1){After: one rigid transform};
\draw[thick,navy] (0,0)--(1,1.4)--(3,1.7)--(5,.7);
\draw[thick,teal] (1,.2)--(2.4,.2)--(3.9,1.5)--(4.1,3);
\draw[flow] (6.1,1.4)--node[above]{fit $R,t$}(8.2,1.4);
\draw[thick,navy] (9,0)--(10,1.4)--(12,1.7)--(14,.7);
\draw[thick,teal] (9,.25)--(10.2,1.2)--(12.1,1.95)--(14.25,.85);
\draw[faultflow] (9,0)--(9,.25);\draw[faultflow] (10,1.4)--(10.2,1.2);\draw[faultflow] (12,1.7)--(12.1,1.95);\draw[faultflow] (14,.7)--(14.25,.85);
\node[anchor=west,text=navy] at (0,-.65){Navy: reference};\node[anchor=west,text=teal] at (5,-.65){Teal: estimate};\node[anchor=west,text=fault] at (10,-.65){Orange: residuals};
''','Schematic only: alignment removes coordinate choice, not path deformation.')+
        r'\medskip $\displaystyle \mathrm{ATE}_{\mathrm{RMSE}}=\sqrt{\frac{1}{N}\sum_{i=1}^{N}\|Rp_i+t-q_i\|^2}$. Square each position residual, average, take the square root.',
        'Four centimetres is a trajectory-wide RMS position residual, not a maximum error.',REPORT+'; evo Metrics; Campos et al. [1]','KNOWN method / SYMBOLIC diagram')
    add('Three repeats and the paper comparison',table(['Run','ATE RMSE (m)','Keyframes','Peak RSS (MiB)'],[
        ['1','0.0415','126','823'],['2','0.0368','126','828'],['3','0.0416','129','828']], [22,64,43,51])+
        r'\medskip All three: one map, no resets, IMU initialized/refined, exit 0. Mean: 0.040 m; paper Table II: 0.036 m, median of ten runs [1].'+
        r'\medskip\par Thread scheduling can change keyframe/optimization order (INFERRED cause of variation). Same inputs do not guarantee bit-identical results. This single sequence supports comparable accuracy, not statistical equivalence.',
        'RPE measures local motion error over a chosen interval; it was not measured here.',REPORT+'; https://arxiv.org/pdf/2007.11898 Table II and Sec. VII-A, verified 2026-10-13','MEASURED runs / SOURCE-SUPPORTED paper')
    add('What N4A proves and leaves open',cols(block('Supported conclusion',r'On known MH01 inputs, the ARM64 build and patches produce centimetre-scale accuracy and repeated initialization. Camera, driver and new-unit calibration are absent from this test.'),block('Still unproven',r'D435i transport, calibration/time offset, live source age, RPE and robot integration. No stable-power throughput: 282--301 s wall for 184 s data, including startup.'))+
        r'\medskip N4A remains OPEN: inherited criteria leave accuracy/continuity budgets UNKNOWN, require ATE/RPE and carry N0 health forward. Stable-power reruns and acceptance review are still needed.',
        'The algorithm path works on this dataset; the full perception system remains unqualified.',REPORT+'; existing N0/N4A acceptance pages','MEASURED accuracy / gate OPEN')
    add('Recorder: freeze the new camera inputs',cols(block('Requested streams',r'\texttt{d435i\_record}: IR1 + IR2, 640$\times$480 Y8 at 30 Hz; gyro 200 Hz; accel 100 Hz. Direct librealsense, no ROS node.'),block('Artifacts and stamps',r'\texttt{stereo\_imu.db3} plus \texttt{timestamps.csv}. Preserve source frame numbers, timestamp domains and camera stamps; arrival timestamps have a different meaning.'))+
        r'\medskip Emitter OFF: projected dots move with the camera and can mislead natural-feature tracking. Image payload: $2(640)(480)(30)=18.432$ MB/s, about 1.1 GB/min before overhead.',
        'A frozen take permits repeatable diagnosis; recording and playback semantics remain untested.',FACTS+'; '+PREP+'d435i_record.cpp; '+PREP+'d435i_rs.h','MEASURED build / PLANNED streams / CALCULATED budget')
    add('One estimator: offline first, then live',
        r'\texttt{stereo\_inertial\_realsense\_D435i}: \texttt{--bag FILE} selects N4B; omit it for N4C. \texttt{--no-viewer} is headless.'+
        fig('P5PATH',r'''
\node[box,text width=28mm] (cam) at (0,0){D435i / USB3\\librealsense};
\node[box,text width=28mm] (rec) at (4.5,0){Recorder\\.db3 + CSV};
\node[box,text width=32mm] (play) at (9,0){Offline playback\\source epochs};
\node[box,text width=35mm] (input) at (14,0){Stereo ORB features\\IMU preintegration};
\node[box,text width=40mm] (track) at (14,-2.1){Tracking caller\\mapping / loop workers};
\node[box,text width=32mm] (traj) at (8,-2.1){Trajectory / states};
\node[box,text width=33mm] (evo) at (2,-2.1){evo + reference\\accuracy if available};
\draw[flow] (cam)--(rec);\draw[flow] (rec)--(play);\draw[flow] (play)--(input);\draw[flow] (input)--(track);\draw[flow] (track)--(traj);\draw[flow] (traj)--(evo);
''','Repeat one recording before adding live scheduling as another variable.')+
        r'\medskip Patch: interval IMU coverage; accel interpolation on gyro epochs; reject duplicate/backward stamps, gaps $>50$ ms and invalid brackets. Offline playback is not paced in real time.',
        'Repeatable offline input separates association defects from live backlog; neither mode has run.',FACTS+'; '+PREP+'stereo_inertial_d435i_file.patch; '+PREP+'d435i_input.h','MEASURED build / PLANNED execution path')
    add('Settings: readback is not calibration',table(['Candidate setting / quantity','Provenance / qualification'],[
        [r'$f_x=f_y=386.95$; $(c_x,c_y)=(321.03,241.04)$ px','MEASURED factory readback at 640 x 480'],
        ['Stereo baseline: 0.0499 m','MEASURED SDK geometry, not holdout validation'],
        ['Camera--IMU transform','NOMINAL factory geometry; time offset UNKNOWN'],
        ['Four IMU noise/walk settings','ASSUMED upstream values; needs Allan variance']], [93,91])+
        r'\medskip Candidate: \texttt{D435i\_317422076650\_stereo\_inertial.yaml}. Session warning: \textquotedbl IMU Calibration is not available\textquotedbl. Built and linked, never run on the camera; assumed values do not satisfy N4B calibration criteria.',
        'Measure spatial/time residuals and unit noise before claiming calibrated VIO.',FACTS+'; '+PREP+'calibration_notes.md; '+PREP+'D435i_317422076650_stereo_inertial.yaml','MEASURED readback / NOMINAL geometry / ASSUMED noise')
    add('Next physical take, power and storage',cols(block('PLANNED motion, after gates',r'After CAMERA AVAILABLE, stable power/storage and input review: 60--90 s take. First 20--30 s: 10--30 cm translations in all axes, $\pm15$--$30^\circ$ rotations; small loop; finish 5--10 s still.'),block('Power / storage blockers',r'5.1 V / 5 A supply and 128 GB V30/A2 card ordered. 32 GB card: 13 GB free; historical 17--19 MB/s writes give no margin for 18.4 MB/s stereo. New media still needs qualification.'))+
        r'\medskip Inspect ``IMU initialized'', state 2, one map and finite ordered poses; repeated ``Not enough motion... Reseting'' or LOST points to a failed attempt. Initialization needs motion and $\geq10$ keyframes; duration alone proves nothing.',
        'Repair power, qualify storage and new-unit gates; then record, repeat offline and consider live.',FACTS+'; '+PREP+'n4b_plan.md; '+ENV,'PLANNED physical recipe / MEASURED blockers')
    assert len(pages)==12
    marker='% PAGE 84:'
    text=text.replace(marker,r'\section{2026-10-13 progress}'+'\n'+'\n'.join(pages)+'\n'+marker)
    # Preserve original status section and illustration; bring summary and roadmap up to date.
    text=text.replace('{7.1 Historical evidence}','{8.1 Historical evidence}').replace('{7.2 Current evidence gaps}','{8.2 Current evidence gaps}').replace('{7.3 Conditional roadmap}','{8.3 Conditional roadmap}').replace('{8. Conclusion}','{9. Conclusion}')
    text=replace_frame(text,'8.2 Current evidence gaps',frame('8.2 Current evidence gaps',table(['Layer','Current status on 13 October'],[
        ['N0--N3: platform / new unit','OPEN; under-voltage and storage qualification unresolved'],
        ['N4A: EuRoC MH01','MEASURED accuracy; OPEN for power rerun / contract review'],
        ['N4B / N4C: D435i','Programs BUILT, never run; calibration unqualified'],
        ['N5--N7: metrics / health / STM32','Partial N4A metrics only; campaign and integration PLANNED']], [72,112]),
        'No Pi gate has passed; measured progress and qualification gaps coexist.',FACTS+'; '+REPORT,'MEASURED progress / qualification OPEN'))
    text=text.replace('Start with fresh camera-free N0 evidence.','Repair supply; refresh camera-free N0 evidence.')
    text=text.replace('N4A needs N0; stereo/calibration enables N4B/C and N5.','Rerun N4A with stable power; qualify stereo/calibration for N4B/C.')
    text=text.replace('Status: no Pi gate passed; next action is fresh N0 evidence.','Status: N4A accuracy measured; no Pi gate passed; repair power next.')
    text=text.replace('Methods are published; project results remain unmeasured.','N4A accuracy is measured; D435i and robot qualification remain OPEN.')
    text=text.replace('N5–N7','N5--N7')
    # Contents: add the progress section while retaining the established box layout.
    start=text.index(r'\begin{frame}{Contents}');end=text.index(r'\end{frame}',start)+len(r'\end{frame}')
    toc=r'\begin{frame}{Contents}\begin{tikzpicture}'
    for i,s in enumerate(['Introduction','Background','System design','Implementation by gate','Evaluation method','Engineering decisions','2026-10-13 progress','Current status and roadmap','Conclusion'],1):
        y=-i*.88
        toc+=r'\node[fill=navy!6,rounded corners=3pt,minimum width=190mm,minimum height=8mm,anchor=west] at '+f'(0,{y}) '+'{};'
        toc+=r'\node[fill=navy,text=white,minimum width=10mm,minimum height=8mm,anchor=west,font=\large\bfseries] at '+f'(0,{y}) '+'{'+str(i)+'};'
        toc+=r'\node[anchor=west,text=navy,font=\large] at '+f'(1.5,{y}) '+'{'+s+'};'
    toc+=r'\end{tikzpicture}\end{frame}'
    text=text[:start]+toc+text[end:]
    return text
