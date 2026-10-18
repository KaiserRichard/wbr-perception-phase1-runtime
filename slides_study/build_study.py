#!/usr/bin/env python3
"""Document generator only. Never invokes lab commands or changes base inputs."""
from pathlib import Path
import json, re
ROOT=Path(__file__).resolve().parent
frames=[]; inventory=[]; steps=[]
current_part='lecture'
from lab_narrative import rewrite, VARIABLE_GROUPS, session_map, take_home
def e(s):
    mapping={'&':r'\&','%':r'\%','_':r'\_','#':r'\#','$':r'\$','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}','\\':r'\textbackslash{}'}
    out=''.join(mapping.get(c,c) for c in s)
    for a,b in {'ᵀ':r'$^{T}$','←':r'$\leftarrow$','□':r'$\square$','→':r'$\to$','↔':r'$\leftrightarrow$','≤':r'$\leq$','≥':r'$\geq$','×':r'$\times$','±':r'$\pm$','°':r'$^\circ$','²':r'$^2$','³':r'$^3$','µ':r'$\mu$','τ':r'$\tau$','σ':r'$\sigma$','√':r'$\sqrt{\vphantom{x}}$'}.items():out=out.replace(a,b)
    return out

def add(title, body, label='KNOWN method', note='', fragile=False):
    n=len(frames)+1
    frames.append(r'\begin{frame}'+('[fragile]' if fragile else '')+'{'+e(title)+'}\n'+r'\evidence{'+e(label)+'}\n'+body+'\n'+r'\note{'+e(note or 'Study synthesis from base/main-v4-91p.tex, updated against base/main.tex. No new physical evidence; every gate remains OPEN.')+'}\n'+r'\end{frame}'+'\n')
    inventory.append({'page':n,'title':title,'evidence':label,'part':current_part})

def teach(title, bullets, takeaway, label='KNOWN method', note='', math=None, diagram=None):
    body=r'\deckitems{'+''.join(r'\item '+e(x) for x in bullets)+'}\n'
    if math:body+=r'\par\medskip '+math+'\n'
    if diagram:body+=r'\par\medskip '+diagram+'\n'
    body+=r'\vfill\takeaway{'+e(takeaway)+'}'
    add(title,body,label,note)

def table(title, heads, rows, takeaway, label='KNOWN method', note='', widths=None):
    widths=widths or [180/len(heads)]*len(heads)
    body=r'\begin{tabular}{@{}'+''.join('L{'+str(w)+'mm}' for w in widths)+r'@{}}\toprule'+'\n'
    body+=' & '.join(r'\textbf{'+e(h)+'}' for h in heads)+r'\\\midrule'+'\n'
    body+='\n'.join(' & '.join(e(v) for v in row)+r'\\[6pt]' for row in rows)
    body+=r'\bottomrule\end{tabular}\vfill\takeaway{'+e(takeaway)+'}'
    add(title,body,label,note)
    if current_part != 'lecture':
        lab_order.append(('table',dict(title=title,heads=heads,rows=rows,takeaway=takeaway,label=label)))

def code(title, command, note='', label='SOURCE-SUPPORTED interface / execution OPEN', after='Run only in the named terminal; stop on a nonzero exit.'):
    assert max(map(len,command.splitlines()),default=0)<=78,(title,max(map(len,command.splitlines())))
    assert len(command.splitlines())<=14,(title,len(command.splitlines()))
    body='\\begin{lstlisting}\n'+command.rstrip()+'\n\\end{lstlisting}\n'+r'\vfill\takeaway{'+e(after)+'}'
    add(title,body,label,note,True)

def flow(key, labels, caption):
    w=39 if len(labels)==4 else 49
    dx=4.6 if len(labels)==4 else 6.0
    d=r'\coursefigure{'+key+r'}{\begin{tikzpicture}'
    for i,label in enumerate(labels):
        d+=r'\node[box,text width='+str(w)+'mm,minimum height=17mm] (a'+str(i)+') at ('+str(i*dx)+',0) {'+e(label)+'};'
        if i:d+=r'\draw[flow] (a'+str(i-1)+'.east)--(a'+str(i)+'.west);'
    return d+r'\end{tikzpicture}}{'+e(caption)+'}'

