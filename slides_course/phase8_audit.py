"""Phase-8 document curation from the preserved Phase-7 deck; no runtime actions."""
from pathlib import Path
import re, json, hashlib
ROOT=Path(__file__).resolve().parent
BASE=ROOT/'qa/main-v4-91p.tex'
F14='experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md'
F13='experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md'
PLAN='experiments/2026-10-13-n4b-d435i-prep/n4b_plan.md'
CAL='experiments/2026-10-13-n4b-d435i-prep/calibration_notes.md'
REPORT='experiments/2026-10-13-n4a-euroc-mh01/REPORT.md'
AUDIT='experiments/2026-10-14-deck-audit/AUDIT.md'

def escape(s):
    return s.replace('_',r'\_').replace('%',r'\%')

def argument(s,start):
    """Return a balanced TeX brace argument, including nested commands."""
    assert s[start]=='{'
    depth=1;i=start+1
    while depth:
        if s[i]=='{' and s[i-1]!='\\': depth+=1
        if s[i]=='}' and s[i-1]!='\\': depth-=1
        i+=1
    return s[start+1:i-1],i

def separate_notes(s):
    notes=[]
    while (i:=s.find(r'\note{'))>=0:
        note,end=argument(s,i+5);notes.append(note);s=s[:i]+s[end:]
    return s,notes

def title(s):
    m=re.search(r'\\begin\{frame\}(?:\[[^]]*\])?\{([^}]+)\}',s)
    return m[1] if m else 'WBR Perception Implementation'

# Drawings keep the inherited palette and fonts. Coordinates are centimetres.
def tikz(s):
    return r'\begin{tikzpicture}[font=\small,box/.append style={font=\small},>=Stealth]'+s+r'\end{tikzpicture}'

def flow(labels,vertical=False):
    s=''
    for i,label in enumerate(labels):
        x,y=(0,-i*1.35) if vertical else (i*4.65,0)
        s+=rf'\node[box,text width=38mm,minimum height=12mm] (n{i}) at ({x},{y}) {{{label}}};'
        if i:
            s+=rf'\draw[flow] (n{i-1}.south)--(n{i}.north);' if vertical else rf'\draw[flow] (n{i-1}.east)--(n{i}.west);'
    return tikz(s)

def two_routes(top,bottom,toplabel='',bottomlabel=''):
    s=''
    for row,labels in enumerate([top,bottom]):
        for i,label in enumerate(labels):
            s+=rf'\node[box,text width=35mm,minimum height=13mm] (r{row}n{i}) at ({i*4.4},{-row*2.1}) {{{label}}};'
            if i:s+=rf'\draw[flow] (r{row}n{i-1}.east)--(r{row}n{i}.west);'
    s+=rf'\node[anchor=west,text=teal!70!black] at (-1.8,1) {{{toplabel}}};\node[anchor=west,text=muted] at (-1.8,-1.1) {{{bottomlabel}}};'
    return tikz(s)

