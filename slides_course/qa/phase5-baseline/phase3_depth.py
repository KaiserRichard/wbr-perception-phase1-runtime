"""Phase-3 content layer; preserves v1 outline/preamble and historical evidence."""
import re


def revise(text):
    replacements = {}
    additions = {}
    def frame(title, body, take, source, status='PLANNED / no gate PASS'):
        keys = re.findall(r'\\coursefigure\{([^}]+)\}', body)
        if keys:
            initial = take if (len(take.split()[0]) > 1 and take.split()[0].isupper()) else take[0].lower()+take[1:]
            take = 'In Figure~\\ref{fig:'+keys[0]+'}, '+initial
        return (r'\begin{frame}{'+title+r'}\evidence{'+status+'}\n'+body+
                r'\vfill\takeaway{'+take+r'}\note{Source: '+source+r'. Commands are teaching examples only; none executed. UNKNOWN budgets require approval.}\end{frame}')
    def table(headers, rows, widths=None):
        widths = widths or [188/len(headers)-4]*len(headers)
        s=r'\par\begin{tabular}{@{}'+''.join('L{'+str(w)+'mm}' for w in widths)+r'@{}}\toprule'+'\n'
        s+=' & '.join(r'\textbf{'+h+'}' for h in headers)+r'\\\midrule'+'\n'
        for row in rows: s+=' & '.join(row)+r'\\[6pt]'+'\n'
        return s+r'\bottomrule\end{tabular}\par'
    def paragraphs(a,b):
        return r'\begin{columns}[T,onlytextwidth]\begin{column}{.48\textwidth}'+a+r'\end{column}\begin{column}{.48\textwidth}'+b+r'\end{column}\end{columns}'
    def block(title, content):return r'\begin{block}{'+title+'}'+content+r'\end{block}'
    def commands(lines):
        lines = [line + (r' \textbackslash{}' if i+1 < len(lines) and lines[i+1].startswith(r'\quad') else '') for i,line in enumerate(lines)]
        return block('Future commands / tools',r'{\ttfamily\normalsize '+r'\par '.join(lines)+'}')
    def diagram(key,code,caption):
        return r'\par\medskip\coursefigure{'+key+r'}{\begin{tikzpicture}[y=.8cm,font=\normalsize,box/.append style={font=\normalsize}]'+code+r'\end{tikzpicture}}{'+caption+r'}\par'
    def setp(p,title,body,take,source,status='PLANNED / no gate PASS'):
        replacements[p]=frame(title,body,take,source,status)
    def add(p,title,body,take,source,status='PLANNED / no gate PASS'):
        additions.setdefault(p,[]).append(frame(title,body,take,source,status))
    runbook='experiments/2026-09-12-pi5-native-sensor-validation/PHASE\_A\_RUNBOOK.md'
    native='docs/RPI5\_NATIVE\_PERCEPTION\_BRINGUP.md'
    offline='docs/ORB\_SLAM3\_OFFLINE\_PREPARATION.md; upstream pinned stereo\_inertial\_euroc.cc'
    # Shared visual semantics: real process boundaries, not an invented ROS estimator node.
    setp(20,'3.4 Sensor-to-pose execution path',
         r'Universal Serial Bus 3 (USB3) feeds the Software Development Kit (SDK).\par'+diagram('D20',r'''
\node[box,text width=36mm] (sensor) at (0,0) {D435i\\USB3 $\geq$5000M};
\node[box,text width=59mm] (wrapper) at (6,0) {Kernel / SDK wrapper\\SDK capture threads\\frame queue $\to$ publisher};
\node[box,text width=52mm] (dds) at (13,0) {ROS topics / DDS\\reader queues\\observer / recorder\\separate processes};
\draw[flow] (sensor)--(wrapper);
\draw[flow] (wrapper)--(dds);
\node[box,text width=59mm] (bag) at (6,-3.6) {Finalized local bag\\lossless derived inputs\\PLANNED stereo adapter};
\node[box,text width=52mm] (orb) at (13,-3.6) {ORB process\\TrackStereo caller\\mapping / loop workers};
\draw[flow] (dds.south)--(13,-1.9)--(6,-1.9)--(bag.north);
\draw[flow] (bag)--(orb);
''','The offline branch isolates estimator behavior from live queues.')+
         r'\medskip IR1/info 15, gyro 200, accel 100 Hz; readers: best effort / volatile.',
         'N3 is IR1-only; the stereo estimator branch requires a reviewed IR2 extension.',runbook)
    add(20,'3.4 Topic and type contract',table(['Topic below /camera/camera','Message / cadence','Reader policy'],[
        [r'\texttt{infra1/image\_rect\_raw}',r'\texttt{sensor\_msgs/msg/Image}; 15 Hz','Best effort / volatile'],
        [r'\texttt{infra1/camera\_info}',r'\texttt{sensor\_msgs/msg/CameraInfo}; 15 Hz','Best effort / volatile'],
        [r'\texttt{gyro/sample}; \texttt{accel/sample}',r'\texttt{sensor\_msgs/msg/Imu}; 200 / 100 Hz','Best effort / volatile'],
        [r'\texttt{/tf\_static} (absolute topic)',r'\texttt{tf2\_msgs/msg/TFMessage}; static','Reliable / transient local']], [73,69,38]),
        'Rates are requested baseline values; verify offers, depth and actual delivery.',runbook+'; n3\_topics.json; ROS Jazzy QoS [3]')
    setp(21,'3.5 Threads and backpressure',paragraphs(
        block('Acquisition / ROS',r'SDK callbacks deliver sensor frames. Wrapper work and DDS buffering precede the observer and recorder. Each queue can add age or discard input.'),
        block('Estimator / Atlas',r'\texttt{TrackStereo} runs in its caller. Local mapping consumes keyframes; loop closing handles place recognition and map changes. Atlas is shared map state [1].'))+
        r'\medskip Record queue capacity, depth, arrival/dequeue time and discard policy at each owned boundary; unavailable counters stay UNKNOWN.',
        'A recorder count mismatch and a tracking stall can originate in different queues.',runbook+'; upstream System.cc')
    setp(27,'3.11 Robot transform ownership',diagram('D27',r'''
\node[box] (map) at (0,0) {map};\node[box] (odom) at (6,0) {odom};\node[box] (base) at (13,0) {base\_link};
\draw[flow] (map)--node[above=5mm,lbl]{global correction / dynamic}(odom);
\draw[flow] (odom)--node[above=5mm,lbl]{local odometry / dynamic}(base);
\node[box] (body) at (0,-3) {body};\node[box] (imu) at (6,-3) {imu\_body};\node[box] (cam) at (13,-3) {camera};
\draw[flow] (base.south)--(13,-1.5)--(0,-1.5)--(body.north);
\draw[flow] (body)--node[above,lbl]{robot mount / static}(imu);
\draw[flow] (base)--node[right,lbl]{robot mount / static}(cam);
''','Dynamic edges need separate planned estimator and continuity owners.')+
        r'\medskip Robot description owns static mounts, including base\_link $\to$ body. The planned bridge owns dynamic edges; implementation is UNKNOWN. Optional world $\to$ map needs an explicit external-reference owner [4].',
        'One parent and one publisher per child; never relabel a jumping map pose as odom.', 'docs/ARCHITECTURE.md; REP-103/105')
    setp(28,'3.12 Camera transform ownership',diagram('D28',r'''
\node[box] (cam) at (7,0) {camera};
\node[box] (opt) at (0,-2) {camera\_optical};\node[box] (imu) at (5,-2) {imu\_camera};
\node[box] (left) at (10,-2) {left camera};\node[box] (right) at (15,-2) {right camera};
\foreach \n in {opt,imu,left,right}{\draw[flow] (cam)--(\n);}
\node[box] (lo) at (10,-4) {left optical};\node[box] (ro) at (15,-4) {right optical};
\draw[flow] (left)--(lo);\draw[flow] (right)--(ro);
''','Wrapper-owned sensor geometry is static; frame names here are conceptual.')+
        r'\medskip Wrapper /camera/camera publishes sensor edges on /tf\_static when tf\_publish\_rate=0. Inspect actual parents and frame IDs; do not add this conceptual tree as a second publisher.',
        'The robot description owns the camera mount; the wrapper owns internal sensor geometry.',runbook+'; n3\_baseline.yaml')
    setp(31,'3.15 Timestamp fields and domains',diagram('D31',r'''
\node[box,text width=45mm] (dev) at (0,0) {Device domain\\$t_{dev}$: frame stamp\\capture event UNKNOWN};
\node[box,text width=49mm] (ros) at (6.5,0) {ROS header domain\\$t_{hdr}$: wrapper stamp\\bag preserves this field};
\node[box,text width=48mm] (host) at (13,0) {Host steady domain\\$t_{drv},t_{pub},t_{rx}$\\instrumented events};
\draw[flow] (dev)--node[above=18mm,lbl]{SDK / wrapper mapping}(ros);
\draw[dashed,navy] (ros)--node[above=18mm,lbl]{not an identity}(host);
\node[box,text width=160mm] at (6.5,-3) {Processing start $t_s$, end $t_e$, output $t_o$: same host steady clock.\\Bag storage $t_{bag}$, Coordinated Universal Time (UTC) logs and /clock: separate semantics.};
''','Header epoch, receipt and output are different events even if units match.')+
        r'\medskip Capture $t_c$ is a physical event; exposure convention and device relation are UNKNOWN. Preserve raw stamps and mapping version before defining source age.',
        'Global-time enablement is configuration evidence, not measured synchronization.',runbook+'; librealsense v2.58.4 global timestamp reader')
    setp(32,'3.16 Where timestamps are stamped',table(['Field / event','Stamp owner','Interpretation'],[
        [r'$t_{dev}$ / sensor frame','Device + SDK metadata','Hardware-relative or mapped domain; inspect each frame'],
        [r'$t_{hdr}$ / message header','ROS wrapper','Producer epoch; not publish time'],
        [r'$t_{rx},t_s,t_e,t_o$','Observer / adapter instrumentation','Local steady-clock receipt, start, end, emission'],
        [r'$t_{bag}$ / storage record','rosbag2 / storage backend','Recorder time; never substitute for source header']], [43,55,82]),
        'A trajectory stamp is the estimated pose epoch, not when its file was written.',runbook+'; n3\_metrics.py')
    setp(34,'3.18 Worked latency decomposition',diagram('D34',r'''
\draw[flow] (0,0)--(16,0);
\foreach \x/\t in {1/$t_{rx}$,5/$t_s$,10/$t_e$,15/$t_o$}{\draw[navy] (\x,-.2)--(\x,.2);\node[above] at (\x,.3){\t};}
\draw[<->,teal,thick] (1,-.8)--node[below]{queue $Q$}(5,-.8);
\draw[<->,teal,thick] (5,-.8)--node[below]{compute $C$}(10,-.8);
\draw[<->,teal,thick] (10,-.8)--node[below]{emit $E$}(15,-.8);
''','All three components use the same host steady clock.')+
        r'\medskip $L_{rx\to o}=(t_s-t_{rx})+(t_e-t_s)+(t_o-t_e)=Q+C+E$.\par\medskip Capture age requires $\widehat t_c=g(t_{dev})$ in this domain. If mapping error is bounded by $u$, true age lies in $[t_o-\widehat t_c-u,\ t_o-\widehat t_c+u]$.',
        'Fast compute does not imply fresh output when queue wait dominates.',runbook)
    setp(44,'3.28 Settings audit before tuning',table(['Pinned parser group','Meaning / check','Failure implication'],[
        ['Camera1 / Camera2; Stereo','Projection, distortion, b or T\_c1\_c2; selected rectification path','Wrong disparity geometry; scale / epipolar error'],
        ['IMU.T\_b\_c1',r'Camera $\to$ estimator IMU; numeric basis-vector / inverse test','Axis/sign error; gravity or bias inconsistency'],
        ['IMU.Frequency; four noise fields','Continuous-time densities / walks; discretize once','False confidence; unstable initialization'],
        ['ORBextractor fields','Feature count, pyramid, FAST thresholds','Tune only after input, timing and calibration']], [48,85,47]),
        'The historical mono candidate with unresolved noise is not stereo-ready.',offline)
    setp(46,'3.30 Planned health envelope',table(['Field family','Receiver purpose','Current design state'],[
        ['Version, session, sequence','Reject unknown format, duplicates and old boot','PLANNED; no wire message'],
        ['Source epoch, domain, age bound','Distinguish new heartbeat from new estimate','Clock relationship UNKNOWN'],
        ['Frames, reset/map ID, state','Reject wrong reference, map jump or initialization','PLANNED semantics'],
        ['Pose / velocity / uncertainty','Use only valid finite supported quantities','Covariance availability UNKNOWN']], [59,77,44]),
        'Publication rate, link transport and stale threshold remain UNKNOWN.', 'docs/ARCHITECTURE.md; docs/DECISIONS.md')
    setp(48,'3.32 Planned Pi-to-STM32 boundary',diagram('D48',r'''
\node[box,text width=47mm] (pi) at (0,0) {Pi health envelope\\session / sequence\\pose epoch / age bound\\frames / reset / validity};
\node[box,text width=47mm] (rx) at (6.5,0) {STM32 receiver\\schema / finite checks\\age $\leq A_{max}$\\session / frame checks};
\node[box,text width=47mm] (nav) at (13,0) {Optional autonomy\\fresh: eligible input\\stale / absent / invalid:\\withdraw perception input};
\draw[flow] (pi)--node[above=18mm,lbl]{rate $r_h$ UNKNOWN}(rx);
\draw[flow] (rx)--(nav);
\node[box,text width=160mm,fill=teal!8] at (6.5,-3.2) {STM32 body IMU $\to$ local balance / LQR / VMC / FSM $\to$ motor limits\\continues under local authority; physical fallback behavior needs safety review};
''','The health path provides optional information; local control keeps authority.')+
        r'\medskip $A_{max}$, transport and $r_h$ require approval. Receiver age must include source age and link residence with a defined clock relation; receipt-only timeout is insufficient.',
        'These are planned semantics; no message, firmware or stability test is implemented.', 'docs/ARCHITECTURE.md; docs/DECISIONS.md')
    setp(50,'4.1 Gate dependencies and status',diagram('D50',r'''
\foreach \x/\n/\t in {0/a/N0,4/b/N1,8/c/N2,12/d/N3}{\node[box,text width=23mm] (\n) at (\x,0) {\t\\OPEN};}
\draw[flow] (a)--(b);\draw[flow] (b)--(c);\draw[flow] (c)--(d);
\node[box,text width=28mm] (e) at (0,-2.6) {N4A EuRoC\\PLANNED};
\node[box,text width=39mm] (f) at (6,-2.6) {N4B offline stereo\\PLANNED};
\node[box,text width=39mm] (g) at (12,-2.6) {N4C live stereo\\PLANNED};
\draw[flow] (a)--(e);\draw[flow] (d.south)--node[above,lbl]{stereo + calibration}(f.north);
\draw[flow] (f)--(g);
\node at (6,-4.5) {Qualified N4 trials $\to$ N5 metrics $\to$ N6 health $\to$ N7 boundary};
''','N4A is independent of camera gates; N4B requires N3 plus stereo/calibration.')+
        r'\medskip N4C also renews physical input gates. N5--N7 are PLANNED. No Pi gate has passed; all execution still requires its explicit authorization.',
        'An independent EuRoC build test cannot promote the D435i transport gates.', 'BRIEF.md; Phase A runbook; offline preparation')
    # Gate operations and criteria. Evidence names for future gates are proposals, not files claimed present.
    setp(51,'4.2 N0: platform preflight',
        paragraphs(block('Purpose / entry',r'Fresh camera-free restart. Establish actual Pi hardware, 64-bit Arm architecture (ARM64), operating system (OS), supply, cooling and time.'),block('Evidence produced',r'JavaScript Object Notation (JSON) inventory, OS/kernel/package versions, power/cooling notes, UTC synchronization and source/binary hashes. Preserve historical sticky flags.'))+
        commands(['python3 platform\_inspect.py > NEW-inventory.json','uname -a; timedatectl status','vcgencmd get\_throttled; vcgencmd measure\_temp']),
        'Inventory is read-only; resolve unstable supply before any build or capture.',runbook)
    add(51,'4.2 N0: acceptance and diagnosis',table(['PASS requirement','Measurement / clock','Evidence'],[
        ['ARM64; Ubuntu 24.04; Jazzy','OS/package inventory; observation UTC','NEW-inventory.json'],
        ['UTC synchronized; flags 0x0','Time service + raw power flags; current boot','Inventory + time/power log'],
        [r'Temperature $<75\,^{\circ}$C; available memory $\geq512$ MiB','Temperature + MemAvailable; sampled host time','Inventory + health samples']], [66,75,39])+
        r'\medskip FAIL: sticky undervoltage points to supply/cable; heat points to cooling; clock unsynchronized blocks cross-log correlation. Idle PASS does not prove loaded health.',
        'These platform prerequisites are carried into N1 and checked again under load.',runbook)
    setp(52,'4.3 N1: own-branch USB and access',
        block('Entry / purpose',r'N0 eligible, CAMERA AVAILABLE, documented direct SuperSpeed cable. Verify the camera branch before SDK streaming.')+
        commands(['python3 n1\_precheck.py --camera-available','\quad --direct-cable-confirmed --output "\$WBR\_RUN/n1"'])+
        r'\medskip Produces sealed result.json, USB topology / sysfs identity, normal-user access checks, SDK enumeration and kernel context. Preserve SDK serial, application-specific integrated circuit (ASIC) serial, firmware-update ID and USB descriptor serial as separate fields.',
        'At 480M stop before SDK enumeration or N2; a 5000M root hub is insufficient.',runbook)
    add(52,'4.3 N1: acceptance and diagnosis',table(['PASS requirement','Measurement / clock','Evidence'],[
        [r'Own direct branch $\geq$5000M','lsusb -t + camera sysfs speed; before/after UTC','n1 USB / sysfs snapshots'],
        ['Video; Human Interface Device (HID); Industrial Input/Output (IIO)','Access + owner inspection; no broad permissions','n1 access checks'],
        ['Identity; eligible sealed receipt','Host/boot match; age $\leq$2 h, no reboot','n1/result.json + raw logs']], [65,77,38])+
        r'\medskip FAIL: 480M $\to$ cable/port/hubs; video works but motion denied $\to$ HID/IIO controls; serial mismatch $\to$ identity/descriptor audit, not firmware update.',
        'Re-run N1 after storage qualification or a topology change.',runbook)
    setp(53,'4.4 N2: staged native acquisition',
        r'Entry: eligible sealed N1. Exact IR1 640$\times$480 Y8/15, gyro/200, accel/100; no combined IMU or fallback.'+
        commands(['python3 phase\_gate.py n2 --camera-available --seconds 20','\quad --n1-result "\$WBR\_RUN/n1/result.json"','\quad --output "\$WBR\_RUN/smoke"'])+
        r'\medskip Repeat with 105 s and previous smoke receipt, then 300 s and previous reproduction receipt. Each stage saves CSV, SDK log, kernel journal, one-Hz health, topology, shutdown and three separately sampled Portable Graymap (PGM) images.',
        'The mandatory 300 s raw soak is separate from the 12 s image-content sampler.',runbook)
    setp(54,'4.5 N2: delivery criteria',table(['PASS threshold','Measurement / clock','Evidence'],[
        ['IR 14.25--15.75 Hz; gap $\leq$0.20 s','N/requested duration; interior rate; SDK stamp and arrival gaps','frames.csv; analysis JSON'],
        ['Gyro 190--210 Hz; gap $\leq$0.05 s','Whole-request / interior windows; per-stream stamps + arrivals','Motion CSV; analysis JSON'],
        ['Accel 95--105 Hz; gap $\leq$0.05 s','Same method; do not compare device and host epochs','Motion CSV; analysis JSON'],
        ['Positive stamps/frame steps; no missing IR frames','Adjacent differences in each stream; internal/trailing gaps strict','CSV + startup-offset review']], [61,79,40]),
        'Burst-only delivery can pass first/last rate while failing whole-request rate.',runbook)
    add(54,'4.5 N2: content, health and acceptance',table(['PASS requirement','Measurement / clock','Evidence'],[
        ['20 / 105 / 300 s stages complete','Requested duration + clean finalized shutdown; host interval','Three capture-result.json files'],
        ['Coherent Y8; finite plausible motion','Dimensions, byte count, stats / hashes; sample epochs','PGMs; content review'],
        ['Clean USB/kernel; stable platform','Continuous journal + one-Hz health; UTC/host times','SDK/kernel/health logs'],
        ['Actual human review; warning retained','Explain startup offsets; retain calibration fallback verbatim','review.json; accepted result']], [60,73,47]),
        r'FAIL: torn images $\to$ USB/raw; motion-only failure $\to$ HID; late shutdown $\to$ controls.',runbook)
    add(54,'4.5 N2: seal reviewed evidence',commands([
        'python3 phase\_gate.py accept-n2 --camera-available',
        '\quad --n1-result "\$WBR\_RUN/n1/result.json"',
        '\quad --smoke "\$WBR\_RUN/smoke/capture-result.json"',
        '\quad --reproduction "\$WBR\_RUN/reproduction/capture-result.json"',
        '\quad --soak "\$WBR\_RUN/soak/capture-result.json"',
        '\quad --review "\$WBR\_RUN/review.json" --output "\$WBR\_RUN/n2-accepted"'])+
        r'\medskip Review.json must reflect actual log/image inspection and calibration provenance. Never prefill acceptance booleans. Sealed evidence is recomputed, not merely trusted.',
        'N2 transport acceptance still leaves final VIO calibration blocked.',runbook)
    setp(55,'4.6 N3: one wrapper, bounded record',r'Entry: reviewed N2, qualified storage, fresh N1 after storage probe, reviewed installed wrapper. Tools run inside the checksummed Pi bundle.'+
        commands(['python3 wrapper\_inspect.py --output NEW-wrapper.json',
        'python3 n3\_record.py --camera-available',
        '\quad --n1-result N1/result.json --n2-result N2/result.json',
        '\quad --storage-result STORAGE/result.json',
        '\quad --bag /mnt/wbr-nvme/NEW\_BAG --seconds 20 --output NEW-record'])+
        r'\medskip The runner uses n3\_baseline.yaml and ten explicit topics. A full 60 s live window precedes recording; observer metrics continue during recorder load.',
        'Parameter readback and observed graph must match; candidate version is not installation evidence.',runbook)
    setp(56,'4.7 N3: stop camera and replay',commands([
        'python3 n3\_bag.py replay /mnt/wbr-nvme/NEW\_BAG',
        '\quad --record-result NEW-record/result.json',
        '\quad --live-domain 42 --replay-domain 43',
        '\quad --output-dir NEW-replay'])+
        paragraphs(block('Artifacts',r'Finalized bag metadata, topic counts, hashes, live metrics, parameter readback, observer/player logs and complete decoded replay comparisons.'),block('Isolation',r'Camera stopped; localhost-only domains. Observer ready/stop handshakes cover complete playback and queue drain. Guard live domain throughout.')),
        'Playable metadata alone does not establish complete, faithful replay.',runbook)
    add(56,'4.7 N3: PASS/FAIL matrix',table(['PASS requirement','Measurement / clock','Evidence'],[
        ['60 s live + load delivery','IR/gyro/accel N2 bands; ROS header and host steady gaps incl. boundaries','Live / record observer JSON'],
        ['Frames, profile, ten topics / types','Readback + image/info agreement + static TF; header stamps','Parameters; graph; context'],
        ['Clean finalized bag / exact replay','Stored vs complete observed counts, order, header and decoded field hashes','metadata.yaml; replay result'],
        ['No contamination / process fault','Live-domain guard + player/observer shutdown; host event time','Full camera/player logs']], [62,80,38]),
        r'FAIL: topic silence $\to$ driver/graph/QoS; missing context $\to$ durability; under-load gaps $\to$ storage.',runbook)
    add(56,'4.7 Storage prerequisite: no mount fallback',table(['Required threshold','Measurement / clock','Evidence'],[
        ['Actual external device / UUID','findmnt, lsblk, bridge + physical identity; inspection UTC','storage identity receipt'],
        [r'$\geq$1 GiB and $\geq$60 s; both rates $\geq$9.216 MB/s','Overall and worst 64 MiB fsync batch; host interval','storage/result.json'],
        ['Matching SHA-256 readback; cleanup','Digest / cleanup result; 10 GiB headroom retained','Storage raw log + receipt']], [64,80,36])+
        r'\medskip The 8 GiB default may finish before 60 s on a fast device: incomplete duration, not low throughput. A larger write budget needs review; the IR1 margin does not qualify stereo bags.',
        r'FAIL: directory resolves to microSD $\to$ mount; slow batches $\to$ storage before ROS tuning.',runbook)
    setp(58,'4.9 N4A: camera-independent EuRoC baseline',r'Entry: N0 only in the camera gate graph; separately authorized ORB run, pinned isolated build, dataset/settings hashes. No N1--N3 dependency.'+
        commands(['cmake --build "\$WBR\_ORB\_WORK/build"',
        '\quad --target stereo\_inertial\_euroc --parallel 2',
        './Examples/Stereo-Inertial/stereo\_inertial\_euroc',
        '\quad Vocabulary/ORBvoc.txt SETTINGS.yaml SEQUENCE TIMES.txt RUN\_ID'])+
        r'\medskip Build dependencies in the documented stages first. Freeze stereo settings and dataset reference coverage. Retain compile/run logs, initialization events, f\_RUN\_ID.txt and kf\_RUN\_ID.txt.',
        'The repo mono build example must be adapted explicitly to the pinned stereo target.',offline)
    add(58,'4.9 N4A: estimator acceptance contract',table(['Required / open threshold','Measurement / clock','Proposed evidence'],[
        ['Finite ordered trajectories; coverage','Export epochs in dataset time; coordinate/format audit','Trajectory files + audit'],
        ['Repeat initialization / tracking','All attempts incl. failure; first eligible dataset epoch + host events','Run/state timelines'],
        ['Accuracy / continuity budgets UNKNOWN','Reference association, rigid alignment, ATE/RPE; dataset epochs','evo outputs + budget review']], [65,77,38])+
        r'\medskip FAIL: load/link error $\to$ build; empty images $\to$ reader paths; no inertial initialization $\to$ settings/time/motion. No accepted numeric budget means no performance PASS.',
        'A EuRoC result validates the algorithm path; it says nothing about this camera transport.',offline)
    setp(59,'4.10 N4B: offline D435i stereo',paragraphs(block('Entry / purpose',r'N3 plus reviewed IR2 stereo extension and accepted calibration. N4A informs diagnosis but is not a camera-input dependency.'),block('Artifacts',r'Immutable bag, lossless derived left/right images and raw motion, manifest, association/rejection metrics, settings and repeat trajectories.'))+
        commands(['ros2 bag info /path/to/FINALIZED\_STEREO\_BAG',
        './Examples/Stereo-Inertial/stereo\_inertial\_euroc',
        '\quad Vocabulary/ORBvoc.txt QUALIFIED.yaml DERIVED TIMES.txt RUN\_ID'])+
        r'\medskip Stereo conversion is PLANNED; no converter command exists. Review adapter format/API before implementation, then test exact time and lossless count reconciliation.',
        'The historical IR1-only mono candidate cannot supply the required stereo inputs.',offline)
    add(59,'4.10 N4B: input and run criteria',table(['Required / open threshold','Measurement / clock','Proposed evidence'],[
        ['Lossless stereo + valid pairing','Counts/pixels, epipolar residuals, left/right stamp difference; source domain','Association / image audit'],
        ['Calibrated geometry, noise and offset','Holdout residuals; camera/IMU units and common time relation','Calibration report + hashes'],
        ['Repeatable finite tracking; budgets UNKNOWN','All trials, epochs, initialization/loss; no GT means accuracy UNKNOWN','Run logs + trajectories']], [63,79,38])+
        r'\medskip FAIL: vertical mismatch $\to$ rectification; missing brackets $\to$ motion coverage; bias instability $\to$ clocks/calibration before feature tuning. Residual limits are not yet approved.',
        'Default/CAD values and zero placeholder noise do not qualify final VIO.',offline)
    setp(60,'4.11 N4C: live stereo scheduling',paragraphs(block('Entry / purpose',r'Accepted offline stereo, renewed N1--N3 with stereo load and unchanged calibration/settings. Isolate the additional live scheduling cost.'),block('Tools / artifacts',r'Planned bounded live driver invokes TrackStereo; no approved launch command exists. Capture input/output/state events, pairing decisions, queue depth and shutdown logs.'))+
        commands(['ros2 topic info --verbose DISCOVERED\_IR2\_TOPIC',
        'ros2 param dump /camera/camera',
        'vcgencmd get\_throttled'])+
        r'\medskip These diagnosis commands do not implement the live stereo bridge. Select ROS versus non-ROS input path through matched-data evidence and architecture review.',
        'Offline success cannot bound live source age or queue growth.',offline+'; '+runbook)
    add(60,'4.11 N4C: live PASS/FAIL criteria',table(['Required / open threshold','Measurement / clock','Proposed evidence'],[
        ['Valid paired input + IMU coverage','Source epochs; renewed stereo transport metrics','Input / pairing timeline'],
        ['Initialization / continuity budgets UNKNOWN','Attempt count; loss/reset state; source epochs + host event times','State timeline / trajectories'],
        ['Latency / queue bounds UNKNOWN','Queue, compute, receipt/output on host steady; mapped capture with uncertainty','Latency / queue / health log']], [65,77,38])+
        r'\medskip FAIL: offline works, live lags $\to$ wrapper/DDS/executor/queue; thermal stalls $\to$ N0 under load; loss in both $\to$ input/calibration first. Missing counters stay UNKNOWN.',
        'Approve bounds before a live performance verdict; do not tune around unmeasured age.',offline)
    setp(61,'4.12 N5: reproducible measurement',r'Entry: qualified N4 trials, frozen hypotheses, trial count, reference and clock relations. Retain failures as part of the experiment denominator.'+
        commands(['evo\_ape tum REFERENCE.tum ESTIMATE.tum --align',
        'evo\_rpe tum REFERENCE.tum ESTIMATE.tum --help'])+
        paragraphs(block('Outputs',r'Original exports, conversion audit, evo version/argv/results, latency samples with eligibility, initialization/loss events and resource time series.'),block('Tools still planned',r'Event instrumentation and queue counters need reviewed implementation. No first-party N5 acceptance validator exists. Approve metric bounds before the campaign.')),
        'A metric file is a measurement artifact, not automatic performance acceptance.',offline+'; evo maintainer Metrics [8]')
    add(61,'4.12 N5: measurement criteria',table(['Required / open threshold','Measurement / clock','Proposed evidence'],[
        ['ATE/RPE only with valid reference','Associated source epochs; rigid alignment; overlap and exclusions','evo raw output / audit'],
        ['P50/P95/P99 + initialization/loss','Named interval, estimator and sample count; host steady / source epochs','Raw events + trial summary'],
        ['Resources, losses, queue depth','One-Hz health + event join; sequence/count reconciliation; unknown counters marked','Health / counter time series']], [61,79,40])+
        r'\medskip All numeric performance budgets are UNKNOWN. FAIL: cross-domain subtraction $\to$ clocks; suspicious low ATE $\to$ alignment/association; averages hide stalls $\to$ raw timeline.',
        'Missing ground truth blocks accuracy claims; it does not force synthetic zero errors.',offline)
    setp(62,'4.13 N6: health semantics with fixtures',paragraphs(block('Entry / purpose',r'Reviewed message semantics after N5; rate, transport, age rule and clock relation approved. Use synthetic fixtures before hardware integration.'),block('Tools / evidence',r'PLANNED receiver harness; no runnable project validator exists. Deliver event fixtures, expected/actual transitions, rejection reasons and revision hashes.'))+
        table(['Fixture','Expected planned response'],[
        ['Old epoch + fresh heartbeat','STALE; heartbeat does not refresh pose'],
        ['New boot / reset / map ID','Re-establish session and frame'],
        ['NaN, wrong frame, duplicate sequence','INVALID / reject; optional input withdrawn']], [85,99]),
        'Synthetic health tests qualify semantics only; they do not prove robot fallback.', 'docs/ARCHITECTURE.md; docs/DECISIONS.md')
    add(62,'4.13 N6: planned acceptance table',table(['PASS contract / open threshold','Measurement / clock','Proposed evidence'],[
        ['Reject every declared invalid fixture','Compare expected/actual state + reason; synthetic event time','Fixture verdicts'],
        ['Age bound $\leq A_{max}$; value UNKNOWN','Source-age bound + receiver elapsed time; defined Pi/STM32 relation','Clock / wrap / delay fixtures'],
        ['Reset re-establishment explicit','Session/frame sequence; no silent recovery','Transition trace + review']], [64,77,39])+
        r'\medskip FAIL: old pose accepted $\to$ source-age semantics; wrap breaks timeout $\to$ receiver clock; old session accepted $\to$ reset protocol. Rate and timeout remain unselected.',
        'Implement only after API/message review; do not infer acceptance from a heartbeat.', 'docs/ARCHITECTURE.md')
    setp(63,'4.14 N7: staged controller boundary',paragraphs(block('Entry / purpose',r'N6 semantics accepted plus separate safety authorization. STM32 body IMU, control loops, watchdog and motor limits remain local.'),block('Tools / artifacts',r'PLANNED bench receiver / controlled fault injection; no approved motor-test command exists. Preserve STM32 and Pi traces, test setup, fallback policy and safety review.'))+
        table(['Stage','Evidence needed before progression'],[
        ['Receiver bench, no actuation','Link loss, stale/reset/invalid rejection'],
        ['Approved controlled integration','Local balance timing and watchdog independence'],
        ['Separately approved physical test','Safe setup; controller-owned fallback observations']], [67,117]),
        'Pi loss must not remove local balance authority; actual stability is unmeasured.', 'AGENTS.md; docs/ARCHITECTURE.md')
    add(63,'4.14 N7: planned acceptance table',table(['Required / open threshold','Measurement / clock','Proposed evidence'],[
        ['No perception authority over safety','Ownership / code review + controlled fault trace','Boundary review'],
        ['Local control retained on Pi loss','STM32 loop/watchdog/motor state; MCU clock','Controller trace + setup'],
        ['Fallback inside approved safety budget','Fault onset to local action; MCU domain; numeric bound UNKNOWN','Fault timeline + sign-off']], [62,77,41])+
        r'\medskip FAIL: balance depends on ROS heartbeat $\to$ ownership; stale reference retained $\to$ fallback semantics; link reset bypasses validation $\to$ session handling.',
        'No approved setup and bound means no physical integration PASS.', 'AGENTS.md; docs/ARCHITECTURE.md')
    setp(70,'5.2 ATE computation outline',
         r'Absolute Trajectory Error (ATE) compares associated poses after a declared alignment. $P_i$ is the estimate and $Q_i$ the reference; root mean square error (RMSE) summarizes translation [8].'+
         diagram('D70',r'\node[box,text width=165mm] {$E_i=Q_i^{-1}SP_i,\qquad e_i=\|\operatorname{trans}(E_i)\|,\qquad \mathrm{RMSE}=\sqrt{\frac{1}{N}\sum_i e_i^2}$};','Rigid alignment S removes reference-origin choice, not a stereo scale error.')+
         r'\medskip Associate epochs within a predeclared tolerance; retain unmatched samples. Convert both trajectories to the same pose direction and units before fitting $S$. Report valid overlap and failure trials.',
         'Without independent reference data, D435i absolute accuracy stays UNKNOWN.',offline+'; evo Metrics')
    add(70,'5.2 Symbolic ATE worked example',table(['Associated pair','Aligned translation residual','Squared contribution'],[
        [r'$Q_a,SP_a$',r'$(u,0,0)$',r'$u^2$'],
        [r'$Q_b,SP_b$',r'$(0,v,0)$',r'$v^2$'],
        [r'$Q_c,SP_c$',r'$(0,0,w)$',r'$w^2$']], [44,91,45])+
        r'\medskip $\mathrm{RMSE}=\sqrt{(u^2+v^2+w^2)/3}$. This is a symbolic teaching example, not measured data. Unmatched epochs are excluded from this sum but reported separately.',
        'A low error over short surviving overlap does not imply successful full-sequence tracking.', 'evo Metrics [8]', 'KNOWN method / SYMBOLIC example')
    setp(71,'5.3 RPE and pair policy',
         r'Relative Pose Error (RPE) compares estimated motion with reference motion over a declared interval [8].'+
         diagram('D71',r'\node[box,text width=165mm] {$E_{ij}=(Q_i^{-1}Q_j)^{-1}(P_i^{-1}P_j)$\\Translation and rotation are separate metrics.};','Relative deltas expose local drift rather than global alignment choice.')+
         table(['Pair policy','Question answered'],[
         ['Fixed time separation','How wrong is motion over that duration?'],
         ['Fixed distance separation','How does error grow per traveled distance?'],
         ['Consecutive vs all eligible pairs','Different weighting; report choice and pair count']], [83,101]),
         'Never compare RPE numbers with different delta units or pairing policies.', 'evo Metrics [8]')
    setp(72,'5.4 Trajectory conversion and evo',commands([
        'evo\_ape tum REFERENCE.tum ESTIMATE.tum --align',
        'evo\_rpe tum REFERENCE.tum ESTIMATE.tum',
        '\quad --pose\_relation angle\_deg --delta 1 --delta\_unit m'])+
        r'\medskip The 1 m delta is a command example, not a project acceptance threshold [8]. Check installed --help, version, association tolerance, valid coverage and reference quality.'+
        block('Conversion before comparison',r'Technical University of Munich (TUM) format uses seconds, xyz and quaternion qx qy qz qw. Preserve EuRoC originals; audit quaternion order, units, pose direction and frame. Metric stereo defaults to rigid alignment; scale fitting is a separate diagnostic.'),
        'Store exact argv and raw output; conversion errors can dominate the metric.',offline+'; evo Metrics/Formats')

    add(51,'4.2 N0: physical inventory record',paragraphs(
        block('Target versus observation',r'Target: Pi 5, 8 GB, Ubuntu, active cooling and qualified bulk storage. Record actual memory, board, supply label, cable and cooler; do not overwrite historical inventory.'),
        r'\coursefigure{P09}{\slideimg[.46\textheight]{\linewidth}{P09}{Fresh preflight inspection}}{Inspect the actual assembly before assigning platform readiness.}'),
        'A diagram of the target is not evidence of the assembled platform.',runbook)
    add(59,'4.10 N4B: immutable adapter provenance',paragraphs(
        block('Derived input contract',r'Preserve raw bags. Manifest links input, converter, settings and calibration hashes; record domains, offset sign, interpolation brackets and every rejected sample.'),
        r'\coursefigure{P10}{\slideimg[.46\textheight]{\linewidth}{P10}{Offline frozen-input analysis}}{Frozen inputs make estimator comparisons attributable.}'),
        'Test lossless pixels, exact nanoseconds, no extrapolation and count reconciliation.',offline)

    add(53,'4.4 N2: reproduction and mandatory soak',commands([
        'python3 phase\_gate.py n2 --camera-available --seconds 105',
        '\quad --n1-result "\$WBR\_RUN/n1/result.json"',
        '\quad --previous "\$WBR\_RUN/smoke/capture-result.json"',
        '\quad --output "\$WBR\_RUN/reproduction"',
        'python3 phase\_gate.py n2 --camera-available --seconds 300',
        '\quad --n1-result "\$WBR\_RUN/n1/result.json"',
        '\quad --previous "\$WBR\_RUN/reproduction/capture-result.json"',
        '\quad --output "\$WBR\_RUN/soak"']),
        'Inspect each zero-exit stage before starting the next; no automatic final acceptance.',runbook)
    add(54,'4.5 Worked window-rate and boundary check',
        r'Let a requested window have duration $T$, $N$ received frames, and first/last arrivals $a_1,a_N$ relative to its start.\par\medskip '+
        'Whole-window rate $N/T$ measures coverage; $(N-1)/(a_N-a_1)$ measures only the surviving span. Both are needed. '+
        r'Boundary silence is $B=\max(a_1,T-a_N)$; inspect adjacent arrival and source-stamp gaps separately.\par\medskip',
        'Burst delivery can have a nominal interior rate and long boundary silence.',runbook, 'KNOWN method / SYMBOLIC example')
    add(56,'4.7 Content checks beyond delivery rates',table(['Runbook proposal','Measurement / clock','Evidence / limit'],[
        [r'Stationary mean gyro norm $\leq$0.10 rad/s', 'Finite raw gyro vectors over declared stationary window; header epochs','Raw samples + axis review'],
        [r'Stationary mean accel norm 9.0--10.5 m/s$^2$', 'Finite raw accel; units/frame and stationary interval documented','Raw samples + operator notes'],
        ['Zero incomplete/corrupt notifications', 'Unfiltered SDK/kernel startup-to-stop log; UTC/run interval','Raw logs, not counters alone']], [63,77,40])+
        r'\medskip These are native bring-up engineering criteria, not manufacturer specifications. Audit the prepared validator separately: matching rates do not prove all manual content criteria.',
        'CameraInfo/TF and plausible stationary vectors do not prove calibrated camera--IMU timing.',native)

    add(44,'3.28 Numeric IMU settings contract',r'YAML (YAML Ain’t Markup Language) settings must follow the selected pinned parser. All four unit-specific noise quantities remain UNKNOWN.'+table(['Key family','Interpretation'],[
        [r'IMU.NoiseGyro / NoiseAcc', r'Continuous-time gyro / accel noise densities; code multiplies by $\sqrt{f}$'],
        [r'IMU.GyroWalk / AccWalk', r'Bias random-walk quantities; code divides by $\sqrt{f}$'],
        [r'IMU.Frequency / T\_b\_c1', r'Input-grid frequency $f$ / camera-to-IMU transform; not raw accel rate']], [73,111])+
        r'\medskip Camera.width/height/fps and Camera1/Camera2 keys must match actual inputs. Example EuRoC values describe that dataset; they are not D435i calibration.',
        'Do not discretize densities twice or replace unresolved noise with example values.',offline)
    # Remove low-information filler everywhere; meaningful caption references remain.
    text=re.sub(r'Figure~\\ref\{fig:([^}]+)\} explains the .*?\.\\par\\medskip',
                r'The mechanism in Figure~\\ref{fig:\1} identifies the boundary to inspect.\\par\\medskip',text)
    # Replace the remaining generic lead-ins with caption references so no stock filler is introduced.
    text=re.sub(r'The mechanism in Figure~\\ref\{fig:([^}]+)\} identifies the boundary to inspect\.\\par\\medskip','',text)
    chunks=re.split(r'(?=% PAGE \d+:)',text)
    result=[chunks[0]]
    for chunk in chunks[1:]:
        match=re.match(r'% PAGE (\d+):[^\n]*\n',chunk);p=int(match[1])
        if p in replacements:
            tail=''
            if r'\end{document}' in chunk:
                raise ValueError('Cannot replace reference/tail chunk')
            chunk=match[0]+replacements[p]+'\n'
        result.append(chunk)
        result.extend('\n'+s+'\n' for s in additions.get(p,[]))
    text=''.join(result)

    text=re.sub(r'\\medskip Figure~\\ref\{fig:([^}]+)\} illustrates .*?\.', '', text)
    parts = re.split(r'(?=\\begin\{frame\})', text)
    for i, part in enumerate(parts):
        ids = re.findall(r'\\coursefigure\{([^}]+)\}', part)
        for key in ids:
            if r'\ref{fig:'+key+'}' not in part:
                match = re.search(r'(\\item [^\n]*?)(?=\\item|\}\n|\}\\medskip)', part)
                if match:
                    part = part[:match.end()] + r' (Figure~\ref{fig:'+key+'})' + part[match.end():]
        parts[i] = part
    return ''.join(parts)