# PART A: same 91-page lecture progression, with Phase-8 corrections.
add('WBR perception: understand, record, explain',r'''\begin{columns}[c,onlytextwidth]
\begin{column}{.50\textwidth}\Large Stereo-inertial perception\par\medskip
\normalsize Pi 5 / D435i / ROS 2 Jazzy\par\medskip
STM32 retains balance and safety.\par\medskip
Two short lab sessions; analysis at home.\par\medskip
Study revision: 18 October 2026\end{column}
\begin{column}{.46\textwidth}\coursefigure{cover}{\slideimg[.49\textheight]{\linewidth}{P01}{Conceptual robot}}{Conceptual platform, not a wiring guide.}\end{column}\end{columns}
\vfill\takeaway{Explain each boundary and leave the lab with evidence, including failures.}''','KNOWN ownership / all gates OPEN','BRIEF.md; base/main.tex cover and current claims. P01 is inherited conceptual artwork with known silhouette/board defects; never use it for wiring.')
teach('How to study this deck',['Part A: ownership → sensing → runtime → calibration → gates → evaluation.','Part B: follow step IDs, named terminals, checks and failure branches.','Recap answers are on the following PDF page; print the session checklists from backup.'],'Read the evidence label before believing a number.')
table('What an evidence label means',['Label','Meaning'],[['KNOWN / SOURCE-SUPPORTED','Stable method / inspected source interface.'],['MEASURED / CALCULATED','Archived observation / arithmetic with stated inputs.'],['INFERRED / ASSUMED','Interpretation / proposed choice or review threshold.'],['UNKNOWN / OPEN','Missing evidence / qualification unfinished.']],'A layout PASS or script exit 0 cannot promote a hardware gate.',widths=[65,115])
teach('System ownership: why WBR needs two computers',['The Pi runs perception and optional navigation on Linux.','STM32H7 owns body estimation, balance and motor safety.','LQR = Linear Quadratic Regulator; VMC = Virtual Model Control.','The Nucleo-F446RE is a link/supervisor stand-in, not the WBR controller.'],'Pi loss must withdraw optional input while local control keeps authority.',note='Canonical AGENTS.md, docs/ARCHITECTURE.md, docs/DECISIONS.md ADR-001; WBR physical balance retention is untested.',diagram=flow('owners',['D435i → Pi perception','Reviewed optional state','STM32 local control'],'Ownership boundary; no physical safety verdict.'))
teach('Camera IMU and body IMU have different jobs',['D435i inertial measurement unit (IMU) lives in imu_camera.','It supports visual-inertial odometry (VIO): motion from images and inertial data.','The controller IMU lives in imu_body and supports local balance.','Different mounts, clocks and calibrations prohibit naive substitution.'],'An IMU is a sensor type, not a shared reference frame.',note='Architecture ADR-002; camera and body IMUs remain separate.')
teach('Ownership: worked stale-input example',['Illustrative: 20 ms inference is followed by 300 ms in a queue.','Even a newly transmitted heartbeat can accompany a 320 ms old result.','The receiver must assess source age, validity, frame and session.'],'Why WBR cares: fast arithmetic does not make a usable navigation input.','CALCULATED illustrative; no WBR age budget',math=r'\[A=20+300=320\;\mathrm{ms}\]')
teach('Ownership: common mistake and check yourself',['Mistake: reset the Linux process and assume its old pose is still valid.','A new process/session may have a new origin, map and clock relation.','Question: can the camera IMU replace the body IMU during Pi failure?'],'Explain the independent control path aloud before connecting anything.',note='Answer: no. The camera path depends on the failed Pi and has unrelated mount/clock/calibration. STM32 retains its own sensing and safety authority.')
teach('D435i inputs and the identity that matters',['New SDK serial 317422076650; firmware readback 5.17.3.10; BMI085.','Keep SDK, ASIC, firmware-update and USB descriptor serial fields separate.','Old SDK serial 243322073847 has no transferable gate receipts.'],'Why WBR cares: a replacement camera needs fresh acquisition evidence.','MEASURED archived identity / fresh readback OPEN',note='base/main.tex Phase-8 D435i sensor inputs; docs/PROJECT_STATE.md; canonical N1 runbook. ASIC/descriptor observed 327743061057; firmware-update ID must be freshly established.')
table('Two stream profiles: never merge their evidence',['Purpose','IR images','Raw motion'],[['N2 qualification','IR1 Y8 640×480, 15 Hz','Gyro 200; accel 100 Hz'],['N4 development / S / C','IR1 + IR2 Y8 640×480, 30 Hz','Gyro 200; accel 100 Hz'],['A Allan / I diagnostics','No images','Gyro 200; accel 100 Hz']],'N2 still needs 20 → 105 → 300 s, including the 300-second soak.','SOURCE-SUPPORTED profiles / qualification OPEN',widths=[57,76,47])
teach('USB and power: inspect the camera branch',['D435i goes directly to a blue USB 3 port with its own known cable.','The camera node must show ≥5000M; a 5000M root hub is insufficient.','The 8 GB Pi booted the old card, but historical under-voltage persisted.'],'Why WBR cares: missing motion or frames can originate below the estimator.','MEASURED historical / SOURCE-SUPPORTED requirement',note='base/main.tex current hardware and USB; docs/PROJECT_STATE.md. CN HARDWARE.md later owner inventory reports one official 27 W PSU; arrival is not WBR qualification.')
teach('Storage: calculate the payload before recording',['Each Y8 image has 640×480 bytes; two views arrive 30 times each second.','The payload alone is 18.432 MB/s before serialization and indexes.','Two 120 s representations can require over 4.4 GB, before derived files.'],'The 1.09 MB/s USB2 stick cannot record this stream.','CALCULATED payload / MEASURED USB-stick rate',math=r'\[2(640)(480)(30)=18{,}432{,}000\;\mathrm{B/s}\]')
teach('Hardware: common mistake and check yourself',['Mistake: a larger RAM board repairs a weak supply or slow card.','A 15 s RAM diagnostic had zero observed drops; long card writes were gapped.','Question: does a clean RAM capture qualify persistent storage?'],'Separate transport, temporary capture, durable copy and replay evidence.',note='Answer: no. Phase 8 reports 29.99 Hz IR, 33 ms maximum gap, gyro 200.2 and accel 101 Hz for the short RAM test. Card take had 0.3–2.9 s gaps after 22 s; writer blocking is INFERRED.')
teach('Stereo geometry: two views constrain depth',['Rectification makes corresponding scene points lie on a shared image row.','Disparity is left u minus right u; baseline is a positive distance.','Wrong pairing, camera order or focal length makes metric depth wrong.'],'Why WBR cares: stereo gives scale only with valid geometry.',math=r'\[d=u_L-u_R,\qquad Z=\frac{f_x b}{d}\]',diagram=flow('stereo',['Same scene point','Paired rectified pixels','Metric depth'],'Conceptual stereo reasoning, not a depth measurement.'))
teach('Stereo: worked depth and disparity',['Factory readback: fx = 386.9533 px; baseline = 0.04991255 m.','Their product is 19.31383 px·m; at 1 m the ideal disparity is 19.31 px.','At disparity 10 px, calculated depth is about 1.931 m.'],'The calculation uses readback geometry; it is not independent accuracy.','MEASURED readback / CALCULATED example',math=r'\[f_x b=19.31383\;\mathrm{px\,m},\quad Z(10\;\mathrm{px})=1.93138\;\mathrm{m}\]',note='docs/D435I_CALIBRATION_PLAN.md §1–2. Distances measured from left optical center, not housing front.')
teach('Stereo: small disparity makes distant depth fragile',['Differentiate Z = fb/d: a small pixel error has increasing depth effect.','At 2 m, d ≈ 9.657 px; illustrative 0.5 px error gives ≈0.104 m error.','Lighting, blur, target visibility and stereo skew affect matching.'],'Use static S intervals before diagnosing a geometric failure.','CALCULATED first-order illustrative error',math=r'\[|\delta Z|\approx\frac{Z^2}{f_xb}|\delta d|=\frac{4}{19.31383}(0.5)=0.104\;\mathrm{m}\]')
teach('Stereo: common mistake and check yourself',['Mistake: copy the SDK negative x translation into Stereo.b.','SDK IR1→IR2 has tx = −b; ORB baseline magnitude is +b.','Question: if left/right images are exchanged, what happens to disparity?'],'Test frame direction and signs before changing feature thresholds.',note='Answer: disparity changes sign for the same ordering convention, producing negative inferred Z if the model is not changed. Stereo.T_c1_c2 is right→left; Kalibr cam1.T_cn_cnm1 is left→right.')
teach('IMU model: what the two channels measure',['Gyro measures angular rate plus bias and noise, in rad/s.','Accelerometer measures specific force, including the gravity relation.','Bias, scale/misalignment, white noise and bias walk are different errors.'],'Why WBR cares: systematic IMU errors bend prediction between images.',math=r'\[\omega_m=\omega+b_g+n_g,\qquad a_m=R_{bw}(a_w-g_w)+b_a+n_a\]',note='Pedagogical ideal model; all symbols frame-defined here. Separate physical scale/misalignment diagnostics are needed; no full intrinsic calibration is claimed.')
teach('Visual-inertial prediction bridges image intervals',['At 30 Hz, image intervals are about 33.3 ms; gyro nominal dt is 5 ms.','Gyro-grid association uses original gyro and bracketed interpolated accel.','Visual residuals correct accumulated propagation errors.'],'Interpolation adds an aligned input grid, not a new sensor.',diagram=flow('vio',['IMU propagation','Image constraints','Corrected state'],'Timing and geometry must connect both sensor cues.'))
teach('IMU: worked bias and noise scaling',['Illustrative uncorrected gyro bias 0.01 rad/s accumulates 0.1 rad in 10 s.','That is about 5.73° before visual correction; it is not this unit’s bias.','Continuous gyro density 0.001 at 200 Hz gives discrete σ ≈ 0.01414 rad/s.'],'ORB scales continuous densities internally; never discretize twice.','CALCULATED illustrative / ASSUMED candidate noise',math=r'\[\delta\theta=b_gT=0.1\;\mathrm{rad},\quad \sigma_d=N\sqrt{f}=0.001\sqrt{200}\]')
teach('Allan deviation: choose the supported region',['Average stationary samples over τ and compare neighboring averages.','A −1/2 log slope supports white-noise density N at τ = 1 s.','A +1/2 slope supports walk K via its fitted value at τ = 3 s.'],'A flat bias-instability minimum is not the bias-walk coefficient.',note='docs/D435I_CALIBRATION_PLAN.md §5; calibration/allan/README.md. At least one decade, slope tolerance ±0.1, fit R²≥0.95 and cluster support are ASSUMED tool review criteria.',math=r'\[\sigma_A^2(\tau)=\tfrac12\,\operatorname{mean}(\bar x_{k+m}-\bar x_k)^2\]')
teach('Allan: common mistake and check yourself',['Mistake: use rounded vendor CSV or interpolated 200 Hz accel as raw data.','Preserve XYZ full precision; raw accel remains 100 Hz and gyro 200 Hz.','Question: can a clean 36 s pilot establish long-term random walk?'],'Use the pilot for acquisition; plan ≥4 h provisional, preferably 15–24 h.',note='Answer: no. Short data may support timing checks or limited white-noise evidence, but not a supported long-τ walk. Report K UNKNOWN when the rising fit lacks support. Warm up 30 minutes and keep temperature/stationarity documented.')
teach('Frames: axes and the pose origin',['Body convention: x forward, y left, z up. Optical: x right, y down, z forward.','A trajectory describes a named sensor origin in a named reference frame.','The camera-to-robot mount must be composed to obtain robot-body pose.'],'Why WBR cares: a good camera trajectory can still give the wrong body motion.',note='base/main-v4-91p.tex frame definitions and Phase-8 pose origin; actual WBR mount is UNKNOWN.')
teach('Transforms: write the direction as an equation',['T_ab maps coordinates from b into a: p_a = R_ab p_b + t_ab.','The inverse rotation is transpose; inverse translation is −Rᵀt.','Keep mathematical rotation direction separate from array storage order.'],'A name such as Tbc is useful only with its mapping equation.',math=r'\[T_{ab}^{-1}=\begin{bmatrix}R_{ab}^{T}&-R_{ab}^{T}t_{ab}\\0&1\end{bmatrix}\]')
teach('Transforms: worked rotated lever arm',['Illustrative camera origin is 0.1 m along the body x axis.','A 90° body yaw rotates that lever arm into the world y axis.','Copying camera position to base_link creates orientation-dependent error.'],'Rigid alignment cannot remove a changing lever-arm error.','CALCULATED illustrative',math=r'\[R_z(90^\circ)\begin{bmatrix}0.1\\0\\0\end{bmatrix}=\begin{bmatrix}0\\0.1\\0\end{bmatrix}\]')
teach('Frames: common mistake and check yourself',['Mistake: publish the same TF child from both wrapper and robot description.','Wrapper owns internal sensor geometry; robot description owns its mount.','Question: can a loop-corrected map pose be relabeled continuous odom?'],'Assign one parent and one publisher per child.',note='Answer: no. Loop correction may jump map pose. A continuity owner must explicitly maintain map→odom and continuous odom→base semantics; that bridge is not established by current WBR code.')
table('Timestamp chain: every kind has an owner',['Stamp','Owner / meaning'],[['Physical capture','Actual exposure/measurement event; convention UNKNOWN.'],['Device / SDK frame','Hardware, global or system domain; keep raw metadata.'],['Driver / ROS header','Wrapper assigns the message’s source epoch.'],['Publish / subscriber receipt','Different events; instrument on a stated host clock.']],'A shared unit such as nanoseconds does not imply a shared clock.',widths=[64,116])
table('Timestamp chain: processing, bag and output',['Stamp','Meaning'],[['Processing start / end','Local queue wait and compute intervals.'],['ROS bag storage time','Recorder event; never a substitute for header/capture.'],['Estimator pose epoch','Time the estimated state describes.'],['Emission / file write / MCU receipt','Availability and receiver events, not pose epochs.']],'Why WBR cares: measuring compute alone misses old input and queueing.',widths=[68,112])
teach('Clocks: worked same-clock latency',['Illustrative host-steady events: receive 10, start 30, end 42, emit 45 ms.','Queue = 20 ms; compute = 12 ms; emission overhead = 3 ms.','Receipt-to-output = 35 ms; physical capture age is still UNKNOWN.'],'Capture age also needs a measured mapping and uncertainty.','CALCULATED illustrative',math=r'\[L_{rx\to o}=(30-10)+(42-30)+(45-42)=35\;\mathrm{ms}\]')
teach('Clocks: common mistake and check yourself',['Mistake: subtract an MCU timer from a Pi monotonic timestamp.','Global-time enabled is configuration, not measured physical synchronization.','Question: all streams say SYSTEM_TIME; is equal-domain checking enough?'],'Calibration rejects SYSTEM_TIME even when every stream agrees.',note='Answer: no. Current calibration plan requires GLOBAL_TIME or HARDWARE_CLOCK plus supported metadata. SYSTEM_TIME may be host-arrival fallback. Equality is necessary but does not establish exposure timing or intersensor offset.')
teach('ROS 2: graph, typed topics and QoS',['Robot Operating System 2 (ROS 2) connects typed publishers and subscribers.','Data Distribution Service (DDS) provides transport and Quality of Service (QoS).','QoS does not validate frames or clocks; isolate wrapper faults from the algorithm.'],'Inspect graph, type, QoS and payload together.',diagram=flow('ros',['RealSense wrapper','DDS topic + QoS','Recorder / observer'],'Planned WBR integration; native SDK diagnostics are separate.'))
table('QoS: compatibility before counting frames',['Writer','Reader','Match?'],[['Best effort','Reliable','No'],['Reliable','Best effort','Yes'],['Volatile','Transient local','No'],['Reliable + transient local','Same policy for static TF','Yes']],'Use sensor-compatible QoS and durable static context.',widths=[65,80,35])
table('ROS topics: explicit sensor names',['Under /camera/camera/','Type / requested rate'],[['infra1/image_rect_raw; infra2/image_rect_raw','Image, 30 Hz each for stereo'],['infra1/camera_info; infra2/camera_info','CameraInfo, matching image profile'],['gyro/sample; accel/sample','Imu, raw 200 / 100 Hz'],['/tf_static (absolute)','TFMessage, reliable / transient local']],'N3 baseline selects IR1/15 and extra context; IR2 needs separate attestation.','SOURCE-SUPPORTED names / observed graph OPEN',widths=[102,78])
teach('ROS bags: a durable record is an experiment input',['Choose sqlite3 storage, explicit topics and a fresh take directory.','Stop with Ctrl-C; wait for metadata finalization before hashing or copying.','Retain parameter readback, wrapper log, QoS, metadata and power samples.'],'Record in the lab; keep interpretation reproducible at home.')
teach('ROS: worked queue and common mistake',['At 30 Hz, ten queued images can add about 333 ms before processing.','Mistake: ros2 topic hz looks nominal, so the bag must be complete.','Question: can a late-starting volatile reader recover prior static TF?'],'Compare counts, source stamps and context; do not infer them from rate.','CALCULATED illustrative / KNOWN ROS semantics',note='Answer: a volatile reader does not request retained historical delivery. Use reliable/transient-local for /tf_static, verify actual offer and record context. Nominal surviving-span rate can coexist with startup/tail losses.',math=r'\[10/30=0.333\;\mathrm{s}\]')
table('Calibration: four questions, four evidence types',['Quantity','Current state'],[['Image intrinsics + stereo geometry','MEASURED factory readback; optical validation OPEN.'],['Camera–IMU extrinsic','INFERRED nominal CAD; unit alignment OPEN.'],['Camera–IMU time offset','UNKNOWN; zero is an operating assumption.'],['IMU densities / walks','ASSUMED example values; unit Allan OPEN.']],'Why WBR cares: no single calibration report answers all four.',widths=[75,105])
teach('Intrinsics and stereo: validate the operating model',['Operating candidate is Rectified, 640×480 Y8, factory equal projections.','Do not refit physical lens distortion from already rectified pixels blindly.','S take checks rows, fixed-K reprojection, coverage and depth scale.'],'A fitted PinHole candidate is reviewed separately before deployment.','MEASURED readback / ASSUMED operating choice',note='docs/D435I_CALIBRATION_PLAN.md §1–2 and calibration/lab/README.md. Y8 ASIC rectification is INFERRED in the plan, not independently verified here. No operating YAML is overwritten.')
teach('Measured target: a 6×4 printable AprilGrid',['Use A3 45 mm tags, spacing ratio 0.3; A4 30 mm is the fallback.','Laser print at actual size; measure black edges, axis stretch and flatness.','Replace nominal tagSize in a session copy; keep tagRows = 4.'],'The plan’s stale six-row paragraph loses to the actual 6×4 target files.','SOURCE-SUPPORTED target / measured dimensions OPEN',note='calibration/aprilgrid/README.md and YAMLs. A3 working range 0.4–0.8 m; A4 0.3–0.5 m. Earlier 6×6/80 mm target is superseded.')
teach('Camera–IMU calibration: excite observable motion',['Kalibr uses a fixed measured grid and fixed factory camera chain.','Record C1–C3 with translation and rotation about all three axes.','Keep 5–10 s still at each end, emitter off, no impacts, blur or cable pull.'],'An attractive transform can coexist with bad residuals.',note='Calibration plan §3; lab allows 60–120 s, default 120 s in plan. Study lab uses 60 s C takes to fit RAM; separate S is 120 s only when reserve permits.')
teach('Kalibr transform: worked inversion',['Kalibr T_cam_imu maps IMU→camera; ORB T_b_c1 maps camera→IMU.','For R = I, inversion negates t; for general R use −Rᵀt.','ORB b refers to the D435i IMU, never STM32 imu_body.'],'Run basis-vector and inverse-composition checks before using a candidate.','SOURCE-SUPPORTED convention / CALCULATED example',math=r'\[T_{b c1}=T_{cam\,imu}^{-1},\quad t_{b c1}\approx[-5.52,\;5.10,\;11.74]^T\;\mathrm{mm}\]',note='The displayed camera→IMU translation is the nominal factory comparison, not a Kalibr result. A hypothetical Kalibr identity-R translation of [5.52,-5.10,-11.74] mm inverts to this nominal vector.')
teach('Kalibr time: worked sign and application boundary',['Convention: t_imu = t_cam + shift seconds.','Illustrative +2 ms maps camera time 1.000 s to IMU time 1.002 s.','Correct both image stamps once before coverage/association; keep raw audit.'],'ORB has no time-offset YAML key; runtime hook availability is OPEN.','SOURCE-SUPPORTED sign / CALCULATED illustrative',math=r'\[t_{cam,corrected}=t_{cam,raw}+0.002\;\mathrm{s}\]',note='docs/D435I_CALIBRATION_PLAN.md §4. Do not move IMU too, do not shift exported inputs twice, do not invent --cam-imu-shift-ms as an available flag.')
table('Calibration: proposed review thresholds',['Check','ASSUMED review threshold'],[['S image geometry','RMS ≤0.5 px; row median ≤0.3 px, p95 ≤1 px.'],['S coverage / depth','≥100 pairs, four quadrants; depth error ≤2%.'],['C repeated extrinsics','Spread ≤3 mm / 1°; CAD comparison ≤5 mm / 2°.'],['C time shifts','At least 3 takes; max−min ≤1 ms.']],'These are ASSUMED review thresholds, not manufacturer specs or gate PASS.','ASSUMED from current calibration plan',widths=[65,115])
teach('Calibration: common mistake and check yourself',['Mistake: use an optimizer’s tiny uncertainty as proof of physical accuracy.','Check residual patterns, detections, data timing and held-out repeatability.','Question: can online bias estimates fix unknown IMU scale/misalignment?'],'Keep calibration OPEN when the data cannot identify the parameter.',note='Answer: no. Online bias can address offsets; it does not establish scale/misalignment. Six static gravity poses diagnose accel, but do not determine gyro scale without known rotation or observable dynamic calibration.')
teach('ORB-SLAM3: work shared across threads',['SLAM = simultaneous localization and mapping; ORB = Oriented FAST and Rotated BRIEF.','Tracking handles each stereo input, IMU prediction and pose optimization.','Local mapping optimizes nearby keyframes and scene points.','Loop closing corrects revisits; Atlas may hold multiple maps.'],'Why WBR cares: a nonempty trajectory may hide resets or a map switch.',diagram=flow('orb',['Tracking on caller','Local mapping worker','Loop / Atlas work'],'Cooperating roles; bidirectional links show shared work.').replace(r'\draw[flow]',r'\draw[flow,<->]'))
teach('Tracking: account for every image interval',['Pair left/right by original identity and valid time relation.','Supply covered IMU samples; reject duplicate/backward time and gaps.','Log tracking state, lost frames, resets, map identity and initialization.'],'A viewer or successful launch is not a tracking verdict.')
teach('Initialization: stereo scale does not solve everything',['Stereo baseline supplies metric geometry under valid calibration.','Gravity, velocity and inertial biases still need sufficient excitation.','A still take can end cleanly with no initialized map.'],'Use smooth multi-axis motion; keep target calibration and VIO routes separate.')
teach('Association: worked interpolation',['Illustrative accel values: 1.0 at 10 ms and 3.0 at 20 ms.','At gyro time 15 ms, bracketed linear interpolation gives 2.0.','Outside the bracket or across an invalid gap, reject rather than extrapolate.'],'Preserve both raw accel and the derived gyro-grid value.','CALCULATED illustrative',math=r'\[a(15)=1+\frac{15-10}{20-10}(3-1)=2\]')
teach('ORB: common mistake and check yourself',['Mistake: increase feature count to hide dropped data or wrong geometry.','Debug power → USB → raw streams → clocks → ROS/bag → calibration → ORB.','Question: does offline replay establish live throughput or fresh output?'],'Use immutable inputs to isolate code changes, then test live scheduling.',note='Answer: no. Offline playback removes acquisition deadlines; mapping/loop workers still cause scheduling variation. Live age, queueing, drops, power and resource limits need their own evidence.')
table('Gate ladder: prerequisites remain OPEN',['Gate','Meaning / current evidence'],[['N0 / N1','Stable platform / current-unit access; OPEN.'],['N2 / N3','Exact raw soak / ROS record-replay; OPEN, active N3.'],['N4A','Known EuRoC dataset on Pi; strong historical evidence, OPEN.'],['N4B / N4C','D435i offline / live; no qualified camera trajectory.']],'N4A is a separate branch; it cannot accept the camera prerequisites.','SOURCE-SUPPORTED current project state',widths=[45,135])
table('Gate ladder: measurement and controller boundary',['Gate','Required evidence'],[['N5','Reproducible accuracy/continuity/latency/resources.'],['N6','Health semantics: stale, invalid, reset, unknown-age fixtures.'],['N7','Staged controller integration, independent local control.']],'WBR age budgets and physical safety bounds remain UNKNOWN.','OPEN / N5–N7 not started',widths=[40,140])
table('N2 thresholds stay exactly as specified',['Stream / condition','Requirement'],[['IR1 / gyro / accel','14.25–15.75 / 190–210 / 95–105 Hz.'],['Image / motion max gap','≤0.20 s / ≤0.05 s.'],['Order and image identity','Positive time/frame steps; no missing image frames.'],['Durations and health','20 → 105 → 300 s; clean power/kernel; actual review.']],'A 20 s stereo diagnostic is not the 20 s N2 stage.','SOURCE-SUPPORTED gate criteria',widths=[73,107])
teach('Dated evidence: what the sources actually establish',['Phase 8: card gaps, short RAM success, first-frame crash, interrupted repair.','Later lab source reports rebuild + 15 s still EuRoC-route replay exit 0.','That still replay has no map; hand-motion tracking and live remain unverified.'],'Keep the later report separate from the Phase-8 historical snapshot.','MEASURED source-reported diagnostics / all gates OPEN',note='base/main.tex Phase 8 controls conflicts with 91p. sources/LAB_DAY_2026-10-15-4b63.md opening box is later evidence from 14 Oct night, not independently rerun. CN 16 Oct supply availability is owner-reported, not WBR loaded qualification.')
teach('Gate example, common mistake and check yourself',['Worked case: 15 Hz interior rate with a long start delay misses window coverage.','Compare N/T and (N−1)/(last−first), plus start/tail silence.','Question: may a historical gate receipt survive a camera swap or reboot?'],'No tuning can repair evidence from the wrong device or boot.',note='Answer: no. N1 receipts are identity/host/boot bound, expire after two hours and need renewal after reboot/topology change. Old-unit N2/N3 does not transfer; keep whole-window and interior statistics.')
teach('Evaluation: the measured EuRoC MH01 baseline',['Historical 4 GB Pi completed three runs with IMU initialization, one map, no resets.','Absolute Trajectory Error (ATE), rigid-aligned: 0.0415 / 0.0368 / 0.0416 m.','These are root mean square errors (RMSE); mean RMSE is about 0.040 m.','Alignment fits rotation and translation only; scale is not fitted.'],'Why WBR cares: known input tests the build without camera adaptation.','MEASURED historical / N4A OPEN',note='base/main.tex Phase-8 baseline; experiments/2026-10-13-n4a-euroc-mh01/REPORT.md. Under-voltage invalidates a performance verdict; no D435i accuracy claim. Phase-8 excludes later numeric RPE and paper comparator.')
teach('ATE: worked RMS after a declared alignment',['Illustrative position residuals after SE(3) alignment are 0.03 and 0.04 m.','RMSE is sqrt((0.03² + 0.04²)/2) = 0.03536 m.','Report association tolerance, overlap, excluded frames and failed trials.'],'An alignment removes gauge freedom; it does not prove frame compatibility.','CALCULATED illustrative',math=r'\[\operatorname{ATE}_{RMSE}=\sqrt{\tfrac1n\sum_i\|p_i^{ref}-(Rp_i^{est}+t)\|^2}\]')
teach('RPE: relative pose error over a fixed interval',['Illustrative reference relative translation is 1.00 m; estimate is 1.02 m.','With equal rotation/direction, translation RPE is 0.02 m for that pair.','Declare delta seconds/metres/frames, endpoint policy and eligible pair count.'],'Numeric historical RPE remains UNVERIFIED under Phase-8 source restrictions.','CALCULATED illustrative / historical RPE UNVERIFIED',math=r'\[E_{ij}=(T_i^{-1}T_j)_{ref}^{-1}(T_i^{-1}T_j)_{est}\]',note='This teaches the metric without reinstating the excluded Phase-7 numeric claims. tools/trajectory_eval uses first eligible endpoint, no interpolation, overlapping pairs allowed.')
teach('Without ground truth: useful proxies have limits',['Record initialization time, resets/maps, loss fraction and longest lost interval.','Use a measured straight segment and return-to-start route with placement uncertainty.','Loop closure can conceal drift: report pre-loop and final closure separately.'],'Tape scale and closure are proxies, never D435i ATE.','ASSUMED review protocol / accuracy UNKNOWN',note='Calibration plan V1–V3: initialization ≤30 s, zero resets, one map, loss ≤1%, none >1 s, route closure/segment error ≤2%, cross-take closure spread ≤1 percentage point; all are ASSUMED.')
teach('Evaluation: common mistake and check yourself',['Mistake: fit Sim(3) scale and call the metric-scale stereo result accurate.','A plausible path or low aligned residual can hide scale, frame and timing errors.','Question: can 184 s dataset time / 282 s wall time give per-frame P99?'],'Report metric boundaries and evidence eligibility before comparing numbers.',note='Answer: no. Startup, vocabulary loading, tracking and shutdown are mixed in wall time. Historical walls 301/282/284 s, peak RSS 823/828/828 MiB and 87/178 live power-fault samples are summaries, not per-frame latency distributions.')
teach('Pi↔STM32 link: integrity before semantics',['Step 9b bench firmware checks RTT, CRC, sequence, session and silence.','It runs on F446RE as a link stand-in; NO_LINK is not OS HOLD or FAILSAFE.','Why WBR cares: packet integrity and fallback policy are distinct tests.'],'Never flash link-bench firmware and expect the CN/OS supervisor.',note='sources/STM32_LINK_STEP_2026-10-15.md; tools/link_bench/README.md; OS protocol/PROTOCOL.md and newer OS-wt-cn docs/CN_INTEGRATION.md.')
teach('UART: worked serialization floors',['WBR bench request/reply wire lengths imply ≈3.65 ms at 115200 baud.','CN E7 sends chunked images; 30 kB plus framing is 30,510 UART bytes.','At 115200 8N1, the E7 ingress line-time floor is ≈2.648 s.'],'UART image ingress and small supervisory messages have different budgets.','CALCULATED from source framing',math=r'\[T_{wire}=\frac{10\,N_{bytes}}{\mathrm{baud}}\quad\text{(8N1)}\]',note='Link step 9c expects request ≈2210 us and reply ≈1430 us. CN E7_DESIGN.md includes 17-byte overhead per 1024-byte chunk. These are floors, not measured RTT.')
table('CN/OS supervisor states and recovery',['State','Source-defined behavior'],[['INIT = 0','Readiness incomplete; fresh local and network evidence required.'],['FRESH = 1','All required liveness, age and validity checks healthy.'],['HOLD = 2','Results stale; can recover when all checks become healthy.'],['FAILSAFE = 3','Latched; board port requires reset, then new readiness.']],'Stop results with heartbeat alive to show HOLD before FAILSAFE.','SOURCE-SUPPORTED OS integration / hardware UNTESTED',note='Original OS protocol v1 names states but does not define transition thresholds. Newer OS-wt-cn docs/CN_INTEGRATION.md: heartbeat timeout 100 ms, result/network HOLD 200 ms, FAILSAFE 500 ms, 1 s healthy rearm API, 5 ms transit allowance; provisional defaults, not WBR safety budgets.',widths=[52,128])
teach('Link and supervision: common mistake and check yourself',['Mistake: stop the whole Pi bridge and expect HOLD→FAILSAFE.','Local heartbeat loss triggers FAILSAFE at 100 ms; network stale-data path is separate.','Question: do new packets automatically recover latched FAILSAFE?'],'Two fault injections test two mechanisms; record state and reason.',note='Answer: no. HOLD can return to FRESH; latched FAILSAFE needs explicit local rearm API after health, or board reset on this port. Neither link-bench NO_LINK nor CN/OS host tests prove WBR physical independence.')
# PART A END
from lecture_expansion import expand_lecture
expand_lecture(globals())
(ROOT/'qa/lecture-count.txt').write_text(str(len(frames))+' lecture pages\n')