SPECS=[]
def frame(old,name,text,diagram,caption,take,source='',status='KNOWN method',wide=False,key=None):
    key=key or 'E'+str(old)
    # Visual-review fixes remain in the authoring module, not the generated TeX.
    if old==13:
        diagram=diagram.replace(r'node[lbl,right,text width=33mm]{Optional reference; integration planned}',r'node[lbl]{Optional reference}')
    if old==14:
        text=text.replace('The 64 GB USB stick cannot sustain this recording load.','The 64 GB Universal Serial Bus (USB) stick cannot sustain recording.')
    if old==15:
        text=text.replace('Current diagnostic programs read the camera through librealsense directly.','Programs use the librealsense software development kit (SDK) directly.')
    if old==19:
        wide=True
    if old=='M1':
        wide=True
        diagram=tikz(r'\foreach \x/\lab in {0/Left at $t_0$,5/Right at $t_0$,10/Left at $t_1$}{\draw[navy](\x,0)rectangle(\x+3,2.2);\node at(\x+1.5,2.6){\lab};}\foreach \x/\y in {.6/.5,1.1/1.5,2.3/.8}{\fill[teal](\x,\y)circle(3pt);\fill[teal](\x+4.8,\y)circle(3pt);\fill[teal](\x+10.2,\y+.2)circle(3pt);\draw[flow,dashed](\x,\y)--(\x+4.8,\y);\draw[flow,dashed](\x+4.8,\y)--(\x+10.2,\y+.2);}\node at(4,-.6){Stereo matches constrain depth};\node at(10,-.6){Later matches constrain motion};')
    if old==32:
        diagram=diagram.replace(r'\draw[flow](t.north east)--node[lbl,above]{Keyframes}(m.west);',r'\draw[flow](t.north east)--(m.west);\node[lbl] at(1.5,1.5){Keyframes};')
        diagram=diagram.replace(r'\node[lbl]at(5,-1.4)',r'\node[lbl]at(5,-2.0)')
    if old==30:
        diagram=tikz(r'\foreach \x/\lab/\purpose in {0/Target motion/Geometry and timing,5/Room motion/Initialization and tracking,10/Stationary IMU/Noise statistics}{\node[box,text width=40mm,minimum height=17mm]at(\x,0){\lab};\node[text width=40mm,align=center]at(\x,-1.4){\purpose};}')
    if old==24:
        diagram=tikz(r'\draw[flow](0,1.5)--(8,1.5);\draw[flow](0,-.6)--(8,-.6);\node[anchor=west]at(0,2.2){Device clock: capture stamps};\node[anchor=west]at(0,-1.25){Host: arrival, start, end, output};\fill[teal](1,1.5)circle(3pt);\fill[navy](4,-.6)circle(3pt);\node[box,text width=43mm](m)at(4,.5){Clock relation required};\draw[flow,dashed](1,1.5)--(m.north west);\draw[flow,dashed](m.south)--(4,-.6);\node[text width=77mm,align=center]at(4,-2.3){Mapping uncertainty limits source-age accuracy.};')
    if old==17:
        wide=True
        diagram=tikz(r'\node[box,text width=22mm](s)at(0,0){Sensor};\foreach \x/\lab in {3/Newest,5.5/Older,8/Oldest}{\node[box,fill=navy!6,text width=20mm,minimum height=17mm]at(\x,0){\lab};}\node[box,text width=25mm](c)at(11.5,0){Slow writer};\draw[flow](s.east)--(1.9,0);\draw[flow](9.1,0)--(c.west);\node at(5.8,-1.2){Oldest leaves first; sustained arrival exceeds consumption.};')
    if old==40:
        diagram=diagram.replace(r'\draw[flow](f.east)--node[lbl,above]{Age or state fails}(h.west);',r'\draw[flow](f.east)--(h.west);\node[lbl]at(2.35,.75){Age or state fails};')
    if old==87:
        diagram=tikz(r'\node[box,text width=36mm](a)at(0,1){Known-data ATE};\node[box,text width=36mm](r)at(0,-1){Short RAM take};\node[box,text width=45mm](e)at(6,0){Diagnostic evidence};\draw[flow](a.east)--(e.west);\draw[flow](r.east)--(e.west);\node[box,draw=fault,text width=104mm]at(3,-2.5){Power, rebuild, calibration and formal gates remain OPEN};')
    if old==80:
        wide=True
        paths=tikz(r'\node at(2.5,3){(a) Aligned paths: conceptual};\draw[navy,thick](0,0)--(0,2)--(5,2)--(5,0);\draw[teal,thick,dashed](.2,.1)--(.3,2.3)--(4.7,2.3)--(5.2,.2);\draw[faultflow](0,2)--(.3,2.3);\draw[faultflow](5,2)--(4.7,2.3);\draw[faultflow](5,0)--(5.2,.2);\node at(2.5,1){Position residuals};\node[text=navy]at(.7,-.7){Reference};\node[text=teal]at(4,-.7){Estimate};')
        diagram=r'\begin{minipage}[c]{.46\linewidth}\centering'+paths+r'\end{minipage}\hfill\begin{minipage}[c]{.48\linewidth}\centering'+diagram.replace(r'>=Stealth]',r'>=Stealth,y=.82cm]')+r'\end{minipage}'
        caption='(a) Residuals after rigid alignment; (b) measured MH01 ATE, no scale fitting.'
    if wide:
        body=text+r'\par\vfill\coursefigure{'+key+'}{'+diagram+'}{'+caption+'}'
    else:
        body=r'\begin{columns}[T,onlytextwidth]\begin{column}{.43\textwidth}'+text+r'\end{column}\begin{column}{.53\textwidth}\coursefigure{'+key+'}{'+diagram+'}{'+caption+r'}\end{column}\end{columns}'
    # One explicit figure reference in meaningful instructional prose.
    take=take+rf' (Figure~\ref{{fig:{key}}})'
    details={
        9:'New camera SDK serial 317422076650; ASIC serial 327743061057; USB descriptor serial 327743061057; firmware-update ID is a separate field, not independently established here. Firmware 5.17.3.10; BMI085. Historical SDK 243322073847 and USB descriptor 251843061466 do not transfer N1/N2/calibration receipts.',
        28:'Preserve SDK warning: IMU Calibration is not available. Intrinsics and 0.0499 m baseline are factory readback; camera-to-IMU geometry NOMINAL; numeric upstream noise ASSUMED; time offset UNKNOWN.',
        'M4':'RAM path /dev/shm had 3.9 GB capacity. smoke_ram.sh is in experiments/2026-10-13-n4b-d435i-prep/. Short test and checksum do not establish 100-second reliability or qualified persistent storage.',
        'M5':'Initial patches: C++17 and removal of -march=native; Sophus tests disabled after aarch64 array-bounds errors, with headers still used; bool increment replaced by assignment true. D435i gdb stack: main -> System::GetTimeFromIMUInit -> LocalMapping::GetCurrKFTime. Patch 4 initializes KeyFrame* mpCurrentKeyFrame = nullptr in include/LocalMapping.h. EuRoC does not call this query. Power loss interrupted rebuilding after 3 of about 27 objects. Resume command is cmake --build build -j4 in the separate Pi build copy; teaching only, not executed here.',
        80:'Paper value unverified in the audit source set; comparator omitted. Earlier Phase-7 RPE and extra Sim(3) digits are unverified under this source restriction. Original source/PDF and calculation report remain unchanged; no new evaluation was run.',
    }.get(old,'')
    notes=escape('Phase 8: '+source+'. '+AUDIT+'. All drawings conceptual unless labeled measured. No gate PASS. '+details)
    SPECS.append((old,name,r'\begin{frame}{'+name+r'}\evidence{'+status+'}'+body+r'\vfill\takeaway{'+take+r'}\note{'+notes+r'}\end{frame}'))

def bullets(*items):return r'\deckitems{'+''.join(r'\item '+x for x in items)+'}'