# PART B: synchronized records render both slides and LAB_PLAN.md.
current_part='lab'
lab_intro=[]; lab_order=[]
def intro(title, bullets, takeaway, label='ASSUMED session schedule', note=''):
    teach(title,bullets,takeaway,label,note)
    lab_intro.append((title,bullets,takeaway))
    lab_order.append(('intro',dict(title=title,bullets=bullets,takeaway=takeaway,label=label)))

def step(sid,title,goal,setup,expected,criterion,fail,files,blocks,source,label='SOURCE-SUPPORTED procedure / execution OPEN',extra=None):
    item=dict(id=sid,title=title,goal=goal,setup=setup,expected=expected,criterion=criterion,fail=fail,files=files,blocks=blocks,source=source,label=label,extra=extra or [])
    item=rewrite(sid,item)
    steps.append(item)
    lab_order.append(('step',item))
    for suffix,fields in [('setup and observation',[('Goal / why','goal'),('Physical setup','setup'),('What you see','expected')]),('decision and recovery',[('PASS / FAIL','criterion'),('If FAIL','fail'),('Take these files home','files')])]:
        body=r'\par\medskip'.join(r'\textbf{'+caption+':} '+e(item[field]) for caption,field in fields)
        add(sid+' | '+(title if suffix=='setup and observation' else 'Decision, recovery and files'),body,label,source+' '+(' '.join(extra or [])))
    for i,(terminal,cmd) in enumerate(blocks,1):
        code(sid+f' | {terminal} ({i}/{len(blocks)})',cmd,source,label,after='Use the checks and failure branch on the preceding '+sid+' step card.')

intro('Lab operating contract',['Each supervised session is capped at 150 min; first failure consumes the retry buffer.','No build, install, card clone or persistent network change belongs in these sessions.','The 30 min warm-up and Allan take (≥4 h provisional; 15–24 h preferred) happen at home.'],'Stop at the time cap; leave skipped work OPEN.','ASSUMED time budget / SOURCE-SUPPORTED stop rules')
intro('Packing checklist',['8 GB Pi + qualified 128 GB card + 27 W supply; 4 GB Pi + own supply for CN.','D435i/cable, Ethernet, Mac/power, rigid measured AprilGrid, ruler/calipers, tape.','F446RE, Mac USB cable, 3 jumpers; optional analyzer; prepared firmware and tools.'],'Pack distinct link-bench and OS-supervisor firmware with hashes.','SOURCE-SUPPORTED packing / availability to verify')
intro('Stop rules: the earliest failed layer wins',['New live power fault, reboot, USB <5000M or data reversal: stop acquisition.','At a missing tool, unknown device identity or unverified command: stop that branch.','One corrected retry with a new ID; then defer to Session 2 or home preparation.'],'Do not tune SLAM, erase failed takes or relax thresholds to hide sensor faults.','SOURCE-SUPPORTED prerequisites / ASSUMED one-retry policy')
for variable_title, variable_rows in VARIABLE_GROUPS:
    table(variable_title,['Variable / binding','Plain meaning'],variable_rows,'Repeat bindings in each named terminal; use fresh actual session and take IDs.','SOURCE-SUPPORTED shell bindings / chosen deployment paths',widths=[60,120])
session_map(globals(),1)
table('Session 1 timeline: 150 min maximum',['Elapsed','Task / exit artifact'],[['0–15 / 15–30 min','S1.0–2: setup, power, storage/USB identity.'],['30–55 / 55–75 min','S1.3–4: N2 stages/review; N3 audit/record-replay.'],['75–110 / 110–125 min','S1.5–7: ROS S/C takes; native replicas only if ready.'],['125–140 / 140–150 min','S1.8–10: A pilot plan, link bench, verified handoff.']],'N3 unresolved at minute 75 means calibration qualification is deferred.','ASSUMED wall-time budget',widths=[63,117])
intro('Before lab: prepare, do not improvise',['Owner-authorized transfer/deployment, card setup and any builds happen beforehand.','Gate bundle, wrapper, ROS CLI, native recorder, Kalibr image and CN files must exist.','The strict card exception needs a reviewed sustained-write receipt; capacity is insufficient.'],'An unready prerequisite becomes a documented skipped step.','SOURCE-SUPPORTED runbook / readiness OPEN',note='Latest lab runbook requires owner phrase transfer before clone/deployment/write tests. The study builder performs none. No new permission is being requested for document generation.')
step('P0','Bind prepared paths and verify tools','Name the prepared runtime and data roots before either session.','Mac: canonical checkout. Pi: owner-provisioned bundle, sourced Jazzy; no camera process.','All required files exist; fresh evidence folder and source revision retained.','Observable: all test commands succeed; missing path = OPEN, not install now.','Stop; prepare the missing dependency at home. Never guess a replacement script.','Pi: ~/wbr-evidence/study-SESSION; Mac: wbr-data/study-SESSION.',[
('Mac / before lab', '''cd ~/Desktop/Research/wbr-perception-phase1-runtime
export WBR_HOST=richard@192.168.50.2
bash experiments/2026-10-15-demo-day/demo.sh --help
git rev-parse HEAD
git status --short'''),
('Pi / each shell', '''source /opt/ros/jazzy/setup.bash
export GATE="$HOME/wbr-runtime/study-gates"
export RUN="$HOME/wbr-evidence/study-S1-20261018"
export DATA="$HOME/wbr-takes/study-S1-20261018"
# Prepared, reviewed 128 GB data-directory exception.
mkdir -p "$RUN" "$DATA"
test -f "$GATE/phase_gate.py"
test -f "$GATE/n3_record.py"
test -f "$GATE/n3_bag.py"
export ROS_DOMAIN_ID=42 ROS_LOCALHOST_ONLY=1''')], 'Canonical AGENTS.md; archived PHASE_A_RUNBOOK.md; demo.sh --help; docs/D435I_CALIBRATION_PLAN.md storage exception.',extra=['study-gates is an explicitly chosen pre-lab deployment location, not a claimed existing runtime path. It must contain the full checksummed archived bundle; do not copy individual gate files. Session date/IDs are operator run IDs, not claims of capture on 18 Oct. Repeat environment bindings in each Pi terminal. DATA is a dedicated directory on the qualified 128 GB slot card; record actual findmnt/lsblk identity.'])
step('S1.0','Set up and make the evidence manifest','Strain relief and provenance let each result be attributed.','Pi/cables fixed; USB direct; power last; owner CAMERA AVAILABLE before camera access.','Notebook records supply, board, card, cable, cooler, target, room and run ID.','Observable: all manifest fields present or explicitly UNKNOWN; no active competing process.','Fix cabling first; record a missing field; do not borrow a hub or overwrite a run.','RUN/identity.txt, source-git.txt, source-dirty.txt; target measurements.',[
('Pi / control', '''uptime > "$RUN/identity.txt"
uname -a >> "$RUN/identity.txt"
findmnt -T "$DATA" >> "$RUN/identity.txt"
lsblk -o NAME,SIZE,MODEL,FSTYPE,UUID,MOUNTPOINTS \\
  >> "$RUN/identity.txt"
ps -eo pid,args > "$RUN/processes-before.txt"'''),
('Mac / canonical checkout', '''git rev-parse HEAD > /tmp/study-source-git.txt
git status --short > /tmp/study-source-dirty.txt
shasum -a 256 calibration/lab/config/*.yaml \\
  calibration/aprilgrid/*.yaml > /tmp/study-config.sha256''')], 'Latest lab runbook steps 0–3; calibration plan per-take manifest. Standard read-only Linux/macOS commands.',extra=['Copy /tmp/study-source-* and study-config.sha256 into the final session archive before /tmp cleanup. Record actual tool/binary/config hashes, wrapper version, SDK version, serials separately and notes on any dirty sources; a Git hash alone is insufficient.'])
step('S1.1','Power and storage preflight','Exclude the two measured bottlenecks before collecting sensor data.','27 W supply on 8 GB Pi, cooling, prepared qualified 128 GB data path.','Raw throttled, rail voltage, temperature and free bytes; reviewed write receipt.','SOURCE-SUPPORTED N0: flags 0x0, T <75°C, MemAvailable ≥512 MiB. ASSUMED full-profile write ≥27.6 MB/s.','Stop for live faults/reboot; correct supply/cable/cooling. No capture on an unqualified volume.','RUN/power-before.txt, capacity.txt; existing write receipt, with hash.',[
('Pi / control', '''vcgencmd get_throttled | tee "$RUN/power-before.txt"
vcgencmd pmic_read_adc EXT5V_V \\
  | tee -a "$RUN/power-before.txt"
vcgencmd measure_temp | tee -a "$RUN/power-before.txt"
free -h | tee "$RUN/capacity.txt"
df -B1 "$DATA" /dev/shm | tee -a "$RUN/capacity.txt"
timedatectl status > "$RUN/time-before.txt"''')], 'base/main.tex N0 table; calibration plan storage/power requirements; lab runbook telemetry.',extra=['ASSUMED card qualification: test file larger than the largest take and for at least its duration, sustained ≥27.6 MB/s; free ≥2× planned take plus OS reserve. Native script uses extra RAM/disk reserves. The archived external-storage gate runner does not accept the card policy by default; that is a real N3 tooling blocker. A clone/post-boot 4 GiB speed test is not equivalent qualification. Historical latched bits are retained; strict gates still require zero.'])
step('S1.2','USB, serial and fresh N1','Confirm the new camera branch before starting any stream.','Owner authorization, direct cable, stable N0, complete prepared GATE bundle.','USB camera ≥5000M; SDK serial 317422076650; firmware and separate identity fields saved.','SOURCE-SUPPORTED: n1_precheck exits 0 with strict eligible receipt; no access/kernel fault.','At 480M stop before SDK; fix cable→port→topology, retry once under a new output path.','RUN/usb.txt, sdk-enumeration.txt; RUN/n1/result.json and sealed logs.',[
('Pi / control', '''lsusb -t | tee "$RUN/usb.txt"
# Only after camera branch is confirmed >=5000M:
rs-enumerate-devices > "$RUN/sdk-enumeration.txt" 2>&1
cd "$GATE"
python3 n1_precheck.py --camera-available \\
  --direct-cable-confirmed --output "$RUN/n1"''')], 'Archived PHASE_A_RUNBOOK.md and n1_precheck.py; source lab enumeration procedure.',extra=['Read normal-user permissions; no broad chmod. N1 expires after two hours or reboot; renew after topology/storage changes. SDK enumeration warning absence does not prove physical IMU calibration.'])
step('S1.3','Exact N2 acquisition: inspect each stage','A sustained raw stream must be trusted before ROS or SLAM.','Eligible strict N1; IR1/15, gyro/200, accel/100; no other camera owner.','20 s, 105 s and mandatory 300 s raw results plus image samples and 1 Hz health.','SOURCE-SUPPORTED: IR 14.25–15.75, gyro 190–210, accel 95–105 Hz; gaps ≤0.20/0.05 s; positive steps, zero missing IR frames.','Stop at first failed layer: power→USB→permissions→profile→time; one new-ID retry then S2.','RUN/smoke, reproduction, soak: capture-result.json, CSV, raw logs and PGMs.',[
('Pi / gate bundle, stage 1', '''cd "$GATE"
python3 phase_gate.py n2 --camera-available --seconds 20 \\
  --n1-result "$RUN/n1/result.json" \\
  --output "$RUN/smoke"'''),
('Pi / only after prior stage review', '''python3 phase_gate.py n2 --camera-available --seconds 105 \\
  --n1-result "$RUN/n1/result.json" \\
  --previous "$RUN/smoke/capture-result.json" \\
  --output "$RUN/reproduction"
# Review that result before issuing the next command.
python3 phase_gate.py n2 --camera-available --seconds 300 \\
  --n1-result "$RUN/n1/result.json" \\
  --previous "$RUN/reproduction/capture-result.json" \\
  --output "$RUN/soak"''')], 'Archived phase_gate.py CLI and PHASE_A_RUNBOOK.md exact N2 stages.',extra=['These native gate samples are required historical-tooling outputs; the vendor CSV lacks domain tags and rounds motion. They cannot replace full-precision calibration takes. Native gate capture has no ROS publisher; a simultaneous ROS bag is unavailable. Preserve this explicit exception/gap instead of launching a second device owner.'])
step('S1.3R','Human N2 review and acceptance','Separate automatic capture from an actual gate decision.','All three strict stages complete; reviewer has opened images and unfiltered logs.','review.json contains actual UTC/reviewer/notes and reviewed booleans, not a prefilled approval.','Observable: clean coherent images, plausible finite IMU, explained startup offset, preserved warnings and eligible acceptance.','Leave OPEN if review is incomplete; do not prewrite true booleans or bypass diagnostic receipts.','RUN/review.json; RUN/n2-accepted/result.json.',[
('Pi / after actual review', '''python3 phase_gate.py accept-n2 --camera-available \\
  --n1-result "$RUN/n1/result.json" \\
  --smoke "$RUN/smoke/capture-result.json" \\
  --reproduction "$RUN/reproduction/capture-result.json" \\
  --soak "$RUN/soak/capture-result.json" \\
  --review "$RUN/review.json" --output "$RUN/n2-accepted"''')], 'phase_gate.py accept-n2; PHASE_A_RUNBOOK.md manual review schema.',extra=['Review schema strings: utc, reviewer, notes, power_supply, cooling, scene, calibration_provenance (verified parser field: utc, timezone-aware and ≤2 h old). Required true booleans: raw_logs_clean, images_coherent, startup_offsets_explained, imu_values_plausible, power_cooling_documented, calibration_warning_preserved. The exact UTC field is verified in the command audit; never invent a review receipt.'])
step('S1.4','Active N3: baseline record and replay','Prove graph, QoS, context and faithful replay before calibration-derived ROS claims.','Reviewed N2, installed reviewed wrapper and a storage receipt accepted by the runner.','60 s live window then 20 s explicit sqlite3 bag; camera stops before replay on domain 43.','SOURCE-SUPPORTED: exact topics/types, N2 rate bands, full replay count/header/payload agreement, no live contamination.','No accepted storage receipt or card policy support: stop and leave N3 OPEN; do not fabricate the receipt.','DATA/N3; RUN/n3-record and n3-replay including logs and readback.',[
('Pi / prepared bundle', '''python3 wrapper_inspect.py --output "$RUN/wrapper.json"
# UNVERIFIED: card-exception receipt/runner compatibility.
# Run only with a reviewed eligible storage receipt.
python3 n3_record.py --camera-available \\
  --n1-result "$RUN/n1/result.json" \\
  --n2-result "$RUN/n2-accepted/result.json" \\
  --storage-result "$RUN/storage/result.json" \\
  --bag "$DATA/N3" --seconds 20 --output "$RUN/n3-record"'''),
('Pi / after live camera has stopped', '''python3 n3_bag.py replay "$DATA/N3" \\
  --record-result "$RUN/n3-record/result.json" \\
  --live-domain 42 --replay-domain 43 \\
  --output-dir "$RUN/n3-replay"''')], 'n3_record.py/n3_bag.py; n3_topics.json/n3_qos.yaml; archived gate runbook.',extra=['The command interface is verified; compatibility with a strict 128 GB card exception is UNVERIFIED. The bounded-microSD diagnostic path is not equivalent to accepting storage. If N3 remains OPEN, subsequent takes can only be explicitly diagnostic; default qualification sequence stops here.'])