def main_frames(original):
    SPECS.clear()
    cover=original[0].replace('13 October 2026','14 October 2026').replace('A gate-by-gate engineering guide','Understanding the system and its current evidence')
    cover=cover.replace('Engineering and evidence snapshot','System explanation and diagnostic snapshot')
    SPECS.append((1,'WBR Perception Implementation',cover))
    frame(3,'1. Navigation and balance',bullets('A wheel-biped robot (WBR) needs scene-relative motion for navigation.','The Raspberry Pi estimates motion; STM32H7 maintains balance locally.','Perception supplies optional navigation information.'),two_routes(['Scene','Pi motion estimate'],['Body sensors','STM32H7 balance']),'Navigation and balance use separate sensing paths.','Loss of perception must leave local balance control running.','docs/ARCHITECTURE.md',wide=True,status='KNOWN ownership / integration PLANNED')
    frame(13,'2. Controller ownership',bullets('Linux runs image processing and mapping.','STM32H7 owns body estimation, balance and motor safety.','Navigation references cross only a reviewed boundary.'),tikz(r'\node[box,text width=78mm,minimum height=19mm] (p) at (0,1.2) {Pi: perception and navigation};\node[box,text width=78mm,minimum height=19mm] (s) at (0,-1.4) {STM32H7: body sensing, balance, motor safety};\draw[flow,dashed] (p.south)--node[lbl,right,text width=33mm]{Optional reference; integration planned}(s.north);'),'The controller retains local authority.','A pose is advice to navigation, never a motor-safety authority.','docs/ARCHITECTURE.md; AGENTS.md',status='KNOWN ownership / integration PLANNED')
    frame(4,'3. Pose usability',bullets('A pose is an estimated position and orientation.','Correct-looking numbers may describe old motion or the wrong frame.','Consumers need age, frame and estimator validity.'),tikz(r'\draw[flow] (-.4,0)--(8,0);\node[above] at (1,0){Capture};\node[above] at (4,0){Delayed processing};\node[above] at (7,0){Pose arrives};\fill[teal] (1,0) circle(3pt);\fill[fault] (7,0) circle(3pt);\draw[decorate,decoration={brace,mirror,amplitude=5pt}] (1,-.4)--(7,-.4) node[midway,below=7pt]{Source age, not just computation};'),'Delay can make a plausible pose unusable.','A recent heartbeat does not establish recent sensor capture.','docs/ARCHITECTURE.md',wide=True)
    frame(14,'4. Session hardware',bullets('The 8 GB Pi booted the same 32 GB micro Secure Digital (microSD) card.','It reported 7.8 GiB memory; under-voltage persisted.','The 64 GB USB stick cannot sustain this recording load.'),tikz(r'\node[box,text width=72mm] (p) at (0,1.2){Pi 5: 8 GB / same 32 GB card};\node[box,text width=72mm,draw=fault] (v) at (0,-.3){5 V / 3 A: power unresolved};\node[box,text width=72mm] (u) at (0,-1.8){USB stick: 1.09 MB/s with fsync};'),'More memory does not repair power or storage.','The ordered 5 A supply and larger card have no qualification evidence.','F14 items 1,6,7; '+F14+'; '+F13,status='MEASURED boot / final availability UNVERIFIED')
    frame(9,'5. D435i sensor inputs',bullets('Infrared (IR) left and right images provide stereo views.','The gyroscope measures angular rate; the accelerometer measures specific force.','This new camera needs its own calibration and gate evidence.'),tikz(r'\node[box,text width=28mm,minimum height=30mm] (d) at (0,0){D435i};\node[box,text width=42mm] (i) at (5,1.2){IR1 + IR2\\640$\times$480, 30 Hz};\node[box,text width=42mm] (g) at (5,-.1){Gyro: 200 Hz};\node[box,text width=42mm] (a) at (5,-1.3){Accel: 100 Hz};\draw[flow](d.east)--(i.west);\draw[flow](d.east)--(g.west);\draw[flow](d.east)--(a.west);'),'Selected development inputs; the emitter is off.','This paired 30 Hz profile does not replace N2’s IR1/15 profile.',F13+' section B,E; '+PLAN,status='MEASURED identity / diagnostic development profile')
    frame(22,'6. Independent inertial sensors',bullets('An inertial measurement unit (IMU) combines gyro and acceleration measurements.','The camera IMU supports visual-inertial estimation.','The controller body IMU supports local balance.'),two_routes(['Camera IMU','Pi perception'],['Body IMU','STM32H7 balance']),'Different mounts, clocks and calibration; separate jobs.','Sharing an IMU name does not make the measurements interchangeable.','docs/ARCHITECTURE.md',wide=True)
    frame(15,'7. Sensor-to-trajectory paths',bullets('Current diagnostic programs read the camera through librealsense directly.','One recording can be replayed repeatedly; live mode bypasses the file.','Robot Operating System 2 (ROS 2) integration is planned.'),two_routes(['D435i / SDK','Record / replay','ORB-SLAM3','Trajectory / evo'],['D435i / SDK','ROS 2 wrapper','Topics / bag','Reviewed adapter'],'Current direct software development path','Planned ROS 2 / N3 path'),'Current and planned paths are different implementation stages.','No successful D435i trajectory is established yet.',F13+' section E; '+F14+' item 5; '+PLAN,wide=True,status='BUILT direct path / ROS integration PLANNED')
    frame(10,'8. ROS 2 communication',bullets('A publisher sends typed messages on a topic; subscribers receive them.','Images, IMU samples and poses travel on separate topics.','Quality of Service (QoS) policies control delivery compatibility.'),flow(['Driver publisher','Typed sensor topics','Recorder / estimator subscriber']),'ROS 2 connects processes through a message contract.','Matching topic names alone does not establish compatible delivery.','ROS 2 Jazzy QoS [3]; docs/PERCEPTION_TOOLING_ARCHITECTURE.md',wide=True,status='KNOWN ROS concepts / integration PLANNED')
    frame(19,'9. Pose origin and axes',bullets('Simultaneous Localization and Mapping (SLAM) estimates pose while building a map.','The exported trajectory describes camera IMU/body pose in the SLAM world.','Robot-body pose also needs the mount transform.'),tikz(r'\node[box,text width=23mm] (w) at (0,0){SLAM world};\node[box,text width=23mm] (i) at (3.1,0){Camera IMU};\node[box,text width=23mm] (b) at (6.2,0){Robot body};\draw[flow](w.east)--(i.west);\draw[flow,dashed](i.east)--(b.west);\node[below,text width=75mm,align=center] at (3.1,-.8){$T_{WB}=T_{WI}T_{IB}$\\$T_{IB}$: separately defined rigid mount};'),'Compose the estimated sensor pose with a defined mount.','A camera trajectory is not automatically a robot-body trajectory.',PLAN+' success observations; docs/ARCHITECTURE.md')
    frame(6,'10. Stereo geometry',bullets('Match the same physical point in the two images.','Horizontal displacement is disparity $d$.','With focal length $f$ and baseline $b$, depth is $Z=fb/d$.'),tikz(r'\coordinate (p) at (3,3);\node[box,text width=20mm] (l) at (0,0){Left};\node[box,text width=20mm] (r) at (6,0){Right};\fill[teal](p)circle(3pt);\node[above]at(p){Fixed scene point};\draw[flow](l.north)--(p);\draw[flow](r.north)--(p);\draw[<->] (0,-.8)--node[lbl,below]{Baseline $b$}(6,-.8);\node at(3,1){Depth $Z$};'),'Two viewpoints constrain metric depth.','Bad correspondences or calibration yield bad depth.',PLAN+'; ORB-SLAM3 [1]')
    frame('M1','11. Features constrain motion',bullets('An image feature is a recognizable corner or local pattern.','Match fixed scene features across stereo views and later images.','Many consistent matches constrain camera movement.'),tikz(r'\foreach \x/\lab in {0/Time $t_0$,4.3/Time $t_1$}{\draw[navy] (\x,0)rectangle(\x+3,2.2);\node at(\x+1.5,2.6){\lab};}\foreach \x/\y in {.6/.5,1.1/1.5,2.3/.8}{\fill[teal](\x,\y)circle(3pt);\fill[teal](\x+4.5,\y+.2)circle(3pt);\draw[flow,dashed](\x,\y)--(\x+4.5,\y+.2);}\node[text width=75mm,align=center]at(3.65,-.8){A shared scene must explain the matched image locations.};'),'Correspondences link observed pixels to one motion model.','Track scene features, then test whether their geometry agrees.',PLAN+' emitter discussion; retained tracking explanation')
    frame(7,'12. Visual and inertial estimation',bullets('Visual-inertial odometry (VIO) combines both sensor cues.','IMU prediction bridges image intervals but accumulates drift.','Image constraints correct that prediction against the scene.'),tikz(r'\node[box,text width=28mm](v)at(0,1){Image constraints};\node[box,text width=28mm](i)at(0,-1){IMU prediction};\node[box,text width=33mm](p)at(5,0){Joint motion estimate};\draw[flow](v.east)--(p.west);\draw[flow](i.east)--(p.west);'),'Two complementary cues constrain the same motion.','Calibration and timing must connect both measurements correctly.',PLAN+'; ORB-SLAM3 [1]')
    frame('M2','13. Motion between images',bullets('Gyro and accel samples arrive between successive stereo pairs.','The helper interpolates accel only within valid gyro-time brackets.','Preintegration summarizes interval motion before visual correction.'),tikz(r'\draw[flow](0,0)--(15,0);\foreach \x/\lab in {1/Image $k$,13/Image $k+1$}{\draw[navy,thick](\x,-.3)--(\x,.5);\node[above]at(\x,.6){\lab};}\foreach \x in {2,3,4,5,6,7,8,9,10,11,12}{\fill[teal](\x,0)circle(2pt);}\foreach \x in {2,4,6,8,10,12}{\draw[navy,fill=paper](\x,-.7)circle(2pt);}\node[anchor=west]at(1,-1.3){Top: gyro grid; lower: raw accel brackets.};\draw[decorate,decoration={brace,amplitude=5pt}](2,1.3)--(12,1.3)node[midway,above=7pt]{Interval prediction $\rightarrow$ image correction};'),'Interpolation aligns samples; it creates no new sensor information.','Reject missing coverage and invalid time steps rather than extrapolating.',F13+' section E; '+PLAN,wide=True,status='PREPARED helper / full runtime association UNVERIFIED')
    frame(33,'14. Tracking',bullets('Extract and match features from each stereo pair.','Use the inertial prediction to guide pose estimation.','Check consistency; update tracking state and select keyframes.'),flow(['Stereo pair + IMU','Feature correspondences','Pose + tracking state']),'Tracking estimates the current sensor pose.','Tracking state is part of the output’s meaning.','ORB-SLAM3 [1]; retained tracking frame',wide=True)
    frame(34,'15. Keyframes and Atlas',bullets('A keyframe preserves a useful viewpoint instead of every image.','Mapping refines keyframe poses and persistent scene points.','Atlas holds multiple maps; a new map is not seamless tracking.'),tikz(r'\foreach \x/\y/\id in {0/0/A,3/1/B,6/0/C}{\node[box,text width=12mm](\id)at(\x,\y){\id};}\foreach \x/\y in {1/2,3/2.8,5/2}{\fill[teal](\x,\y)circle(3pt);\draw[navy!45](A.north)--(\x,\y);\draw[navy!45](B.north)--(\x,\y);\draw[navy!45](C.north)--(\x,\y);}\node at(3,-1){Keyframes A--C observe shared map points.};'),'Selected views preserve geometric constraints.','Inspect resets and map identity as well as trajectory files.','ORB-SLAM3 [1]')
    frame(32,'16. Algorithm work sharing',bullets('Tracking handles each incoming image and predicts current pose.','Local mapping refines nearby keyframes and scene structure.','Loop closing recognizes revisits and corrects map drift.'),tikz(r'\node[box,text width=38mm](t)at(0,0){Tracking\\caller thread};\node[box,text width=38mm](m)at(5,1.4){Local mapping\\background worker};\node[box,text width=38mm](l)at(10,0){Loop closing\\background worker};\draw[flow](t.north east)--node[lbl,above]{Keyframes}(m.west);\draw[flow](m.east)--(l.north west);\draw[flow,dashed](l.south)--(5,-1.4)--(t.south);\node[lbl]at(5,-1.4){Map corrections return to tracking};'),'Roles cooperate asynchronously; queueing and scheduling matter.','Offline playback does not eliminate multithreaded run variation.','ORB-SLAM3 [1]',wide=True)
    frame(8,'17. Drift and revisits',bullets('Odometry accumulates local motion errors along a path.','Loop closure recognizes a previously observed place.','A map correction can change the global trajectory.'),tikz(r'\draw[teal,thick,rounded corners] (0,0)--(0,2)--(5,2)--(5,0)--(0,0);\draw[fault,thick,dashed,rounded corners] (0,0)--(.4,2.3)--(5.5,2.7)--(6,.3)--(1.3,-.4);\draw[flow](1.3,-.4)--(0,0);\node[text=teal]at(2.5,1){Corrected map};\node[text=fault]at(3,-1){Accumulated local drift};'),'Conceptual paths, not measured trajectories.','Local continuity and global map correction need different frame semantics.','ROS REP-105 [4]; ORB-SLAM3 [1]')
    frame(35,'18. Inertial initialization motion',bullets('Initialization estimates gravity, velocity and inertial biases.','Translate in several directions and rotate the camera.','Then move through a small loop and finish briefly still.'),flow(['Translation + rotation','Small room loop','Still ending']),'Diagnostic motion gives the estimator useful excitation.','Look for IMU initialization; a launch alone is not success.',F13+' section E; '+PLAN+' success observations',wide=True,status='PLANNED diagnostic recipe / not target calibration')
    frame('M3','19. Infrared projector',bullets('Tracking needs features belonging to the fixed scene.','Projected dots depend on the moving camera projector.','This development path disables the emitter and uses scene texture.'),tikz(r'\node[box,text width=22mm](c)at(0,0){Camera + projector};\draw[navy,thick](6,-1)--(6,2);\node[above]at(6,2){Wall};\draw[fault,dashed](c.east)--(6,.2);\draw[fault,dashed](c.east)--(6,1.2);\fill[teal](6,1.7)circle(3pt);\node[anchor=east,text=teal]at(5.8,1.7){Fixed corner};\node[text=fault,text width=60mm,align=center]at(3,-1.6){Projected pattern changes with projector viewpoint.};'),'Scene geometry and projected texture are different cues.','Emitter off is a runtime choice; it is not calibration.',F13+' section E; '+PLAN+' emitter discussion',status='DEVELOPMENT profile: emitter OFF')
    frame(28,'20. Calibration questions',bullets('Image intrinsics describe projection; stereo extrinsics relate the cameras.','Camera--IMU geometry is factory nominal; physical alignment is unverified.','Noise is assumed and time offset remains unknown.'),tikz(r'\node[box,text width=72mm]at(0,1.8){Image projection: factory readback};\node[box,text width=72mm]at(0,.4){Sensor geometry: NOMINAL};\node[box,text width=72mm]at(0,-1){IMU noise: ASSUMED};\node[box,text width=72mm,draw=fault]at(0,-2.4){Time offset / alignment: UNVERIFIED};'),'Four calibration questions need separate evidence.','A runnable settings file does not establish calibrated VIO.',F13+' section E; '+CAL,status='Calibration unverified')
    frame(29,'21. Stereo rectification',bullets('Rectification places corresponding points along the same row.','A wrong image model leaves vertical mismatch or distorted geometry.','Validate paired pixels before tuning the estimator.'),tikz(r'\foreach \x/\lab in {0/Left rectified,4.4/Right rectified}{\draw[navy](\x,0)rectangle(\x+3,2.5);\node[above]at(\x+1.5,2.6){\lab};\draw[teal,dashed](\x,1.3)--(\x+3,1.3);}\fill[teal](1,1.3)circle(3pt);\fill[teal](6.2,1.3)circle(3pt);\fill[fault](6.2,1.9)circle(3pt);\draw[fault,<->](6.6,1.3)--(6.6,1.9);\node[text=fault]at(3.7,-.8){Vertical mismatch indicates a geometry problem.};'),'Correct matches share an epipolar row.','Matched rates do not establish matched image geometry.',CAL+'; ORB-SLAM3 [1]')
    frame(30,'22. Three different capture motions',bullets('Target calibration estimates geometry and camera--IMU timing.','Room motion tests diagnostic initialization and tracking.','A stationary noise recording supports Allan analysis.'),flow(['Known target motion','Room translation / loop','Long stationary IMU']),'Different captures answer different engineering questions.','A successful hand-motion demo does not replace calibration.',CAL+'; '+PLAN,wide=True,status='PLANNED qualification / diagnostic recipe available')
    frame(24,'23. Timestamp clock domains',bullets('Sensor stamps describe capture in a device clock.','Host receipt and processing times use a host clock.','Shared units do not establish shared epochs or drift.'),tikz(r'\draw[flow](0,1.5)--(8,1.5);\draw[flow](0,-.6)--(8,-.6);\node[anchor=west]at(0,2.2){Device clock: capture stamps};\node[anchor=west]at(0,.1){Host clock: arrival, start, end, output};\fill[teal](1,1.5)circle(3pt);\fill[navy](4,-.6)circle(3pt);\draw[dashed,navy](1,1.5)--(4,-.6);\node[text width=77mm,align=center]at(4,-1.5){Mapping and uncertainty are needed to estimate source age.};'),'Transport links events, not automatically their clock origins.','Never subtract device capture from host output without a defined relation.','docs/PERCEPTION_TOOLING_ARCHITECTURE.md; SDK [5]')
    frame(17,'24. Queues and backpressure',bullets('A slow consumer lets old samples accumulate in a queue.','Blocking may reach acquisition and cause recording gaps.','Bound queues and make overflow or rejection visible.'),tikz(r'\node[box,text width=18mm](s)at(0,0){Sensor};\foreach \x/\lab in {2/Newest,3.3/Older,4.6/Oldest}{\draw[navy,fill=navy!6](\x-.5,-.5)rectangle(\x+.5,.5);\node[rotate=90]at(\x,0){\lab};}\node[box,text width=20mm](c)at(7,0){Slow writer};\draw[flow](s.east)--(1.5,0);\draw[flow](5.1,0)--(c.west);\node[text width=78mm,align=center]at(3.7,-1.5){Oldest leaves first; sustained arrival exceeds consumption.};'),'Queue direction follows arrival order and dequeue order.','Low compute time can coexist with high source age.',PLAN+' input queues; docs/PERCEPTION_TOOLING_ARCHITECTURE.md')
    frame(18,'25. Recording gaps on the card',bullets('The 100 s hand-moved take had 0.3--2.9 s gaps after 22 s.','Observed file growth was 16.6 MB/s against an 18.4 MB/s input budget.','Writer stalls blocking acquisition are strongly inferred.'),flow(['Camera delivery','Card writes stall','Recording has gaps']),'Observed gaps; storage bottleneck is an inferred cause.','No USB/power kernel error during this take does not resolve general power.',F14+' item 3',wide=True,status='MEASURED gaps / cause INFERRED')
    frame('M4','26. Record in RAM, copy later',bullets('Random-access memory (RAM) avoids card writes during capture.','The 15 s test: IR 29.99 Hz, maximum gap 33 ms, zero observed drops.','Gyro 200.2 Hz; accel 101 Hz. The later copy passed checksum.'),flow(['Capture into RAM','Stop and finalize','Copy + checksum']),'Short RAM test separated capture from slow persistent writes.','3.9 GB RAM filesystem fits an estimated 1.7 GB take; long reliability is unverified.',F14+' item 4',wide=True,status='MEASURED 15 s diagnostic / long take PLANNED')
    frame(59,'27. Camera-independent baseline',bullets('EuRoC MH01 is a public drone dataset with stereo and IMU measurements.','Ground truth (GT) is independently measured motion used as the reference answer.','The Pi completed three trials with one map, no resets and IMU initialization.'),two_routes(['EuRoC stereo + IMU','Pi ORB-SLAM3','Estimated trajectory'],['Reference motion','Ground-truth trajectory','Aligned comparison']),'Known input separates algorithm/build issues from camera adaptation.','These completed trials do not establish D435i accuracy or real-time speed.',F13+' section D; '+REPORT+'; EuRoC [2]',wide=True,status='MEASURED historical 4 GB baseline / N4A OPEN')
    frame(80,'28. Baseline trajectory error',bullets('Absolute Trajectory Error (ATE) is position mismatch after aligning the paths.','Use one rotation and translation, with no scale fitting (SE(3)).','Root mean square error (RMSE) summarizes the position residuals.'),tikz(r'\draw[flow](0,0)--(7,0);\draw[flow](0,0)--(0,3.7);\foreach \y/\lab in {0/0,1.5/0.02,3/0.04}{\draw(0,\y)--(-.1,\y);\node[anchor=east]at(-.2,\y){\lab};}\foreach \x/\y/\v/\r in {1.2/3.1125/0.0415/1,3.5/2.76/0.0368/2,5.8/3.12/0.0416/3}{\fill[teal](\x,\y)circle(3pt);\node[above=2mm]at(\x,\y){\v};\node[below]at(\x,0){Run \r};}\node[anchor=west]at(0,4.1){ATE RMSE (m)};\node at(3.5,-1.1){Three-run mean: 0.040 m};'),'Measured MH01 rigid-alignment position error.','About four centimetres on MH01; D435i accuracy remains UNKNOWN.',REPORT+'; '+F13+' section D; audit: omit unverified paper comparator and RPE',status='MEASURED ATE / N4A qualification OPEN')
    frame('M5','29. Baseline success and camera crash',bullets('Three initial compatibility patches enabled the native build and EuRoC trials.','Offline D435i replay crashed before the first keyframe.','Patch 4 initializes the keyframe pointer; rebuilding was interrupted by power loss.'),two_routes(['EuRoC example','Three-patch build','Completed baseline'],['D435i example','Different time query','Crash / patch 4 pending']),'The two examples exercise different code paths.','A source repair is not a verified executable until rebuilding succeeds.',F13+' section C; '+F14+' item 5',wide=True,status='MEASURED crash / rebuild INCOMPLETE')
    frame(61,'30. Repeatable offline diagnosis',bullets('The recorder preserves camera samples and timestamps in one file.','Replay runs the same input without a live acquisition deadline.','The first offline smoke test crashed; no camera trajectory succeeded.'),flow(['Immutable recording','Offline patched example','Logs + trajectory check']),'Repeated input isolates estimator changes from acquisition changes.','Resume and verify patch-4 rebuilding before another diagnostic run.',PLAN+'; '+F14+' items 2--5',wide=True,status='MEASURED recording / successful N4B UNVERIFIED')
    frame(64,'31. Live freshness',bullets('Live estimation must consume new data as it arrives.','Queue growth can make an otherwise accurate pose stale.','No successful live estimator run is documented; rebuild is incomplete.'),tikz(r'\draw[flow](0,0)--(8,0);\foreach \x in {0,1.3,2.6,3.9,5.2,6.5}{\draw[teal,thick](\x,.1)--(\x,.7);}\draw[fault,thick](0,-.7)--(7,-.7);\node[anchor=west]at(0,1.3){Input: regular image cadence};\node[anchor=west,text=fault]at(0,-1.4){Consumer: work can exceed the interval};'),'A conceptual overload timeline; no latency measurement.','Measure age, queueing and drops after offline diagnosis succeeds.',F14+' item 5; '+PLAN,status='PLANNED live diagnostic / N4C OPEN')
    frame(73,'32. Bottom-up diagnosis',bullets('Identify the earliest failed layer before tuning later layers.','A recording gap starts with delivery/storage checks.','A first-frame crash starts with its stack trace and build identity.'),flow(['Hardware / USB','Input / storage','Clocks / calibration','Estimator / evaluation']),'Earlier failures invalidate conclusions from later layers.','Preserve raw warnings and failed runs while isolating the cause.',F14+' items 3--5; docs/PERCEPTION_TOOLING_ARCHITECTURE.md',wide=True)
    frame(40,'33. Health supervision',bullets('A heartbeat says a process is alive, not that its pose is fresh.','A planned receiver checks source age, validity and session identity.','Stale or invalid perception withdraws optional navigation input.'),tikz(r'\node[box,text width=26mm](f)at(0,0){Fresh + valid};\node[box,text width=26mm,draw=fault](h)at(4.7,0){Stale / invalid};\draw[flow](f.east)--node[lbl,above]{Age or state fails}(h.west);\node[box,text width=72mm](s)at(2.35,-2){STM32H7 local balance continues};\draw[flow,dashed](f.south)--(s.north west);\draw[faultflow,dashed](h.south)--(s.north east);'),'Navigation validity is supervised separately from balance.','Rates, age budgets and message design still require review.','docs/ARCHITECTURE.md',status='Integration PLANNED / no physical safety verdict')
    frame(42,'34. Different evidence branches',r'N4A tests known data; camera qualification follows N0 $\rightarrow$ N1 $\rightarrow$ N2 $\rightarrow$ N3. No gate has PASSED.\par\medskip Exact N2 raw profile: IR1 Y8 640$\times$480/15, gyro/200, accel/100.',tikz(r'\node[box,text width=20mm](n0)at(0,0){N0\\platform};\node[box,text width=26mm](a)at(4.3,1.5){N4A\\EuRoC / OPEN};\node[box,text width=26mm](n1)at(4.3,-1.2){N1\\USB $\geq$5000M};\node[box,text width=26mm](n2)at(8.6,-1.2){N2\\300 s soak};\node[box,text width=26mm](n3)at(12.9,-1.2){N3\\ROS + replay};\draw[flow](n0.north east)--(a.west);\draw[flow](n0.south east)--(n1.west);\draw[flow](n1.east)--(n2.west);\draw[flow](n2.east)--(n3.west);\node[anchor=west,text=muted]at(3,.3){All camera gates remain OPEN};'),'Dataset results do not qualify new-camera transport or timing.','The 15 s RAM test cannot replace the mandatory 300-second N2 soak.',F14+'; '+PLAN+' exact N2 requirements',wide=True,status='MEASURED diagnostics / all gates OPEN')
    frame(87,'35. Established work and open gaps',bullets('Established: 8 GB boot, EuRoC trials and short RAM recording.','Open: power, long capture, patch-4 rebuild and calibrated camera tracking.','Later Wi-Fi reachability failed; final operating state is unverified.'),two_routes(['Known-data ATE','Short RAM take','Diagnostic evidence'],['Power + rebuild','Calibration + gates','Qualification still OPEN']),'Useful observations coexist with unresolved qualification.','Neither larger RAM nor a clean short take establishes robot readiness.',F14+' items 1--7; '+REPORT,wide=True,status='MEASURED progress / power UNRESOLVED')
    frame(89,'36. Next diagnostic sequence',r'After explicit CAMERA AVAILABLE authorization, the addendum proposes this diagnostic sequence. It does not bypass formal N1 $\rightarrow$ N2 $\rightarrow$ N3 qualification.',flow(['Resume patch-4 build','100 s take into RAM','Offline replay + plot','Then live diagnostic']),'Proposed sequence, not executed in deck authoring.','Stable power and calibration remain prerequisites to qualification.',F14+' tomorrow plan; '+PLAN,wide=True,status='PLANNED / diagnostic only')
    frame(90,'37. Current system claim',bullets('The Pi build estimated motion on known EuRoC input with about 4 cm ATE.','Camera recording improved in a short RAM test; camera estimation remains unverified.','STM32H7 retains local balance and motor-safety ownership.'),two_routes(['Known-data estimation','Measured baseline'],['Camera / robot readiness','Open qualification']),'Progress and readiness answer different questions.','Resume the repair and diagnostic sequence while keeping every gate OPEN.',F14+'; '+REPORT+'; docs/ARCHITECTURE.md',wide=True,status='MEASURED baseline / integration PLANNED')
    assert len(SPECS)==38
    return list(SPECS)