intro('Record contract: one device owner, explicit representations',['Main S/C/A takes use one ROS wrapper plus ros2 bag record, explicit topics and sqlite3.','Native S/C replicas use the checked recorder after ROS stops; their own IDs stay distinct.','Native playback→ROS recording is source-supported but target compatibility is UNVERIFIED.'],'Native Allan CSV has no supplied ROS companion adapter; that branch is blocked.','SOURCE-SUPPORTED ownership / conversion gaps OPEN',note='This is an explicit source limitation, not a claim that two camera owners can run together. Every primary study take is ROS-recorded. Native gate samples and native Allan pilot do not yet have a verified ROS companion. Native replicas are separate physical takes, not synchronized duplicates; home playback recording is derived evidence.')
step('S1.5','ROS recipe shared by S, C1–C3 and A','Record primary takes once with explicit sensor and context topics.','Source-checked study configs deployed at STUDY; actual graph/readback reviewed; one wrapper.','/camera/camera streams + metadata; bag in DATA/ID/ros; parameter and power logs.','ASSUMED 30 Hz profile: image 28.5–31.5, gyro 190–210, accel 95–105 Hz; no reversals/skips, max gaps 1.5 periods.','Power→USB→profile→QoS→storage. Stop on missing metadata/domain; one new-ID retry only.','DATA/ID/ros + RUN/ID parameters, QoS, wrapper and raw power logs.',[
('Pi / camera terminal A', '''export STUDY="$HOME/wbr-runtime/study-docs"
: "${ID:?Bind this step ID in each Pi terminal first}"
mkdir -p "$RUN/$ID"
set -o pipefail
# Source-checked recipe; installed wrapper remains UNVERIFIED.
ros2 launch realsense2_camera rs_launch.py \\
  config_file:="$STUDY/lab-config/ros-stereo.yaml" \\
  2>&1 | tee "$RUN/$ID/wrapper.log"
# Keep this terminal open. Ctrl-C after the bag finalizes.'''),
('Pi / control terminal B', ''': "${ID:?Set current step ID, for example S-ROS-01}"
mkdir -p "$RUN/$ID" "$DATA/$ID"
ros2 param dump /camera/camera > "$RUN/$ID/params.yaml"
ros2 topic list -t > "$RUN/$ID/topics.txt"
ros2 topic info --verbose /camera/camera/gyro/sample \\
  > "$RUN/$ID/gyro-qos.txt"
vcgencmd get_throttled > "$RUN/$ID/power-before.txt"'''),
('Pi / topic selection terminal B', '''TOPICS=(
/camera/camera/infra1/image_rect_raw
/camera/camera/infra2/image_rect_raw
/camera/camera/infra1/camera_info /camera/camera/infra2/camera_info
/camera/camera/gyro/sample /camera/camera/accel/sample
/camera/camera/gyro/imu_info /camera/camera/accel/imu_info
/camera/camera/extrinsics/depth_to_infra1
/camera/camera/extrinsics/depth_to_infra2
/camera/camera/extrinsics/depth_to_gyro
/camera/camera/extrinsics/depth_to_accel /tf_static
/camera/camera/infra1/metadata /camera/camera/infra2/metadata
/camera/camera/gyro/metadata /camera/camera/accel/metadata
)'''),
('Pi / recorder terminal B, same shell', '''# UNVERIFIED: installed metadata presence/field semantics.
ros2 bag record --storage sqlite3 --output "$DATA/$ID/ros" \\
  --qos-profile-overrides-path "$STUDY/lab-config/qos.yaml" \\
  --topics "${TOPICS[@]}"
# Ctrl-C after this take's duration; wait for finalization.
ros2 bag info "$DATA/$ID/ros" > "$RUN/$ID/bag-info.txt"
vcgencmd get_throttled > "$RUN/$ID/power-after.txt"'''),
('Pi / telemetry terminal C, during each take', '''# Bind RUN and ID as in terminal B; Ctrl-C after capture stops.
while true; do
  date -u +%FT%TZ
  vcgencmd get_throttled
  vcgencmd pmic_read_adc EXT5V_V
  vcgencmd measure_temp
  sleep 1
done > "$RUN/$ID/power-periodic.txt" 2>&1''')], 'Local realsense-ros rs_launch.py config_file handling, node parameters and metadata publishers; n3_record.py recorder_argv storage/topics/QoS interface.',extra=['The literal TOPICS array is shared by the slides and LAB_PLAN; define it and run the recorder in the same terminal. Installed ROS/wrapper readiness is UNVERIFIED; check actual topic info and param readback before capture. Scripted diagnostic checks use rates ±5% and 1.5 periods, tighter than N2 gaps; do not substitute thresholds. Metadata must retain SDK timestamp/domain; ROS headers alone cannot establish original domain. For 30 Hz gaps ≤50 ms; gyro ≤7.5 ms; accel ≤15 ms.'])
step('S1.5F','Finalize, hash and preserve each ROS take','A copied bag is usable only after clean stop and checksum verification.','Ctrl-C bag first, wait for metadata; then stop wrapper. No process writes either tree.','ros2 bag info succeeds; hashes verify; original timestamps and failed attempts retained.','Observable: metadata lists every selected topic with nonzero expected counts; SHA256 verifies on Mac.','Keep originals; retry transfer once; mismatch or missing context = unusable/OPEN.','Pi DATA/ID; Mac wbr-data/study-S1-20261018 plus RUN logs.',[
('Pi / after finalization', '''cp "$STUDY/lab-config/ros-stereo.yaml" "$RUN/$ID/"
cp "$STUDY/lab-config/qos.yaml" "$RUN/$ID/"
cd "$DATA/$ID"
find ros -type f -print0 | sort -z | xargs -0 sha256sum \\
  > SHA256SUMS
sha256sum -c SHA256SUMS
# Save periodic telemetry from a separate terminal during takes.
# For all S/C/A takes: before, during, after; errors stay visible.'''),
('Mac / after all writers stop', '''mkdir -p ~/Desktop/Research/wbr-data/study-S1-20261018
rsync -a richard@192.168.50.2:wbr-takes/study-S1-20261018/ \\
  ~/Desktop/Research/wbr-data/study-S1-20261018/
cd ~/Desktop/Research/wbr-data/study-S1-20261018/S-ROS-01
shasum -a 256 -c SHA256SUMS''')], 'Calibration plan manifest/hash requirements; lab runbook steps 10–11; n3_bag.py finalized metadata rules.',extra=['No deletion is part of this plan. Save Git hash and dirty diff, exact config/tool/binary hashes, SDK/wrapper versions, camera identities, raw readbacks/exposure/gain/global-time and motion correction, time domains, notes, requested/observed profile, target, storage identity, power/kernel faults. A new path is required for every retry. Use correct session ID for S2 archives.'])
step('S1.6','S stereo take: static intervals then coverage','Validate factory stereo geometry before trusting metric depth.','Measured rigid A3 6×4 grid; emitter OFF, daylight/NIR light; ROS recipe ready.','120 s S-ROS-01: static ranges then slow target coverage; optional distinct S-NATIVE-01.','ASSUMED: ≥100 matched pairs/four quadrants; RMS ≤0.5 px; row median ≤0.3/p95 ≤1 px; depth ≤2%.','Inspect print→light/exposure→pairing→timestamps before calibration edits; defer failed take to S2.','DATA/S-ROS-01/ros; optional native path printed by recorder; target measurements.',[
('Pi / ROS control before S1.5', '''export ID=S-ROS-01
# Run S1.5 with this ID; record 120 seconds.
# 0-10s: still at 0.5m; 10-20s: 1m; 20-30s: 1.5m.
# Use those ranges only if the small grid decodes in both IRs.
# If not: 0.4 / 0.6 / 0.8m visibility run, mark far-depth OPEN.
# 30-120s: slow sweeps / tilts; four-quadrant coverage.
# Finalize and hash with S1.5F before continuing.'''),
('Pi / OPTIONAL native replica, ROS stopped', '''export WBR_CAMERA_AVAILABLE='CAMERA AVAILABLE'
# Native replica is a new take; repeat the S motion recipe.
bash ~/wbr-runtime/calib-lab-20261015/pi/record_calib_take.sh \\
  S-NATIVE-01 120
# Requires 3,974,400,000 free tmpfs bytes plus disk reserves.
# UNVERIFIED: native playback -> derived ROS companion (H2).
# Without a validated companion route, defer native replica.''')], 'Calibration plan S protocol and thresholds; calibration/lab/pi/record_calib_take.sh exact NAME SECONDS interface.',extra=['Current plan retains 0.5/1/1.5 m depth checks while printable target README gives 0.4–0.8 m A3 visibility range. The small target may not decode at 1.5 m: report the far-depth check OPEN rather than moving an invisible target as if calibrated. Native recorder copies into ~/wbr-evidence/2026-10-15-calib-S-NATIVE-01/take; hard-coded date is the script path, actual UTC belongs in manifest. Full 120 s RAM reserve may fail even on 8 GB; do not shrink to 60 s and claim full S coverage silently.'])
step('S1.7','C1–C3 camera–IMU takes','Three independent excitations expose spatial and temporal repeatability.','Fixed measured grid; same settings/domains; 60 s each, whole target visible, no camera competitors.','Three ROS bags with 5–10 s still ends, smooth XYZ translation and roll/pitch/yaw.','ASSUMED capture: no gaps/skips/blur/saturation, known allowed domains. Home fit: spread ≤3 mm/1°, shift spread ≤1 ms.','Correct one visibility/motion issue; retry with a new ID once; defer missing takes to S2.','DATA/C1-ROS-01/ros through C3; native replicas have separate identities.',[
('Pi / ROS control, each take separately', '''export ID=C1-ROS-01
# Run S1.5 for 60 seconds, then S1.5F.
# Repeat with ID=C2-ROS-01, then ID=C3-ROS-01.
# 0-10s still; 10-25s rotations about each axis.
# 25-45s XYZ translations, +/-15-20cm, mixed motion.
# 45-50s varied target position/range; 50-60s still.
# A3: 0.4-0.8m; A4: 0.3-0.5m. No taps/cable pull.'''),
('Pi / OPTIONAL native replicas, ROS stopped', '''export WBR_CAMERA_AVAILABLE='CAMERA AVAILABLE'
bash ~/wbr-runtime/calib-lab-20261015/pi/record_calib_take.sh \\
  C1-NATIVE-01 60
# Repeat recipe and command as C2-NATIVE-01 / C3-NATIVE-01.
# Each 60s native take needs >=1,987,200,000 tmpfs bytes.
# UNVERIFIED: H2 native-to-ROS companion round trip.
# Defer replicas when that route is not validated.''')], 'Calibration plan §3–4; latest lab step 9; record_calib_take.sh and take_diagnostics.py.',extra=['Native replica output ~/wbr-evidence/2026-10-15-calib-C1-NATIVE-01/take etc. Native scripts do not set/log every exposure/gain control; missing readback stays UNKNOWN and prevents calibration qualification. ROS→Kalibr conversion is not implemented by the native SDK take exporter (H3). No cross-representation count equality is expected between separate physical replicas.'])
step('S1.8','Allan pilot and between-session long recording','Validate raw timing first; long supported τ needs hours at home.','Stable supply/storage, 30 min warm-up at home; rigid stationary camera, cable relieved, no images.','A-ROS pilot then 15 h A-ROS run at home; native 36 s pilot is a separately gated diagnostic.','ASSUMED: gyro/accel ±5%, monotonic allowed domains, zero missing samples; temperature/stationarity documented.','Stop on power faults; never run ROS and native together. Missing CSV→ROS companion means native branch BLOCKED.','DATA/A-ROS-pilot-01/ros; at-home A-ROS-15h-01/ros; native allan-* only if gap resolved.',[
('Pi / ROS camera terminal, replace stereo launch', '''export ID=A-ROS-pilot-01
mkdir -p "$RUN/$ID"
set -o pipefail
ros2 launch realsense2_camera rs_launch.py \\
  config_file:="$STUDY/lab-config/ros-imu.yaml" \\
  2>&1 | tee "$RUN/$ID/wrapper.log"
# A separate recorder terminal runs S1.8R, not S1.5 stereo.
# 36s pilot; clean stop, review, warm 30min before long take.
# Plan 15h at home (4h provisional; target 15-24h).
# Run at home only with maintained safe power/storage setup.'''),
('Pi / native alternative, BLOCKED pending companion', '''# UNVERIFIED: no supplied raw-CSV -> ROS2 companion adapter.
# Do not execute this branch until that requirement is resolved.
cd ~/wbr-runtime/allan-20261014
bash ./record_allan.sh 0.01 A-native-pilot-01
# After reviewed pilot and 30min warm-up, at home only:
nohup bash ./record_allan.sh 15 A-native-15h-01 \\
  > "$HOME/allan-A-native-15h-01.launch.log" 2>&1 < /dev/null &''')], 'calibration/allan/record_allan.sh and README.md; current calibration plan wins over lab suggestion to use weak PSU.',extra=['The script accepts HOURS NAME (0.01–30 h), preserves separate 17-digit native gyro/accel CSV, and budgets 207.36 MB/h plus logs with 3× reserve. Long native 15 h CSV budget is 3.1104 GB, not the older 160 B/row plan estimate. ROS raw Imu serialization is larger: measure pilot bytes/hour and reserve ≥2× projected bag plus OS reserve. No supervised lab session includes those 15 hours. If overnight home access is unavailable, leave physical Allan OPEN rather than replacing it with a short lab sample.'])
step('S1.8R','Allan ROS recording: explicit IMU-only bag','Keep every primary A take in ROS 2 bag format without image traffic.','One IMU-only wrapper; copied study QoS; named duration and periodic power monitoring.','A finalized sqlite3 bag with raw gyro/accel, their metadata/context and static TF.','Observable: no image topic selected; expected raw-rate counts, finite values, source domain metadata, clean shutdown.','No metadata or data loss: reject qualification; preserve bag and review at home.','DATA/A-ROS-pilot-01/ros; same structure for A-ROS-15h-01.',[
('Pi / recorder terminal B', '''export ID=A-ROS-pilot-01
mkdir -p "$RUN/$ID" "$DATA/$ID"
ros2 param dump /camera/camera > "$RUN/$ID/params.yaml"
ros2 bag record --storage sqlite3 --output "$DATA/$ID/ros" \\
  --qos-profile-overrides-path "$STUDY/lab-config/qos.yaml" \\
  --topics /camera/camera/gyro/sample \\
  /camera/camera/accel/sample /camera/camera/gyro/metadata \\
  /camera/camera/accel/metadata \\
  /camera/camera/gyro/imu_info /camera/camera/accel/imu_info \\
  /camera/camera/extrinsics/depth_to_gyro \\
  /camera/camera/extrinsics/depth_to_accel /tf_static
# Ctrl-C after 36s pilot; at home use ID=A-ROS-15h-01.
# Finalize and hash with S1.5F, copy ros-imu.yaml as config.''')], 'n3_record.py storage/QoS/topics interface; local wrapper metadata publishers. ROS A→native Allan CSV exporter remains UNVERIFIED.',extra=['Primary ROS A records satisfy bag preservation. The supplied allan_analyze.py expects native raw CSV files and meta.json, not ordinary ROS sensor topic bags; no direct call on A-ROS is valid. The missing extraction/round-trip interface is an explicit H3 preparation gap. Use original raw stamps/units with full precision after reviewed extraction; never substitute bag-write time.'])
step('S1.9','Step 9b link bench: wire and check','Validate the link and message integrity with camera load removed.','Mac powers/flashes F446RE bench image; Pi TX8→D2/PA10, RX10←D8/PA9, GND6↔GND.','About 20 status records/s in NO_LINK, LED follows traffic; no motor code.','SOURCE-SUPPORTED expected: 3000 sent/0 lost; faults CRC/duplicate/session 10/10; wire errors/reboots zero.','Power→GND→pin crossing→port/console→firmware. Missing ttyAMA0: owner setup later or documented USB fallback.','Pi /tmp/wbr_link_bench/out-ID; Mac session/link-bench; firmware SHA256.',[
('Mac / before wiring, prepared binary', '''cd ~/Desktop/Research/wbr-perception-phase1-runtime
test -f tools/link_bench/firmware/prebuilt/link_bench_f446.bin
shasum -a 256 \\
  tools/link_bench/firmware/prebuilt/link_bench_f446.bin
# Owner flashes this bench image from Mac before the session.
# Never flash the CN/OS image for this test or power MCU from Pi.'''),
('Pi / control, camera unplugged', '''ls -l /dev/ttyAMA* /dev/ttyACM* /dev/serial*
groups
grep -n uart /boot/firmware/config.txt
cat /proc/cmdline
# Verify no console/getty owns the chosen device.
export PORT=/dev/ttyAMA0
python3 /tmp/wbr_link_bench/link_bench.py \\
  --port "$PORT" --out /tmp/wbr_link_bench/out-S1-01''')], 'sources/STM32_LINK_STEP_2026-10-15.md; tools/link_bench/pi/link_bench.py and firmware prebuilt image.',extra=['Pre-lab Mac firmware flash can use cp of the checked binary to the verified /Volumes/NOD_F446RE/ drive per source; do not invent another board drive. /tmp/wbr_link_bench/ must include link_bench.py and adjacent link_proto.py copied from tools/link_proto/py/. If owner chooses fallback, PORT=/dev/ttyACM0 after USB moves to Pi; label USB path and recheck power. No config.txt edits/reboot in these short sessions. GPIO path expected RTT floor is calculated; no RTT upper budget invented.'])
step('S1.9T','Step 9b timeouts and optional 9c','Verify silence behavior without confusing it with OS supervisor states.','9b successful; analyzer optional, 3.3 V, 12 MHz, 15 s capture; camera unplugged.','100 ms silences: 0/5 NO_LINK. 300 ms: 5/5 NO_LINK, ≈150–151 ms silence, 5/5 recovered.','SOURCE-SUPPORTED expected observable counts above; bench NO_LINK ≠ HOLD/FAILSAFE.','Check baud/channels/ground first; failed marker = keep 9b-only timing; retry once, then defer.','la-S1-01/summary.json, capture VCD or digital CSV, la.json.',[
('Pi / only after analyzer capture starts', '''python3 /tmp/wbr_link_bench/link_bench.py \\
  --port "$PORT" --out /tmp/wbr_link_bench/la-S1-01 \\
  --phases rtt --duration 10 --marker-gpio 17'''),
('Mac / after copying capture and summary', '''cd ~/Desktop/Research/wbr-perception-phase1-runtime
python3 tools/link_bench/pi/la_analyze.py cap.vcd \\
  --summary la-S1-01/summary.json --out la-S1-01/la.json''')], 'Link source steps 9b/9c; la_analyze.py CLI.',extra=['Probe D0 CN10-33 PA10, D1 CN10-21 PA9, D3 CN10-23 PA8, GND CN10-20. D2 Pi pin11 GPIO17. Expected CALCULATED pi_tx_wire≈2210 us, reply_wire≈1430 us, ~500 matched markers. Decode/reply timing is to be MEASURED, not assigned a fake threshold.'])
step('S1.10','Session handoff: stop at 150 minutes','Preserve failures and choose the smallest Session-2 reruns.','All writers stopped; no clone; every completed directory copied to Mac and verified.','A table of completed, failed, marginal, skipped steps with cause and required equipment.','Observable: hashes match; each failure has next action; no gate status silently promoted.','Preserve Pi originals, retry transfer once; incomplete copy means no deletion or unsupported conclusion.','Mac session/ plus RUN; handoff.md lists exact S2 retry IDs and Allan status.',[
('Mac / copy small logs too', '''mkdir -p ~/Desktop/Research/wbr-data/study-S1-20261018/logs
rsync -a \\
  richard@192.168.50.2:wbr-evidence/study-S1-20261018/ \\
  ~/Desktop/Research/wbr-data/study-S1-20261018/logs/
# Review SHA256SUMS for every copied take as in S1.5F.
# Record A-ROS long-run availability and native/ROS gaps.
# Owner handles clean shutdown after evidence verification.'''),
('Mac / completed native or bench branches only', '''export ARCH="$HOME/Desktop/Research/wbr-data/study-S1-20261018"
export WBR_HOST=richard@192.168.50.2
# For EACH completed native ID only; example C1:
export TAKE=C1-NATIVE-01
mkdir -p "$ARCH/native/$TAKE"
rsync -a "$WBR_HOST:wbr-evidence/2026-10-15-calib-$TAKE/" \\
  "$ARCH/native/$TAKE/"
(cd "$ARCH/native/$TAKE/take" && \\
  shasum -a 256 -c ../ram-sha256.txt)
# Repeat TAKE=S-NATIVE-01 / C2-NATIVE-01 / C3-NATIVE-01 if done.
# If 9b/9c ran, preserve its entire output before /tmp is cleared:
rsync -a "$WBR_HOST:/tmp/wbr_link_bench/" "$ARCH/link-bench/"''')], 'Latest lab source steps 10–11; current calibration plan preservation policy.',extra=['Handoff fields: step/take, requested/resolved profile, success/failed/marginal/skipped, raw paths/hash, power/USB/timing issue, one correction, new retry ID, remaining time, owner-required setup, overnight A state. Card clone from original long-day source is deliberately outside the two-session plan.'])
# PART B1 END
take_home(globals(),1)
session_map(globals(),2)
table('Session 2 timeline: 150 min maximum',['Elapsed','Task / exit artifact'],[['0–30 min','S2.0: one corrected rerun per failed/marginal S1 branch.'],['30–65 min','S2.1: E6 two-Pi edge run; selected sweep, not full campaign.'],['65–95 min','S2.2: E7-C real-UART readiness / bounded trial.'],['95–130 / 130–150 min','S2.3–6: CN/OS fault demo; verified archive and stop.']],'If E7/supervisor preparation is missing, document BLOCKED; do not improvise firmware.','ASSUMED wall-time budget',widths=[57,123])
step('S2.0','Rerun only the earliest failed S1 condition','Spend the retry budget on one discriminating correction.','Read handoff; rebind P0 with fresh study-S2-20261019 paths; power/identity rechecked.','A new-ID attempt with one changed cause; original attempt stays immutable.','Observable: rerun meets the original numeric/observable criteria; no weakened threshold.','At 30 min stop retries; mark OPEN and continue only independent CN work with healthy power.','DATA/new retry IDs; RUN/S2-rerun-ledger.md and fresh N1 after any reboot.',[
('Pi / control, fresh bindings', '''export RUN="$HOME/wbr-evidence/study-S2-20261019"
export DATA="$HOME/wbr-takes/study-S2-20261019"
mkdir -p "$RUN" "$DATA"
vcgencmd get_throttled > "$RUN/power-before.txt"
lsusb -t > "$RUN/usb-before.txt"
# Repeat only the failed S1 step, with new output paths/IDs.
# Example ID=C2-ROS-retry01; same S1.5/S1.7 recipe.
# Reboot/topology change: renew N1; never reuse the old receipt.''')], 'Calibration plan, gate receipt rules and S1 handoff. S2 date is an explicit run-ID example.')
step('S2.1','CN/OS integration: E6 two-Pi edge offloading','Measure real-network RTT and outcomes separately from service time.','8 GB Pi B edge server, 4 GB Pi A client; camera disconnected; prepared CN root, local consoles.','Server READY; client frames.csv + meta.json; edge service-times.csv on its own clock.','ASSUMED smoke: 200 outcomes for 20 s×10 fps, no unidentified frame. Report actual late/lost; clean power required.','Power→route/interface→server/port→protocol→queue/service. One new-output retry; never fake remote timestamps.','Client results_hw/E6/study-S2-*; server hw/results/study-S2-*/ plus preflight.',[
('8 GB server B / ~/CN prepared checkout', '''cd ~/CN
sudo ip link set eth0 up
sudo ip address replace 192.168.77.2/24 dev eth0
sh hw/preflight.sh eth0 /tmp/e6-server-before.json
python3 hw/edge_server.py --host 192.168.77.2 --port 9000 \\
  --transport udp --mode synthetic --sleep-ms 4 \\
  --queue latest \\
  --service-log hw/results/study-S2-udp/service-times.csv'''),
('4 GB client A / local console, after READY', '''cd ~/CN
sudo ip link set eth0 up
sudo ip address replace 192.168.77.1/24 dev eth0
ping -c 3 192.168.77.2
python3 hw/sender.py --host 192.168.77.2 --transport udp \\
  --frame-bytes 30000 --fps 10 --duration 20 \\
  --out-dir results_hw/E6/study-S2-smoke-udp-01
python3 hw/run_e6.py --link ethernet --transport udp \\
  --dry-run'''),
('4 GB client A / selected E6 pass', '''# After reviewed smoke; 30 runs x20s, plus overhead.
python3 hw/run_e6.py --link ethernet --transport udp \\
  --output-root results_hw/E6/study-S2-wired-udp-01
# Repeat TCP only after stopping/restarting server as TCP.
# Wi-Fi: existing AP; verify route dev wlan0 before any run.
# Full four-pass /120-run campaign is outside this session.
# Retain both Pi models, supplies, clocks and before/after flags.''')], 'CN hw/README.md, hw/{edge_server,sender,run_e6,os_inference}.py; configs/E6hw.yaml; docs/HARDWARE.md (owner 16 Oct).',extra=['~/CN is the explicit pre-lab deployment location on both Pis; do not assume it exists without P0. Address commands are source examples for unused 192.168.77.0/24 and require local console if Ethernet carries SSH. Do not mutate a management route blindly. E6 sweep declares synthetic 4 ms service; --queue latest is explicitly logged. No ONNX claim: optional ONNX needs actual model/runtime/hash, separate root and compatible config. Default runner includes separate preflight per run and validates route; 1-client E6 hardware is not equal to 2-client simulator.'])
step('S2.1W','CN/OS integration: Wi-Fi / ONNX branches','Keep transport and compute claims tied to the actual test.','Existing AP connection, both Pis local consoles; do not infer Wi-Fi 6 from Pi name.','Matching UDP or TCP endpoints; sender-clock RTT and server-local service/queue times.','Observable: route dev wlan0; all frame outcomes retained. ONNX unavailable = UNKNOWN, never relabel synthetic.','Wrong route: stop branch; do not reconfigure AP at lab. Missing model/runtime: use labeled synthetic run.','Fresh results_hw/E6/study-S2-wifi-*; separate model hash and server log.',[
('8 GB server B / existing Wi-Fi', '''WIFI_B=$(ip -4 -o address show dev wlan0 scope global \\
  | awk '{split($4,a,"/"); print a[1]; exit}')
python3 hw/edge_server.py --host "$WIFI_B" \\
  --transport udp --mode synthetic --sleep-ms 4 \\
  --service-log hw/results/study-S2-wifi/service-times.csv'''),
('4 GB client A / use server printed IPv4', '''read -r -p 'Pi B Wi-Fi IPv4 address: ' WIFI_B
ip route get "$WIFI_B"
# Continue only if route is dev wlan0.
python3 hw/sender.py --host "$WIFI_B" --transport udp \\
  --frame-bytes 30000 --fps 10 --duration 20 \\
  --out-dir results_hw/E6/study-S2-wifi-udp-01
# Repeat as -02/-03 if time; TCP requires matching server.
# Optional ONNX service syntax (separate run/config):
# --mode onnx --model EXISTING_MODEL.onnx --threads 1'''),
('8 GB server B / OPTIONAL prepared ONNX branch', '''# UNVERIFIED installed model/runtime; use a separate run root.
cd ~/CN
test -s offline-bundle/mobilenetv2-12.onnx
sha256sum offline-bundle/mobilenetv2-12.onnx
python3 hw/edge_server.py --host 192.168.77.2 --port 9000 \\
  --transport udp --mode onnx \\
  --model offline-bundle/mobilenetv2-12.onnx --threads 1 \\
  --queue latest \\
  --service-log hw/results/study-S2-onnx/service-times.csv
# Client: S2.1 sender, new output name study-S2-onnx-01.
# Do not use unchanged synthetic-4ms E6 sweep config here.''')], 'CN hw/README.md Wi-Fi and ONNX sections; hw/os_inference.py fixed-image preprocessing.',extra=['Network bytes are load, not decoded JPEG inference. Freeze transport, payload, fps, model/hash, threads and queue to compare. Remote absolute t_rx/t_start/t_done stay empty; do not derive them from RTT. No hardware E6 result is established by writing this deck.'])
step('S2.2','CN/OS integration: E7-C UART gateway trial','Add F446RE ingress while separating UART delay from network RTT.','Prepared owner CubeMX E7 image, gateway Pi A, edge Pi B; 3.3 V crossed UART, common ground.','CRC-checked chunked frames reach gateway and edge; outcomes include UART and network intervals separately.','DESIGN: stable unique frame IDs, one terminal outcome each; corrupt frames never forwarded. Hardware baud/MCU inference remain UNTESTED.','Power→GND/pins→baud/console→CRC/chunks→server. Missing built firmware = BLOCKED, no guessed flash command.','results_hw/E7/study-S2-edge-udp-01/{args.json,frames.csv,outcomes.jsonl}.',[
('4 GB gateway A / ~/CN', '''# UNVERIFIED hardware: owner's E7 firmware and real UART.
python3 e7/gateway/gateway.py --serial /dev/serial0 \\
  --baud 115200 --host 192.168.77.2 --port 9000 \\
  --transport udp --reply-format timed \\
  --outDir results_hw/E7/study-S2-edge-udp-01
# Stop normally with Ctrl-C after the bounded fixture trial.
# Repeat TCP only with matching timed-reply server.
# No --net-status-ms here until a compatible supervisor exists.''')], 'CN docs/E7_DESIGN.md option C, docs/CODEX_TICKETS.md E7/E7d2/T18; e7/README.md and gateway.py.',extra=['E7 image format is not WBR link bench or OS UART framing. Default firmware has fixed 1×1 JPEG, no trained tiny-CNN. USART2 PA2/PA3 uses ST-LINK VCP; USART1 direct route PA9 TX→Pi15 RX, PA10 RX←Pi14 TX; qualify solder bridges and port. Start 115200 8N1; 921600/2M sustained hardware reliability UNTESTED. At least 100 transfers per size/baud and 3 network repetitions are full design qualification outside this short smoke trial. UART response-to-MCU egress is unimplemented. No cloud endpoint is selected; cloud branch deferred.'])
step('S2.3','CN/OS integration: supervisor readiness','Prove real UART FRESH before attempting Wi-Fi loss.','Owner-prepared OS v3 board image with NET_STATUS support, one UART writer, compatible CN-result IPC producer.','Local heartbeat + local INFERENCE + NET_STATUS all healthy; MCU_STATUS reports state 1.','SOURCE-SUPPORTED: FRESH=1 observed, state/clock telemetry saved. Only host/PTY tested so far; physical path UNTESTED.','Missing image/producer or no FRESH: BLOCKED. E7 telemetry alone sends no INFERENCE; do not pretend it is enough.','OS bridge.csv, inf_rx.csv, state_events.csv, firmware/config hashes; readiness notes.',[
('Gateway Pi / prepared OS checkout', '''# UNVERIFIED: deployed image, UART and CN-result IPC producer.
# Source interface exists; this hardware recipe is not validated.
linux/build/hea_bridge --socket /tmp/cn-results.sock \\
  --serial /dev/ttyAMA0 --baud 921600 \\
  --heartbeat-ms 20 --net-status-ms 20 --policy latest \\
  --csv bridge.csv
# Do NOT run E7 gateway as another writer to the same UART.
# CN producer must provide accepted <IQQBBI IPC records.
# No verified producer/flash command is supplied: STOP if absent.''')], 'OS-wt-cn docs/CN_INTEGRATION.md and protocol/PROTOCOL.md; CN e7/gateway/NET_STATUS.md.',extra=['This is a pre-lab integration dependency, not a fabricated executable. Original requested OS protocol v1 names INIT/FRESH/HOLD/FAILSAFE but NET_STATUS is a later v3 extension in OS-wt-cn. Updated full board image status is UNKNOWN there; only portable sources cross-compiled and host tests passed. Existing E7 gateway --net-status-ms 20 can emit v3 HB/status with one sequence, but sends no INFERENCE or MCU clock map and alone cannot satisfy supervisor local readiness. IPC clock stamps must be explicitly mapped to gateway RAW; remote host times are invalid.'])
step('S2.4','CN/OS integration: Wi-Fi loss while heartbeat lives','Show stale network results cause HOLD then latched FAILSAFE.','S2.3 FRESH, local HB stays 20 ms; stop result path only; local consoles, bench without motors.','FRESH→HOLD at result/network age ≥200 ms; FAILSAFE ≥500 ms (provisional defaults).','Observable: state_events records ordered 1→2→3 with age/silence reasons; no hidden state-event loss.','If HB stops, this is the heartbeat fault instead. Restore link; preserve trace; do not change timeouts.','bridge.csv + state_events.csv + fault-on/off times and server/gateway interface notes.',[
('Wi-Fi transmitting peer / prepared OS scripts', '''# UNVERIFIED real Wi-Fi/UART integration; source CLI verified.
# Affect outgoing results on edge server B, not management SSH.
scripts/netem_inject.sh --dry-run apply wlan0 --loss 100
# After owner checks the printed direction and local console:
scripts/netem_inject.sh apply wlan0 --loss 100
# Leave >500ms while gateway HEARTBEAT stays alive.
# Observe and save MCU states, then restore the path:
scripts/netem_inject.sh clear wlan0''')], 'OS-wt-cn scripts/netem_inject.sh; docs/CN_INTEGRATION.md network age/silence transitions; CN synergy part 6.',extra=['Loss injection is outbound root qdisc; clear deletes instead of restoring previous custom qdisc. Do not apply on an interface with a valued existing root policy; prepare isolated link beforehand. On server B, lost replies stop accepted results at gateway; HB continues locally. This is controlled Wi-Fi result-delivery loss, not a proof of radio disassociation. An actual AP outage can be added manually only after recording network path; expected state semantics stay the same. Loss telemetry counts result identities, not raw Wi-Fi packet loss.'])
step('S2.5','CN/OS integration: recover and test heartbeat loss','Demonstrate the two recovery contracts and Pi independence boundary.','Restore network; latched FAILSAFE observed; owner resets the bench board; no actuation.','After reset and new accepted traffic: INIT→FRESH. HOLD-only short fault can recover automatically.','Observable: latched FAILSAFE never clears merely on resumed packets. Stopping HB gives FAILSAFE near 100 ms, not HOLD first.','Unexpected state: stop; save raw protocol/state trace. Missing hardware test leaves robot independence unproven.','Separate recovery and HB-loss traces; board reset/fault notes and exact config.',[
('Gateway / manual controlled fault sequence', '''# Restore Wi-Fi result path and preserve prior trace first.
# Owner presses board RESET after latched FAILSAFE.
# Verify fresh HB + INFERENCE + NET_STATUS -> INIT then FRESH.
# For HB-loss case: Ctrl-C the sole hea_bridge process.
# Expected provisional HB timeout: 100ms -> latched FAILSAFE.
# Resume bridge; packets alone do not clear the latch.
# Owner resets board, re-establishes FRESH; save a new trace.
# HOLD-only recovery needs measured <500ms result interruption.
# UNVERIFIED: bounded real-network short fault timing fixture.''')], 'OS protocol v3 and docs/CN_INTEGRATION.md explicit latched/rearm/board-reset policy.',extra=['Network age includes reported age + local MCU silence + provisional transit allowance. Thresholds are configuration, not measured physical response guarantees. Measure MCU state-change time on MCU clock or validated mapping; shell/netem command duration is not wire fault onset. There is no remote rearm wire command. Board reset demonstrates this port’s recovery, not uninterrupted WBR balancing. Real robot must retain independent control by architecture; physical N7 remains OPEN.'])
step('S2.6','CN/OS integration: archive and interpret honestly','Finish at 150 min with retained traces and explicit missing hardware evidence.','All jobs stopped normally; netem cleared; each Pi power sampled; Mac reachable.','Both node traces, UART states, configs and hashes copied; pass/fail/missing separated.','Observable: one outcome per generated frame, no cross-clock subtraction, matching copied hashes; no unsupported gate promotion.','Retain node originals; failed transfer blocks deletion; missing telemetry is UNKNOWN.','Mac wbr-data/study-S2-20261019/{wbr,cn-client,cn-server,os}; summary.md.',[
('Each Pi / control', '''vcgencmd get_throttled
vcgencmd pmic_read_adc EXT5V_V
# Save the raw values in that node's run directory.
# On edge peer if injection was used:
scripts/netem_inject.sh status wlan0
# Verify cleared qdisc; do not infer it from restored replies.
# Copy both CN results roots and OS CSVs to Mac; hash finalized files.
# Owner shuts down only after the archive verification.'''),
('Mac / both-node CN archive, then hash review', '''export ARCH="$HOME/Desktop/Research/wbr-data/study-S2-20261019"
mkdir -p "$ARCH/cn-client" "$ARCH/cn-server" "$ARCH/os"
# UNVERIFIED deployment SSH targets/routes: bind from lab inventory.
read -r -p 'Client SSH user@host: ' CN_CLIENT_SSH
read -r -p 'Edge SSH user@host: ' CN_EDGE_SSH
rsync -a --checksum "$CN_CLIENT_SSH:CN/results_hw/" \\
  "$ARCH/cn-client/"
rsync -a --checksum "$CN_EDGE_SSH:CN/hw/results/" \\
  "$ARCH/cn-server/"
# OS trace dir is a pre-lab binding, not a guessed path.
# Copy bridge/inf_rx/state_events CSVs plus firmware/config hashes.
# Verify per-node finalized SHA256 manifests as in S1.5F.''')], 'CN hw/README.md, E7 retained timing contract; OS CN integration telemetry; WBR source handoff policy.')
# PART B2 END
take_home(globals(),2)
current_part='home'
intro('At home: analyze immutable inputs',['Begin with copied hashes, bag metadata, raw counts/timestamps and config identities.','Then validate conversion, fit calibration/noise and replay the same data repeatedly.','Only independent ground truth permits ATE/RPE; room routes provide proxies.'],'Keep acquisition failures visible through every derivative.','SOURCE-SUPPORTED offline workflow')
step('H0','Home: bag metadata, replay and timestamps','Separate a complete recording from a merely readable bag.','Finalized copied bags; sourced ROS environment at home; no live camera publisher.','Topic/type/count table, source stamps, raw domains and complete replay observations.','ASSUMED: zero unexplained drops/reversals; complete context; replay count/header/pixel equality. Bag-info alone is insufficient.','Hash mismatch→copy; missing context→QoS; timestamp issue→raw metadata. Do not sort or fill data to hide gaps.','derived/bag-info.txt, timing/count report, replay logs; originals immutable.',[
('Home Linux / sourced Jazzy', '''export BAG="$HOME/wbr-takes/study-S1-20261018/S-ROS-01/ros"
ros2 bag info "$BAG"
# Stop live wrapper first; use isolated localhost replay domain.
export ROS_DOMAIN_ID=43 ROS_LOCALHOST_ONLY=1
ros2 bag play "$BAG" --rate 1.0 --delay 3 \\
  --qos-profile-overrides-path "$STUDY/lab-config/qos.yaml"
# In another domain-43 terminal: observe source headers/counts.
# UNVERIFIED: extended stereo/metadata bag audit interface.
# n3_bag.py accepts only its reviewed N3 receipt/topic contract.''')], 'n3_bag.py play flags and strict replay contract; current calibration plan raw timing checks.',extra=['Use both N/requested-window and (N−1)/(last−first) surviving-span rates; inspect boundaries, dt histograms, domains, sequence gaps and original metadata. ros2 topic hz is supplemental and does not prove zero loss. ROS→SDK-audit conversion is absent; no invented check script. Record source header separately from rosbag storage time.'])
step('H1','Home: native SDK bag audit and EuRoC export','Inspect the format before decoding and retain original timestamp provenance.','Mac canonical WBR checkout; finalized copied native take; fresh output root.','Audit JSON/Markdown, manifest, grayscale PNGs, raw gyro/accel and gyro-grid CSV, times_ns.txt.','SOURCE-SUPPORTED: common allowed SDK domain, valid order, no rejected gaps; times file nonempty and strictly inside IMU coverage.','Unsupported schema/ROS1 magic: stop; do not rename a bag or use diagnostic override to claim qualification.','derived/C1-native-euroc/{audit,manifest,times_ns,mav0,...}.',[
('Mac / canonical WBR checkout', '''export ARCH="$HOME/Desktop/Research/wbr-data/study-S1-20261018"
export NATIVE="$ARCH/native/C1-NATIVE-01/take"
export DERIVED="$HOME/Desktop/Research/wbr-data/derived-study"
python3 tools/take_tools/take_tools.py inspect \\
  "$NATIVE/stereo_imu.db3"
python3 tools/take_tools/take_tools.py audit \\
  "$NATIVE/stereo_imu.db3" --json /tmp/C1-audit.json \\
  --markdown /tmp/C1-audit.md
python3 tools/take_tools/take_tools.py export-euroc \\
  "$NATIVE/stereo_imu.db3" "$DERIVED/C1-native-euroc"''')], 'tools/take_tools/README.md and take_tools.py; older experiments/2026-10-14-db3-to-euroc/db3_to_euroc.py inspected but not selected.',extra=['Use take_tools.py, not the older converter: it preserves Decimal SDK milliseconds→integer ns, independent raw streams, pixel hashes, interpolation exclusions and strict times-file interior. The older db3_to_euroc.py uses different fixed assumptions; do not mix its CLI/schema. export-euroc expects native /device_0/... metadata, not /camera/camera/... ordinary ROS bags. Take format is detected from magic, not extension. Native domain SYSTEM_TIME is excluded by calibration policy even if a structural tool would accept it.'])