# Keep technical question groups; merged source bodies move to the group's notes.
MERGES={43:44,46:47,48:50,53:55,54:55,66:67,68:69,70:71,72:12,23:36,39:41}
GROUPS=[('Gate acceptance and diagnosis',[44,47,50,51,55,56,57,58,60,62,63,65,67]),('ROS communication and transforms',[11,16,20,21,25,26,27]),('Configuration and calibration',[31,36,37,38]),('Metrics and resource questions',[75,76,78,79,81,82]),('Health and controller tests',[41,69,71]),('Deployment, decisions and history',[5,12,83,84,85,86])]

def remove_evidence_columns(s):
    saved=[]
    def rewrite(m):
        table=m[0]
        if not re.search(r'\\textbf\{(?:Evidence(?: / limit)?|Proposed evidence)\}',table):return table
        saved.append(table)
        # These inherited tables have three unescaped cells in every row.
        table=re.sub(r'L\{[0-9.]+mm\}L\{[0-9.]+mm\}L\{[0-9.]+mm\}',r'L{80mm}L{104mm}',table,count=1)
        lines=table.splitlines()
        for i,line in enumerate(lines):
            if ' & ' in line:
                cells=line.split(' & ');assert len(cells)==3
                suffix=re.search(r'(\\\\.*)$',cells[-1]);assert suffix,line
                lines[i]=' & '.join(cells[:2])+suffix[1]
        return '\n'.join(lines)
    s=re.sub(r'\\begin\{tabular\}.*?\\end\{tabular\}',rewrite,s,flags=re.S)
    return s,saved

def current_corrections(s,old):
    # Historical notes retain provenance but may no longer assert current readiness.
    for a,b in [
      ('Today: Pi 5 4 GB','Historical 13 October: Pi 5 4 GB'),
      ('No camera behavior measured.','Diagnostic stream recordings now exist; complete association/rejection behavior remains unverified.'),
      ('No camera behavior measured','Diagnostic stream recordings exist; estimator association remains unverified'),
      ('No camera behavior measured','Diagnostic stream recordings exist; estimator association remains unverified'),
      ('Both binaries are built; neither has run on this camera.','Recorder diagnostics ran; offline estimator crashed at its first frame. Patch-4 rebuild incomplete.'),
      ('Programs BUILT, never run','Recorder diagnostics ran; no successful D435i estimator run'),
      ('N4A RPE is CALCULATED','N4A RPE is unverified in Phase-8 permitted sources'),
      ('CALCULATED N4A / no gate PASS','RPE UNVERIFIED in permitted sources / no gate PASS'),
      ('verified in Phase 6','prior verification assertion superseded by Phase-8 source restriction'),
      ('Table II, verified','Table II, unverified in audit source set'),
      ('power/RPE/budgets','power and reviewed acceptance budgets'),
      ('power, local-error checks and budgets','power and reviewed acceptance budgets'),
    ]:s=s.replace(a,b)
    if old==44:
        s=s.replace(r'\par\begin{tabular}',r'ARM64: 64-bit Arm; OS: operating system; UTC: Coordinated Universal Time.\par\medskip\begin{tabular}',1)
    if old==55:
        s=s.replace(r'\par\begin{tabular}',r'Transform (TF) messages describe coordinate relationships.\par\medskip\begin{tabular}',1)
    if old==69:
        s=s.replace('API/message review','Application Programming Interface (API) and message review')
    if old==71:
        s=s.replace(r'\par\begin{tabular}',r'MCU denotes the microcontroller unit; its local clock measures controller actions.\par\medskip\begin{tabular}',1)
    if old==41:
        s=s.replace('local balance / LQR / VMC / FSM','balance and actuator control')
        s=s.replace(r'\note{',r'\note{Local controller terms: Linear Quadratic Regulator (LQR), Virtual Model Control (VMC), Finite State Machine (FSM). ',1)
    if old==37:
        s=s.replace('All four unit-specific noise quantities remain UNKNOWN.','Unit-specific noise is UNKNOWN; the diagnostic candidate uses ASSUMED upstream numeric values.')
        s=s.replace('Do not discretize densities twice or replace unresolved noise with example values.','Do not discretize densities twice; assumed upstream values enable diagnostics, not qualification.')
    if old==62:s=s.replace('Default/CAD values and zero placeholder noise do not qualify final VIO.','Factory nominal geometry and assumed numeric noise do not qualify final VIO.')
    if old==65:s=s.replace('wrapper/DDS/executor/queue','SDK callback/queue in the direct path; ROS delivery in the planned path')
    if old==38:s=s.replace('MEASURED helper/build / camera behavior OPEN','PREPARED helper / runtime association UNVERIFIED')
    if old==84:
        s=s.replace('Stereo starts with matching profiles as a reviewed extension.','N4 development selects IR1+IR2 Y8 640$\\times$480/30, gyro/200, accel/100.')
        s=s.replace('Emitter-off is a separate natural-feature tracking experiment.','Development emitter is OFF for fixed-scene feature tracking.')
        s=s.replace('Exact baseline profiles & Paired quality / tail-load comparison','N2 IR1/15; N4 stereo/30 & Independent delivery and load evidence')
        s=s.replace('Preserved emitter state & Separate controlled natural-feature trial','N4 emitter OFF & Reviewed controlled scene/lighting comparison')
        s=s.replace('Preserve accepted emitter setting; compare off/on','Development emitter OFF; compare off/on')
        s=s.replace('PLANNED stereo starts there; emitter-off feature trials are separate','N4 development uses paired 30 Hz images and emitter OFF')
    if old in [56,83]:
        s=s.replace(r'\note{',r'\note{'+escape(F14+' items 3,4,6: microSD take unusable; storage cause inferred; short RAM test clean; USB 2 stick 1.09 MB/s with fsync unsuitable. RAM workaround is diagnostic only, not qualified dataset storage. '),1)
    if old==76:
        # Keep method; do not propagate the earlier calculation's asserted validation.
        s=s.replace(r'\note{Evidence:',r'\note{Phase-8 audit: earlier RPE calculation is UNVERIFIED IN PERMITTED SOURCES; source backup preserves its original exact values and provenance. Earlier claim, not adopted as current fact: Evidence:',1)
        s=s.replace('Tool validation passed per its README','Earlier Phase-7 claim: tool validation passed per its README')
    return s