step('H2','Home: native replica → derived ROS companion','Validate a ROS representation of each native take without opening the device twice.','One finalized native SDK file; ROS recorder ready before file playback; camera physically unplugged.','Wrapper source supports rosbag_filename; a derived ROS bag has original source identities checked.','UNVERIFIED physical format/startup behavior: accept only exact full counts/source stamps/pixels, metadata domains retained.','Any lost beginning/end, rewritten stamp/domain or unsupported db3: BLOCKED companion conversion, retain native file.','derived/C1-native-ros/; conversion receipt with native hash and first/last IDs.',[
('Home ROS / file publisher, no live camera', '''# UNVERIFIED: db3 load and lossless full-window behavior.
# Start ros2 bag record with the S1.5 explicit topic list first.
ros2 launch realsense2_camera rs_launch.py \\
  config_file:="$STUDY/lab-config/ros-stereo.yaml" \\
  rosbag_filename:="$NATIVE/stereo_imu.db3" rosbag_loop:=false
# No tested pause/start handshake exists in this recipe.
# Never claim this derived replay is a second live measurement.
# Native A CSV has no rosbag_filename route: see H3.''')], 'Local realsense-ros realsense_node_factory.cpp load_device and rs_launch.py rosbag_filename/rosbag_loop; live_record_db3_play test source.',extra=['A native SDK .db3 is a recording format, not an ordinary wrapper topic bag. Wrapper playback may remap stamps or begin before discovery; source support does not prove exact conversion. A native replica is not scheduled until this requirement is validated. The mandated ROS companions for native N2/vendor CSV and native Allan CSV remain absent. This is a material input-tool gap recorded in REVIEW_LOG.md.'])
step('H3','Home: conversion boundary and preparation gaps','Prevent a valid command from being used on the wrong bag schema.','Distinguish wrapper ROS bags, native SDK bags and native full-precision IMU CSV.','Native S/C → take_to_kalibr_bag works by source; ordinary ROS S/C and A need reviewed extraction.','Observable: input/output counts, raw metadata/header stamps ≤1 µs, pixel hashes and SI units match. Missing extractor = UNVERIFIED.','Stop fitting; prepare and test conversion at home. Do not invent a script or copy bag-write times into source headers.','Conversion receipt, count/stamp/pixel comparison; all rejected derivatives retained.',[
('Mac / native S/C only', '''cd ~/Desktop/Research/wbr-perception-phase1-runtime
bash calibration/lab/mac/take_to_kalibr_bag.sh \\
  "$NATIVE" "$DERIVED/C1-native-kalibr"
# Repeat independently for C2, C3 and S native takes.
# UNVERIFIED: wrapper ROS bag -> Kalibr source-stamp exporter.
# UNVERIFIED: ROS raw IMU -> Allan CSV extraction.
# UNVERIFIED: native Allan / native N2 -> ROS companion.
# No executable for those absent interfaces is claimed.''')], 'calibration/lab/mac/take_to_kalibr_bag.sh and README.md; tools/take_tools native schema.',extra=['The Kalibr helper calls an exact fixed Foundation tool path /Users/quockaiser/Desktop/Research/wbr-sw-foundation/tools/take_tools/take_tools.py, not automatically this worktree copy. Verify its source hash and prepared Docker image before use. common.sh hard-codes FOUNDATION and IMAGE; there is no environment override. Verify the fixed paths/image; never invent LAB_FOUNDATION. ROS1 output topics are /cam0/image_raw /cam1/image_raw /imu0. Do not pass --diagnostic for accepted calibration.'])
step('H4','Home: Kalibr C fits and stereo validation','Judge residuals and repeatability before selecting a candidate.','Native ROS1 take.bag conversion audited; actual measured target YAML; prepared Intel-Mac Docker image.','Per-take reports/results/camchain; provisional or measured-noise receipt; candidate ORB YAML.','ASSUMED: radial RMS ≤0.5 px; 3 C fits spread ≤3 mm/1°, shift ≤1 ms. S baseline difference ≤1 mm.','Data timing→target/light→motion→frame direction→noise; never replace factory from an attractive single fit.','DERIVED/C1-imucam through C3; S-stereo; report PDFs/logs and orbslam3/ candidates.',[
('Mac / canonical WBR checkout', '''export TARGET="$HOME/Desktop/Research/wbr-data/measured-target.yaml"
bash calibration/lab/mac/run_kalibr_camimu.sh \\
  "$DERIVED/C1-native-kalibr/take.bag" "$TARGET" \\
  "$DERIVED/C1-imucam"
# Repeat with C2/C3 input/output names, no overwrites.
# Optional fourth arg is a supported measured IMU noise YAML.
bash calibration/lab/mac/run_kalibr_stereo_check.sh \\
  "$DERIVED/S-native-kalibr/take.bag" "$TARGET" \\
  "$DERIVED/S-stereo"''')], 'calibration/lab/mac/{run_kalibr_camimu,run_kalibr_stereo_check}.sh and summarize_kalibr.py.',extra=['Cam-IMU uses --cams plural, fixed factory chain, calibrated IMU model and default temporal estimation. Do not pass --no-time-calibration. Report radial RMS from pixel mean/std, not normalized residual or mean alone. Check all axes/residual structure/failed detections, proper orthonormal R, det≈+1, CAD ≤5mm/2° as comparison, not forced truth. Candidate converter emits PinHole; current operating model Rectified. Review rectification before deployment and apply time shift once via a separately reviewed hook; no ORB YAML time-offset field exists.'])