def build():
    text=BASE.read_text();pre,body=text.split(r'\begin{document}',1)
    original=re.findall(r'\\begin\{frame\}.*?\\end\{frame\}',body,re.S);assert len(original)==91
    audit=(ROOT.parent/AUDIT).read_text()
    decisions={int(i):d for i,d in re.findall(r'^\| (\d\d) \| .*? \| (KEEP|BACKUP|CUT) \|',audit,re.M)}
    assert len(decisions)==91
    main=main_frames(original)
    pre=pre.replace(r'\date{13 October 2026}',r'\date{14 October 2026}').replace('A gate-by-gate engineering guide','Understanding the system and its current evidence')
    pre=re.sub(r'% Content source:.*', '% Content source: Phase-8 audit and dated session facts; provenance in notes.',pre)
    out=[pre+r'\begin{document}\raggedright']
    mapping={};ledger=[]
    for page,(old,name,s) in enumerate(main,1):
        if isinstance(old,int):
            mapping[old]=page
            # Preserve full original notes/technical exposition as archival context.
            _,notes=separate_notes(original[old-1])
            inherited=' '.join(notes)
            if inherited:
                s=s.replace(r'\end{frame}',r'\note{Historical pre-Phase-8 teaching/provenance; latest Phase-8 statements above take precedence. '+current_corrections(inherited,old)+r'}\end{frame}')
        out.append(s);ledger.append((page,'MAIN',str(old),name))
    refs=original[90].replace('Methods are published; project results remain unmeasured.','Methods are published; MH01 results are measured, camera accuracy is unverified.')
    # Reference register stays before the appendix, as explicitly requested.
    out.append(refs);mapping[91]=39;ledger.append((39,'REFERENCES','91','References'))
    out.append(r'\appendix')
    page=39
    for group,ids in GROUPS:
        out.append('% BACKUP GROUP: '+group)
        for old in ids:
            assert decisions[old]=='BACKUP'
            s=current_corrections(original[old-1],old)
            visible,notes=separate_notes(s)
            visible,columns=remove_evidence_columns(visible)
            # All original paths and evidence columns live in notes only.
            notes.extend('Original evidence table (thresholds unchanged): '+t for t in columns)
            for src,dst in MERGES.items():
                if dst==old:
                    merged, merged_notes=separate_notes(current_corrections(original[src-1],src))
                    notes.append('Consolidated audit BACKUP '+str(src)+': '+merged.replace(r'\begin{frame}',r'\textbf').replace(r'\end{frame}','')+' '.join(merged_notes))
            name='Backup: '+title(s)
            visible=re.sub(r'(\\begin\{frame\}(?:\[[^]]*\])?)\{[^}]+\}',lambda m:m[1]+'{'+name+'}',visible,count=1)
            # Group descriptions are notes, not extra separator pages.
            combined=escape('Backup group: '+group+'. Latest status: '+F14+'. ')+ ' '.join(notes)
            s=visible.replace(r'\end{frame}',r'\note{'+combined+r'}\end{frame}')
            out.append(s);page+=1;mapping[old]=page;ledger.append((page,'BACKUP',str(old),name))
            for src,dst in MERGES.items():
                if dst==old:mapping[src]=page
    assert set(mapping)=={i for i,d in decisions.items() if d!='CUT'}
    result='\n'.join(out)+r'\end{document}'+'\n'
    result=result.replace(r'\insertframenumber/\inserttotalframenumber',rf'\insertframenumber/{page}')
    (ROOT/'main.tex').write_text(result)
    (ROOT/'qa/phase8-page-map.json').write_text(json.dumps(mapping,indent=2)+'\n')
    lines=['# Phase 8 page list','','38 main pages; references on page 39; consolidated question appendix follows.','', '| Page | Role | Audit ID | Title |','|---:|---|---|---|']
    lines += [f'| {p} | {r} | {i} | {n} |' for p,r,i,n in ledger]
    (ROOT/'qa/PHASE8_PAGE_LIST.md').write_text('\n'.join(lines)+'\n')
    disposition=['# Phase 8 disposition ledger','','Every original frame is accounted for. The original 91-frame source and PDF remain in main-v4-91p.*. BACKUP command/detail frames consolidated into question-group notes preserve source text and requirements.','', '| Audit ID | Decision | Final page / destination |','|---:|---|---|']
    for i,d in decisions.items():disposition.append(f'| {i:02d} | {d} | '+('CUT; preserved in original backup' if d=='CUT' else str(mapping[i])+(' (consolidated in notes)' if i in MERGES else ''))+' |')
    disposition += ['', 'Added explanations M1--M5 are main pages 12,14,20,27,30. M6--M10 are incorporated in retained frames.','Audit source restriction applied: main omits paper/RPE/Sim(3) comparators; RPE appendix labels earlier calculation unverified. Historical Phase-7 evidence remains unchanged.','All 11 acceptance tables preserve exact requirement/measurement cells. Their evidence columns move into notes.','No hardware, camera, SSH or ORB execution; document build/render only.']
    (ROOT/'qa/PHASE8_DISPOSITION.md').write_text('\n'.join(disposition)+'\n')
    print(f'Phase 8: {page} pages (38 main + 1 references + {page-39} backup).')
    return result
if __name__=='__main__':build()