step('H5','Home: Allan fitting on native raw channels','Estimate only slopes supported by stationary physical data.','Completed full-precision native A data and power metadata; primary ROS A needs H3 extraction first.','Per-axis deviation plots, fit ranges/counts, raw/x10 YAML and UNKNOWN unsupported walks.','ASSUMED: slope −0.5/+0.5 ±0.1 over ≥1 decade, R²≥0.95, ≥30 clusters/point; half-run estimates within 30%.','No supported walk: report UNKNOWN; timing faults split segments, never resample across gaps; rerun if power unclean.','OUT/allan.json, summary.md, imu_allan_raw.yaml, imu_allan_x10.yaml, plots.',[
('Mac / native A only after preservation requirement resolved', '''python3 calibration/allan/allan_analyze.py \\
  "$HOME/Desktop/Research/wbr-data/allan-A-native-15h-01" \\
  "$DERIVED/A-native-15h-analysis"
# Do not pass an ordinary ROS bag directory to this command.
# Null YAML scalars are UNKNOWN and cannot feed Kalibr/ORB.
# Review raw native accel100 / gyro200, not interpolated accel.
# First/second-half stability comparison is not automated here.''')], 'calibration/allan/allan_analyze.py and README.md; calibration plan §5.',extra=['N units gyro rad/s/sqrt(Hz), accel m/s²/sqrt(Hz); walk units gyro rad/s²/sqrt(Hz), accel m/s³/sqrt(Hz). ORB continuous values: NoiseGyro/NoiseAcc/GyroWalk/AccWalk; no pre-discretization. x10 is an ASSUMED ablation hypothesis, not measured noise. Power metadata may label DIAGNOSTIC; keep historical sticky flags, monitoring errors and temperature source (Pi SoC, not IMU).'])
step('H6','Home: offline ORB before any live experiment','Replay one immutable motion take to separate code and sensor causes.','Explicit owner CAMERA AVAILABLE authorization for any ORB per runbook; prepared Pi at home; camera may be unplugged.','EuRoC export/times_ns, retained run/command/power logs and trajectory or explicit failure.','ASSUMED review: IMU init ≤30 s, one map, zero resets, loss ≤1%, no single loss >1 s; proxies need route reference.','Hash/export→build identity→coverage→calibration→motion. No rebuild/tuning to hide input faults; preserve crashes.','demo-day runs/NAME, offline/demo_plot.png and demo_stats.json; raw bags copied separately.',[
('Mac / optional existing demo take, not a C/S path', '''cd ~/Desktop/Research/wbr-perception-phase1-runtime
export WBR_HOST=richard@192.168.50.2
# Requires an actual completed native demo record hand100.
# Do not rename a calibration take to satisfy this wrapper.
bash experiments/2026-10-15-demo-day/demo.sh offline hand100
bash experiments/2026-10-15-demo-day/demo.sh fetch hand100
bash experiments/2026-10-15-demo-day/demo.sh report hand100'''),
('Home Pi / generic exported immutable take', '''# Prepared built engine/settings; owner ORB authorization required.
export ORB_DIR="$HOME/orbslam3/ORB_SLAM3"
export TAKE_DIR="$HOME/wbr-data/derived/V1-native-euroc"
export SETTINGS_FILE="$HOME/wbr-data/reviewed-settings.yaml"
export LD_LIBRARY_PATH="$ORB_DIR/lib:$ORB_DIR/Thirdparty/DBoW2/lib"
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$ORB_DIR/Thirdparty/g2o/lib"
"$ORB_DIR/Examples/Stereo-Inertial/stereo_inertial_euroc" \\
  "$ORB_DIR/Vocabulary/ORBvoc.txt" "$SETTINGS_FILE" \\
  "$TAKE_DIR" "$TAKE_DIR/times_ns.txt"
# Run in a fresh directory; archive exact binary/library hashes.
# Required V route take may still be absent: keep replay OPEN.''')], 'demo.sh, remote.sh, summary.py exact subcommands; latest lab runbook steps 6–7.',extra=['No hand100 is newly recorded by this two-session plan unless added as an explicitly separately named optional V motion slot; otherwise the wrapper branch stays skipped. For native calibration/route data, an already-built stereo_inertial_euroc can consume H1 export with verified settings and times_ns; do not use librealsense --bag route. fetch excludes .db3 and euroc-export, so it is not a complete raw-data backup. Take name and file locations are fixed by remote.sh. Later lab reports still-15s exit0, no map, not a hand-motion result.'])
step('H7','Home: trajectory evaluation only with a reference','Compute declared alignment/association metrics, not attractive plots alone.','Actual estimate and independent reference describe the same physical origin/frame relation, units and epoch.','JSON association, SE(3) ATE, declared 1 s RPE and plots; failures retained.','Observable: correct frames/clocks, finite associated data, reported coverage/exclusions. No GT means no ATE/RPE.','Inspect units/order/pose direction/extrinsics→epoch→association→alignment; do not fit scale to hide stereo error.','DERIVED/traj-eval, with input hashes and saved assumptions.',[
('Mac / replace only verified input paths', '''python3 tools/trajectory_eval/traj_eval.py single \\
  --est "$DERIVED/CameraTrajectory.txt" \\
  --ref "$HOME/Desktop/Research/wbr-data/reference.csv" \\
  --est-format orbslam3 --ref-format euroc_gt \\
  --clock-assumption 'Verified common sensor epoch; zero offset' \\
  --est-frame 'imu_camera' --ref-frame 'imu_camera' \\
  --t-max-diff 0.02 --align se3 \\
  --rpe-delta 1 --rpe-unit s --out "$DERIVED/traj-eval"
# Input declarations above must be established, not assumed true.
# No independent room reference: skip, report closure/scale proxies.''')], 'tools/trajectory_eval/traj_eval.py CLI and README.md. Only use frame/clock declarations supported by the actual dataset.',extra=['This command is a source-verified template, not a claim that those input files exist. MH01 reference is dataset IMU/body, not D435i imu_camera: use the actual EuRoC body labels and conventions when reproducing MH01, and verify output pose origin. Current new-room ATE is UNKNOWN. --est-format orbslam3 defaults to ns; euroc_gt is ns and quaternion qw-first, converted internally. RPE uses first eligible endpoint without interpolation; association can reuse samples.'])
intro('Home ablation: preserve every controlled variable',['V1–V3 are separate textured-room 90 s route takes, not target-only C takes.','Pair factory vs selected spatial/time settings with raw vs x10 noise on identical inputs.','Three replays per cell; record initialization, maps/resets, tracking loss and route proxies.'],'Select on development takes, verify on held-out V; keep ties and failures.','ASSUMED calibration-plan protocol',note='Full V1–V3 acquisition/2×2 ablation is future work if no route take exists; it is not hidden within the two-session timeline. Runtime time-shift hook remains unverified; do not invent an ORB flag. Closure ≤2% of measured ≥5m route and straight segment error ≤2% are ASSUMED; report pre-loop closure when accessible. Three replays per cell×three takes is home analysis, not lab time.')
# BACKUPS / printable checklists.
current_part='backup'
intro('Backup: printable Session 1 checklist',['□ P0/S1.0–2: ready paths; manifest; flags 0x0; camera branch ≥5000M; serial.','□ S1.3–4: 20/105/300 s + actual review; N3 record/replay or explicit blocker.','□ S1.5–8: ROS S/C1/C2/C3 + metadata; A pilot; native branches only if companion ready.','□ S1.9–10: camera off, correct bench firmware, link results; hashes/handoff; 150 min.'],'Stop on power/USB/order faults. One new-ID retry; no gate PASS without evidence.','ASSUMED printable one-page field checklist',note='Print this PDF page fit to A4 landscape. Full commands and the seven-field step cards are in LAB_PLAN.md. This checklist is a one-page backup, not a replacement for acceptance review.')
intro('Backup: printable Session 2 checklist',['□ S2.0: handoff read, fresh power/identity/N1 as needed; retries stop at minute 30.','□ S2.1: 8 GB server / 4 GB client; E6 exact service/transport, outcomes and both logs.','□ S2.2–5: E7 image ready; real UART FRESH; result loss vs HB loss; latch/reset contract.','□ S2.6: qdisc cleared, both-node/MCU traces hashed, unresolved work OPEN; 150 min.'],'No FRESH or no verified firmware/producer means skip the fault demo and retain BLOCKED.','ASSUMED printable one-page field checklist',note='CN/OS integration frames do not establish WBR safety. Print A4 landscape. Preserve real-UART untested status unless actual evidence is collected and reviewed.')
table('Backup: what the two-session plan cannot promise',['Gap','Required before acceptance'],[['N3 card receipt policy','Reviewed runner/receipt compatible with approved 128 GB exception.'],['Native / ROS companions','Validated source-preserving playback; CSV adapters absent.'],['Primary ROS → analysis','Reviewed wrapper-bag→Kalibr / raw Allan extraction.'],['Real CN/OS demo','Built v3 board image, result IPC producer and UART qualification.']],'These are source/tooling gaps, not commands to improvise at the bench.','OPEN / UNVERIFIED',widths=[72,108])
table('Sources and reading order',['Local source','Use'],[['base/main-v4-91p.tex → base/main.tex','Lecture flow → Phase-8 factual precedence.'],['sources/LAB_DAY…4b63.md + STM32_LINK…','Latest lab scripts, native diagnostics, link bench.'],['docs/D435I_CALIBRATION_PLAN.md','Current storage/target/timing/noise review protocol.'],['CN hw/e7 + OS-wt-cn CN_INTEGRATION','E6/E7 interfaces; v3 supervisor behavior.']],'Full paths, hashes and material conflicts are in qa/SOURCES.md and README.','SOURCE-SUPPORTED provenance',widths=[92,88])
# Stable references target retained from the base preamble if used later.
add('Review standard: explain the complete evidence chain',r'\hypertarget{referencepage}{}'+r'\deckitems{\item '+e('What is known, measured, assumed and still OPEN?')+r'\item '+e('Which frame and clock does each quantity belong to?')+r'\item '+e('What exact observation rejects this take or triggers fallback?')+r'\item '+e('Where are the immutable raw data, hashes, config and failure logs?')+r'}\vfill\takeaway{'+e('A complete build can pass document QA while every hardware gate remains OPEN.')+'}','KNOWN method','Answers must identify source provenance, original timestamps, named input/output frames, explicit criteria and preserved failures. Builder performed only offline document work.')

# Generate with the identical inherited preamble; only document metadata and total footer differ.
base=(ROOT/'base/main.tex').read_text()
preamble=base.split(r'\begin{document}',1)[0]
preamble=preamble.replace(r'\insertframenumber/78',r'\insertframenumber/'+str(len(frames)))
preamble=preamble.replace(r'\date{14 October 2026}',r'\date{18 October 2026}')
preamble=preamble.replace(r'\subtitle{Understanding the system and its current evidence}',r'\subtitle{Lecture and two scripted lab sessions}')
preamble+='\n'+r'''\usepackage{listings}
\lstset{basicstyle=\ttfamily\normalsize,columns=fullflexible,
  keepspaces=true,showstringspaces=false,breaklines=false,
  aboveskip=2mm,belowskip=2mm,frame=none,tabsize=2}
'''
(ROOT/'main.tex').write_text(preamble+'\n'+r'\begin{document}\raggedright'+'\n'+''.join(frames)+r'\end{document}'+'\n')
(ROOT/'qa/pages.json').write_text(json.dumps(inventory,indent=2)+'\n')
(ROOT/'qa/parts.json').write_text(json.dumps({part:sum(v['part']==part for v in inventory) for part in ['lecture','lab','home','backup']},indent=2)+'\n')
(ROOT/'qa/steps.json').write_text(json.dumps(steps,indent=2)+'\n')
# Plain Markdown shares every command byte with its slide record.
md=['# WBR two-session lab plan','', 'Status: OPEN. English study/runbook; document QA is not hardware qualification. All commands below are instructions for future operator execution; the deck builder ran none of them.', '',
'Both supervised lab visits are capped at 150 minutes. Record in the lab, analyze at home. The stationary ≥4 h provisional / preferred 15–24 h Allan run and 30 min warm-up are separate at-home elapsed time between visits. If home hardware access is unavailable, Allan stays OPEN. Dates in run IDs are examples; use one new ID per actual attempt.', '',
'Every primary S/C/A sensor take is a ROS 2 sqlite3 bag with explicit topics. Optional native S/C replicas have distinct IDs and require a validated derived ROS companion before scheduling. Native N2/vendor CSV and native Allan CSV currently lack a verified ROS companion interface. The missing conversion paths are marked UNVERIFIED, not silently waived. Do not run native SDK and ROS wrapper camera owners concurrently.', '',
'**Preparation blockers:** complete pre-lab authorized deployments, correct firmware and builds, qualified data storage, installed ROS wrapper/CLI, source-clock metadata, full-window conversions and CN/OS result IPC producer. An absent prerequisite stops that branch; there is no instruction to fabricate a receipt or invent a program. Source runbook requires owner `transfer` before deployment/card/write-test work; none is executed by this document build. No card clone belongs in these sessions.', '',
'**Terminals and variables:** Mac commands start from `~/Desktop/Research/wbr-perception-phase1-runtime` unless stated. Pi P0 creates explicit `GATE`, `RUN`, `DATA`; repeat bindings in each terminal. `STUDY=~/wbr-runtime/study-docs` is a pre-lab copy of this document package. On both CN Pis `~/CN` is the prepared CN checkout. `NATIVE` is an actual finalized copied `take/`; `DERIVED` is a fresh output parent; `TARGET` is the actual measured target. Paths are named deployment choices, not assertions they exist.', '',
'**Same-clock rule:** keep original SDK timestamps/domain, ROS header, recorder time, host arrival, processing boundaries and MCU events distinct. No unsynchronized cross-host subtraction. Stable power, fresh unit identity, N1→N2→N3 precede qualified calibration. Diagnostic capture under unresolved prerequisites stays OPEN.', '']
for kind, item in lab_order:
    if kind == 'intro':
        md += ['## '+item['title'],'','**Evidence:** '+item['label'],'']+['- '+b for b in item['bullets']]+['',item['takeaway'],'']
    elif kind == 'table':
        md += ['## '+item['title'],'','**Evidence:** '+item['label'],'','| '+' | '.join(item['heads'])+' |','|'+'|'.join('---' for _ in item['heads'])+'|']
        md += ['| '+' | '.join(str(v).replace('|',' / ') for v in row)+' |' for row in item['rows']]
        md += ['',item['takeaway'],'']
    elif kind == 'map':
        md += ['## '+item['title'],'','```mermaid','flowchart LR']
        for i,label in enumerate(item['labels']):
            md += [f'  S{i}["{label}"]']
        md += ['  S0 -->|YES| S1 -->|YES| S2 -->|YES| S3','  S0 -->|NO| F["Correct once or mark BLOCKED; preserve evidence"]','  S1 -->|NO| F','  S2 -->|NO| F','```','',item['branch'],'']
    else:
        st=item
        md+=['## '+st['id']+' — '+st['title'],'','**Evidence:** '+st['label'], '', '**Goal / why:** '+st['goal'],'','**Hardware / preconditions:** '+st['setup'],'','**Expected output:** '+st['expected'],'','**PASS / FAIL:** '+st['criterion'],'','**If FAIL:** '+st['fail'],'','**Files / destinations:** '+st['files'],'']
        for terminal,cmd in st['blocks']:
            md+=['**'+terminal+'**','', '```bash',cmd.rstrip(),'```','']
        md+=['**Source:** '+st['source'],'']
        if st['extra']:md+=['**Operator detail / limitations:** '+ ' '.join(st['extra']), '']
(ROOT/'LAB_PLAN.md').write_text('\n'.join(md)+'\n')
print(f'Generated {len(frames)} pages; {len(steps)} synchronized step records.')
