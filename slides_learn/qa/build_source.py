from pathlib import Path
root=Path(__file__).resolve().parents[1]
reference=(root.parent/'slides_course/main.tex').read_text()
preamble=reference[:reference.index('\\title{')]
# Keep the reference's theme, fonts, palette, dimensions and base helpers.
preamble+=r'''
\setlength{\emergencystretch}{2em}
\linespread{1.12}
\newcommand{\para}[1]{#1\par\medskip}
\newcommand{\lesson}[1]{\vfill{\color{teal!70!black}\bfseries #1}\par}
\newcommand{\illustration}[2]{\begin{center}\includegraphics[width=.86\linewidth,height=.38\textheight,keepaspectratio]{images/#1.png}\par\small\color{muted}#2\end{center}}
\newcommand{\twocol}[2]{\begin{columns}[T,onlytextwidth]\begin{column}{.48\textwidth}#1\end{column}\begin{column}{.48\textwidth}#2\end{column}\end{columns}}
\newcommand{\diagram}[1]{\begin{center}\begin{tikzpicture}[font=\normalsize]#1\end{tikzpicture}\end{center}}
\tikzset{word/.style={align=center,text width=32mm,minimum height=12mm,draw=rule,fill=white,rounded corners=2pt},dot/.style={circle,fill=teal,inner sep=2.5pt}}
\begin{document}\raggedright
'''
frames=[]
S='experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md'
P='slides_progress/main.tex'
C='slides_course/main.tex'
E='slides_course/qa/n4a-traj-eval-summary.md'
K='docs/D435I_VIO_CALIBRATION_READINESS.md'
def frame(title,body,sources=C,note=''):
    frames.append('\\begin{frame}{'+title+'}\n'+body+'\n\\note{Sources: \\detokenize{'+sources+'}. '+note+'}\n\\end{frame}\n')
def recap(title,points):
    frame(title,'\\para{You should now be able to explain the following in your own words.}\n\\begin{itemize}\n'+''.join('\\item '+p+'\n' for p in points)+'\\end{itemize}\n\\lesson{Try answering aloud before you turn the page.}')
frame('How WBR perception works',r'''
\para{A wheel-biped robot balances on two wheels at the ends of articulated legs. It needs to understand its motion while its controller keeps it upright.}
\illustration{P03}{Conceptual illustration: follow one camera moment through the system.}
\lesson{From sampled signals to an estimate of motion, then to a fair test.}
''',note='Teaching deck for a fourth-year electronics student. All reused illustrations are conceptual, not experimental evidence. WBR means wheel-biped robot.')
frame('We will follow one measurement from sensor to score',r'''
\para{Imagine the robot turning past a table. The camera takes a left and right image of the same corner. Its motion sensor takes samples between images.}
\diagram{\foreach \x/\name/\txt in {0/a/Sensors,4.7/b/Time and space,9.4/c/Motion estimate,14.1/d/Fair test}{\node[word] (\name) at (\x,0){\txt};}\draw[flow](a)--(b);\draw[flow](b)--(c);\draw[flow](c)--(d);}
\para{First we learn what the signals mean. Then we learn how software combines them, how to judge the answer, and why the project tests each layer in order.}
\lesson{The same table corner will return throughout the deck.}
''')
frame('The robot needs both its own motion and nearby geometry',r'''
\para{Wheel rotation alone can mislead us when a wheel slips. A camera can see the table corner move across its image even when wheel measurements are wrong.}
\para{A \textbf{pose} is a position and an orientation: where the sensor is, and which way it points. A sequence of poses is a \textbf{trajectory}, or path through time.}
\para{Depth tells us how far away a visible surface is. Together, motion and depth help the robot reason about obstacles and where it can move.}
\lesson{Seeing a table is useful only if we know where the camera was when it saw it.}
''')
frame('Balance must survive a delayed perception computer',r'''
\twocol{\para{The \textbf{STM32H7} owns motor safety and the hard real-time control loop. Hard real-time means a deadline must be met to preserve the required behavior.}
\para{Think of a timer interrupt that must update control before the next tick.}}{\para{The \textbf{Raspberry Pi} runs perception on Linux. Image processing can take variable time, and the operating system can delay a task.}
\para{Its estimates must be checked for freshness and validity before a future controller interface uses them.}}
\diagram{\node[word] (p) at (0,0){Pi estimates motion};\node[word] (s) at (7,0){STM32H7 keeps control};\draw[flow,dashed](p)--node[above=8mm]{Planned checked interface}(s);}
\lesson{An old or missing pose must not become an unsafe motor command.}
''',P+'; AGENTS.md',note='Existing ownership boundary only. No new interface, rate or fallback budget is proposed.')
recap('You can now explain why perception and control are separate',[
'A pose describes position and orientation; depth describes distance to a surface.',
'The Pi can help understand the scene while the STM32H7 keeps responsibility for control and safety.',
'Explain what could happen if a controller treated an old pose as a current measurement.'])
frame('The D435i combines two views with a motion sensor',r'''
\illustration{P04}{Stylized D435i housing; the aperture drawing is not a hardware guide.}
\para{Two \textbf{infrared cameras} form a stereo pair: left and right views from different positions. The \textbf{IMU}, or inertial measurement unit, contains a gyroscope and an accelerometer.}
\para{In our running moment, both images see the table corner. The IMU measures the camera's turning and acceleration between image times.}
\lesson{The images and IMU provide different kinds of information about the same motion.}
''',S+'; '+C)
frame('Stereo depth comes from a corner shifting between views',r'''
\para{\textbf{Disparity} is the horizontal difference between the positions of the same point in the left and right images. Nearby points shift more than distant points.}
\diagram{\draw[navy,thick](0,0)rectangle(5,1.7);\draw[navy,thick](8,0)rectangle(13,1.7);\node at(2.5,2.15){Left image};\node at(10.5,2.15){Right image};\node[dot](a)at(3,1){};\node[dot](b)at(10.4,1){};\draw[flow](a)--++(0,-1.5);\draw[flow](b)--++(0,-1.5);\node at(2.5,-.95){Corner at 120 pixels};\node at(10.5,-.95){Corner at 100 pixels};}
\para{Illustrative example: rectification aligns matching image rows. Focal length sets the projection scale in pixels. With $f=400$ pixels and camera separation $b=0.05$ metres, disparity $d=20$ pixels gives depth $Z=fb/d=1$ metre.}
\lesson{At 10 pixels of disparity, the same example gives 2 metres of depth.}
''',note='All numbers on this page are illustrative, not D435i calibration. Rectification digitally aligns the stereo views using calibration. Pinhole stereo geometry; focal length is defined here as projection scale in pixels and developed on calibration page.')
frame('IMU readings are useful signals with noise and bias',r'''
\para{A \textbf{gyroscope} measures angular velocity: how fast the camera turns. An \textbf{accelerometer} measures specific force: acceleration relative to free fall. A supported stationary sensor therefore still responds to gravity.}
\twocol{\para{\textbf{Noise} is the rapid random variation, like ADC readings that scatter around a steady input.}\para{\textbf{Bias} is an offset that may change slowly, like an ADC zero error.}}{\diagram{\draw[flow](0,0)--(5,0)node[right]{Time};\draw[navy,dashed](0,.8)--(5,.8);\node[above,font=\small,fill=paper]at(2.5,.8){Unbiased reference};\draw[teal,thick](0,1.3)--(.6,1.5)--(1.1,1.2)--(1.7,1.45)--(2.3,1.25)--(3,1.5)--(3.6,1.3)--(4.3,1.4)--(5,1.25);\node at(2.5,2){Offset plus scatter};\node at(2.5,-.6){Illustrative stationary signal};}}
\lesson{Integrating a small bias repeatedly can create a growing motion error.}
''')
frame('The projector is off so features belong to the room',r'''
\para{A \textbf{feature} is a recognizable image detail, such as a corner. The infrared projector adds dots that can help the depth system match points on a plain surface.}
\diagram{\node[word] (a)at(0,0){Projected dots};\node[word] (b)at(6,0){Real table corner};\node[word] (c)at(12,0){Stable scene structure};\draw[faultflow,dashed](a)--++(0,-1.5)node[below,align=center]{Pattern can move\\with the projector};\draw[flow](b)--(c);}
\para{For visual motion estimation, we want persistent details attached to the room. Projected dots can change on surfaces as the camera moves and create misleading matches.}
\lesson{Turning off the projector trades artificial texture for more trustworthy natural texture.}
''',S+'; '+P)
recap('You can now explain what each sensor contributes',[
'Two views turn a pixel shift into depth when camera geometry is known.',
'The gyro measures turning, and the accelerometer responds to motion and gravity.',
'Explain why random noise, slowly changing bias and moving projected dots cause different problems.'])
frame('A coordinate frame says what a position is relative to',r'''
\para{A \textbf{coordinate frame} is an origin and a set of axes. The same table corner has different coordinates relative to the camera, robot torso and room.}
\twocol{\diagram{\draw[navy,thick,rounded corners](1,1.7)rectangle(3,3);\draw[navy,very thick](1.4,1.7)--(.9,.9)--(1.3,0);\draw[navy,very thick](2.6,1.7)--(3.3,.9)--(3,0);\draw[navy,thick](1.3,-.3)circle(.3);\draw[navy,thick](3,-.3)circle(.3);\draw[flow,teal](2,2.3)--(4.4,2.3)node[right]{Body};\draw[flow,teal](2,2.3)--(2,4);\draw[flow,fault](2.7,3.1)--(4.3,3.7)node[right]{Camera};\draw[flow,fault](2.7,3.1)--(2.3,4.2);\draw[flow](0,-1)--(4,-1)node[right]{World};\draw[flow](0,-1)--(0,2);}}{\para{A \textbf{transform} converts coordinates between frames by rotating the axes and shifting the origin.}\para{It is like translating a sensor's local description into the robot's shared description.}\para{This schematic wheel-biped drawing shows two axes per frame to keep the geometry readable.}}
\lesson{Never compare positions until they describe the same frame.}
''',note='Schematic wheel-biped with torso, two articulated legs and one wheel at each foot. Axis directions are illustrative, not a proposed physical mounting convention.')
frame('A timestamp names the measurement time, not its arrival',r'''
\para{A \textbf{timestamp} is a clock reading attached to a measurement. Like capturing a timer value at an interrupt, it tells us when the event happened.}
\diagram{\draw[flow](0,0)--(15,0)node[right]{Time};\foreach \x/\text in {1/Image exposure,6/USB delivery,11/Software reads}{\draw[navy,thick](\x,-.2)--(\x,.4);\node[align=center,text width=35mm]at(\x,1.1){\text};}\draw[teal,thick,<->](1,-1)--(6,-1)node[midway,below]{Transport delay};}
\para{Our stereo pair belongs at its exposure time. Motion samples must cover the interval since the previous image, even if the Pi receives some of them later.}
\lesson{Using arrival time would turn scheduling delays into apparent sensor motion.}
''',K+'; '+C)
frame('Different clocks need a measured relationship',r'''
\para{A \textbf{clock domain} is the time reference used by a clock. The camera, Pi and STM32 can each start counting at a different origin and run at slightly different rates.}
\diagram{\foreach \y/\name/\txt in {2/Camera/12.000 seconds,0/Pi/450.015 seconds,-2/STM32/8.002 seconds}{\node[anchor=east]at(0,\y){\name};\draw[flow](.5,\y)--(10,\y);\node[fill=paper]at(5,\y){\txt};}\draw[teal,dashed,thick](8,-2.4)--(8,2.4);\node[anchor=west]at(10.5,0){Same event};}
\para{These illustrative readings cannot be subtracted directly. An \textbf{offset} relates their origins; clock-rate drift changes that relationship over time. A common-looking time label alone does not prove exposure alignment.}
\lesson{Record the clock domain as carefully as the timestamp value.}
''',K+'; '+C)
recap('You can now explain where and when a sample belongs',[
'A frame names the axes and origin; a transform connects two frames.',
'A timestamp names a measurement event, while arrival time includes delivery delay.',
'Explain why subtracting two readings from unrelated clocks does not give a time delay.'])
frame('Features let the computer recognize the same corner',r'''
\para{A \textbf{feature} is a distinctive small image region, such as our table corner. ORB features describe such regions with compact bit patterns that software can compare.}
\diagram{\draw[navy,thick](0,0)rectangle(5,2.6);\draw[navy,thick](8,0)rectangle(13,2.6);\draw[navy,very thick](1,.5)--(1,1.8)--(3.5,1.8);\draw[navy,very thick](9,.5)--(9,1.8)--(11.5,1.8);\node[dot](a)at(1,1.8){};\node[dot](b)at(9,1.8){};\draw[flow,teal](a)--node[above,fill=paper]{Match}(b);\node at(2.5,-.5){One image};\node at(10.5,-.5){Another image};}
\para{\textbf{Feature matching} means deciding which regions show the same physical point. Software tests many matches together; a similar bit pattern alone is not enough.}
\lesson{The table corner becomes a repeatable observation rather than a whole picture to memorize.}
''',C,note='ORB descriptor and geometric consistency: Campos et al. 2021. Drawing schematic, not measured feature output.')
frame('Tracking estimates the pose that explains the image',r'''
\para{\textbf{Tracking} means estimating the current pose from recent measurements. If the camera turns, the table corner appears at a new pixel position.}
\diagram{\node[word](a)at(0,0){Earlier pose};\node[word](b)at(5,0){Predicted pose};\node[word](c)at(10,0){Image agrees?};\draw[flow](a)--(b);\draw[flow](b)--(c);\draw[flow,teal](c.south)--++(0,-1.2)-|node[below,pos=.25]{Correct the prediction}(b.south);}
\para{The estimator predicts where previously estimated scene points should appear, compares those predictions with observed pixels, and adjusts the pose to reduce the mismatch.}
\para{This resembles a control observer: predict the state, then use a measurement to correct it.}
\lesson{A pose is an estimate supported by many image matches, not a direct camera output.}
''')
frame('Keyframes and map points preserve useful geometry',r'''
\para{A \textbf{keyframe} is an image and its pose, kept because they add useful information. A \textbf{map point} is an estimated three-dimensional scene point observed in multiple images.}
\diagram{\foreach \x/\id/\txt in {0/a/First keyframe,6/b/New viewpoint,12/c/Later keyframe}{\node[word](\id)at(\x,0){\txt};}\node[dot](p)at(6,2.3){};\node[above]at(p){Table corner in the map};\draw[navy](a)--(p);\draw[navy](b)--(p);\draw[navy](c)--(p);}
\para{\textbf{SLAM} means simultaneous localization and mapping: estimating sensor poses and scene geometry together. Visual-inertial odometry estimates motion from images and IMU samples; SLAM also reuses a map and recognizes old places.}
\lesson{The map and the camera poses help constrain each other.}
''')
frame('The IMU predicts motion between camera images',r'''
\para{Images arrive less often than IMU samples. \textbf{IMU preintegration} summarizes the turning and motion measured between two image times, instead of revisiting every sample for every pose correction.}
\diagram{\draw[flow](0,0)--(14,0);\foreach \x in {1,13}{\draw[navy,very thick](\x,-.3)--(\x,.6);}\foreach \x in {2,3,4,5,6,7,8,9,10,11,12}{\draw[teal,thick](\x,0)--(\x,.25);}\node at(1,1.2){Earlier image};\node at(13,1.2){Our stereo pair};\node at(7,-.8){Summarize the intervening IMU samples};}
\para{The IMU helps during rapid motion and helps estimate gravity. Stereo supplies distances in metres, rather than arbitrary units, through its known camera separation.}
\para{\textbf{IMU initialization} estimates starting velocity, gravity direction and sensor biases. Varied motion helps distinguish these unknowns.}
\lesson{An IMU prediction bridges image times; image observations keep inertial drift in check.}
''',C+'; '+S,note='Campos et al. 2021 visual-inertial initialization and preintegration. Timeline counts are schematic, not a requested sensor profile.')
frame('Three threads share the work and recognize old places',r'''
\para{A \textbf{thread} is a software task that can run alongside other tasks. Our SLAM software, \textbf{ORB-SLAM3}, separates urgent tracking from slower map improvement and place recognition.}
\diagram{\node[word](a)at(0,0){Tracking\\Current pose};\node[word](b)at(6,0){Local mapping\\Refines the map};\node[word](c)at(12,0){Loop closing\\Old places};\draw[flow](a)--(b);\draw[flow](b)--(c);\draw[flow,teal](c.south)--++(0,-1)-|(a.south);}
\para{\textbf{Loop closing} recognizes a place seen earlier. Returning to our table gives a new constraint: these two visits should refer to the same scene, so accumulated drift can be corrected.}
\lesson{Different responsibilities share one map; concurrent work does not guarantee a timing deadline.}
''',C,note='Campos et al. 2021 system overview. Diagram expresses conceptual data sharing, not an exhaustive thread synchronization graph.')
frame('Tracking fails when observations stop constraining motion',r'''
\para{\textbf{Calibration} measures sensor properties so software can interpret the readings correctly.}
\begin{itemize}
\item Blur smears corners, and a blank wall offers few distinctive features to match.
\item Wrong calibration predicts the wrong pixels even for the correct pose.
\item Wrong time pairing combines an image with motion from a different instant.
\item A poorly initialized IMU can pull an otherwise plausible visual estimate in the wrong direction.
\end{itemize}
\para{In our running moment, a missed corner match is different from pairing the corner with the wrong turn. The symptom may look similar, but the layer to inspect is different.}
\lesson{Check input quality, time and geometry before changing algorithm settings.}
''')
recap('You can now explain how images and IMU produce a pose',[
'Features identify observations; tracking finds a pose that explains them.',
'Keyframes and map points preserve geometry, and loop closing constrains drift.',
'Explain how preintegration and initialization make IMU samples useful, and why bad inputs can still defeat SLAM.'])
frame('Calibration tells software what the sensor geometry means',r'''
\para{\textbf{Intrinsics} describe one camera's projection: focal length sets the pixel scale, the image center sets the origin, and distortion models lens warping.}
\para{\textbf{Extrinsics} describe the rotation and translation between sensors. Stereo needs the relation between cameras; visual-inertial estimation also needs the camera-to-IMU relation.}
\diagram{\node[word](a)at(0,0){Left camera};\node[word](b)at(6,0){Right camera};\node[word](c)at(12,0){IMU};\draw[flow,<->](a)--node[above=8mm]{Stereo geometry}(b);\draw[flow,<->](b)--node[above=8mm]{Rigid relation}(c);}
\lesson{Factory values are a starting description; their origin and suitability still need checking.}
''',K+'; '+S)
frame('Calibration must also describe time and uncertainty',r'''
\twocol{\para{A \textbf{camera--IMU time offset} describes how far the image and motion timelines are shifted relative to each other. Sharing a clock domain alone does not establish their physical alignment.}\para{\textbf{IMU noise parameters} tell the estimator how much to trust samples and how quickly bias can change.}}{\illustration{P08}{Conceptual target; not a calibration grid.}}
\para{\textbf{Kalibr} fits camera and IMU geometry and timing from motion past a measured target. \textbf{Allan deviation} analyzes a long stationary IMU recording to estimate noise and slow bias behavior.}
\lesson{Default values and a warning about unavailable IMU calibration do not become measured calibration.}
''',K+'; '+S,note='Kalibr camera-IMU calibration and IMU noise model documentation. Current-unit factory warning is preserved in session facts; older-unit values must not be transferred.')
recap('You can now explain why calibration comes before trust',[
'Intrinsics connect a three-dimensional point to a pixel, and extrinsics connect sensor frames.',
'Camera--IMU time offset and noise parameters describe different sources of error.',
'Explain why a room-motion test and a measured-target calibration recording answer different questions.'])
frame('USB and the driver deliver samples before SLAM sees them',r'''
\para{The stereo pair and motion samples travel over local USB to the Pi. \textbf{librealsense} is the software development kit (\textbf{SDK}) that exposes images, motion readings and their metadata to programs.}
\diagram{\node[word](a)at(0,0){D435i samples};\node[word](b)at(5,0){USB delivery};\node[word](c)at(10,0){librealsense};\draw[flow](a)--(b);\draw[flow](b)--(c);}
\para{Think of UART framing: valid electrical access comes before interpreting a packet. Here we must first check identity, link speed, sample continuity and timestamps.}
\para{Acquisition stays on the Pi. A remote shell controls the session; it does not carry the sensor stream to SLAM.}
\lesson{A driver delivering images is necessary, but it does not prove correct motion estimation.}
''',P+'; AGENTS.md')
frame('ROS 2 messages make sensor data available to other tasks',r'''
\para{\textbf{ROS 2} is robotics middleware: it connects software components. A \textbf{node} is a participating program; a \textbf{topic} is a named channel carrying a defined message type.}
\diagram{\node[word](a)at(0,0){Sensor node};\node[word](b)at(6,0){Image topic};\node[word](c)at(12,0){Recorder node};\draw[flow](a)--(b);\draw[flow](b)--(c);}
\para{Our image message contains the pixel array and a header identifying its time and frame. Other messages carry motion samples and calibration. Like a packet format, the metadata matters as much as the payload.}
\lesson{A topic name alone cannot prove that its messages have the right times or coordinate frames.}
''',C+'; '+P)
frame('Recording once lets us replay the same problem',r'''
\para{A \textbf{bag} is a file-based recording of streams and their timing information. Replaying it lets us test identical input repeatedly, like saving a logic-analyzer trace instead of reproducing an intermittent interrupt.}
\twocol{\para{The ROS 2 path is driver, topics, then a rosbag2 recording. It tests the middleware pipeline.}\para{The D435i input program records directly through librealsense and feeds playback to ORB-SLAM3, bypassing ROS 2.}}{\illustration{P10}{Conceptual review of recorded input.}}
\para{\textbf{Offline} processing reads saved input and can wait for computation. \textbf{Live} processing reads arriving samples and must keep up. The two bag paths need separate compatibility checks.}
\lesson{Record first to separate input problems from live scheduling problems.}
''',S+'; '+P,note='SDK recording uses a rosbag2-format container in the installed SDK, but is not asserted interchangeable with the N3 ROS bag or Kalibr. Preserve source timestamps and input data.')
recap('You can now trace our moment through the software',[
'The camera sends measurements over USB; librealsense exposes them to programs.',
'ROS 2 topics carry typed messages, and bags preserve input for repeated tests.',
'Explain how the ROS recording route differs from the current direct SDK adapter, and what live processing adds.'])
frame('Ground truth gives an independent answer to compare against',r'''
\para{\textbf{Ground truth} is an independently measured reference, with its own uncertainty. A smooth estimated path is not enough: it can still be smoothly wrong.}
\para{\textbf{EuRoC} is a public drone dataset with stereo images, IMU samples and reference motion measurements. The machine-hall sequence called MH01 gives us known input before adapting to our camera.}
\diagram{\node[word](a)at(0,0){Recorded sensors};\node[word](b)at(6,0){Estimated pose};\node[word](c)at(12,0){Reference pose};\draw[flow](a)--(b);\draw[flow,<->,teal](b)--node[above=8mm]{Compare same time}(c);}
\lesson{Our table-camera recording needs an independent reference before we can claim absolute accuracy.}
''',S+'; '+E,note='Burri et al. 2016 EuRoC MAV datasets. Ground truth sources vary by sequence; MH01 uses the machine-hall position reference. Frame and clock assumptions are required before scoring.')
frame('Alignment removes an arbitrary origin without hiding scale',r'''
\para{\textbf{Alignment} places two trajectories in the same coordinate frame. A \textbf{rigid alignment} rotates and shifts the entire estimated path once, without stretching it.}
\diagram{\draw[teal,very thick](0,0)--(2,0)--(2,2);\draw[fault,very thick](3,1)--(3,3)--(1,3);\node at(1.5,-.7){Before: different origins};\draw[flow](5,1)--(7,1);\draw[teal,very thick](9,0)--(11,0)--(11,2);\draw[fault,dashed,very thick](9,.12)--(11,.12)--(11.12,2);\node at(10,-.7){After: one shared frame};}
\para{Teal shows the reference; coral shows the estimate. SLAM can choose its own world origin, so removing that difference is fair. Stereo already provides distances in metres. Stretching its trajectory would conceal an error in those distances.}
\lesson{Match timestamps and sensor frames first; then use rotation and translation for the main score.}
''',E+'; '+P,note='Schematic paths; no measured results drawn. SE(3) alignment for main comparison, Sim(3) diagnostic only. Association tolerance 0.02 s; shared EuRoC clock assumed, zero offset; common IMU-body frame.')
frame('ATE measures the global position mismatch',r'''
\para{\textbf{ATE}, absolute trajectory error, compares estimated and reference positions at matched times after alignment. A \textbf{residual} is one remaining difference.}
\twocol{\diagram{\draw[flow](0,0)--(5,0)node[right]{$x$};\draw[flow](0,0)--(0,3)node[above]{$y$};\node[dot](a)at(2,1){};\node[circle,fill=fault,inner sep=2.5pt](b)at(3.5,2){};\draw[thick,<->](a)--node[below right]{5 cm}(b);\node[below]at(a){Reference};\node[above]at(b){Estimate};}}{\para{Illustrative example: the aligned position differs by 3 cm in one direction and 4 cm in the perpendicular direction.}\para{The residual length is $\sqrt{3^2+4^2}=5$ cm.}\para{\textbf{RMSE}, root mean square error, squares every residual length, averages the squares, then takes the square root.}}
\lesson{ATE RMSE summarizes the whole matched path; it is not an error bound for every pose.}
''',E+'; '+C,note='Example numbers illustrative. Diagram axes schematic, not to scale. For residuals 3 cm and 4 cm, RMSE would be sqrt((9+16)/2)=3.54 cm; example not included as experimental result.')
frame('RPE asks how much a short motion segment is wrong',r'''
\para{\textbf{RPE}, relative pose error, compares motion between two times rather than absolute positions. It can measure both displacement error and turning error.}
\diagram{\draw[flow,teal](0,.6)--(9,.6);\draw[flow,fault](0,-.6)--(10,-.6);\node[anchor=east]at(0,.6){Reference};\node[anchor=east]at(0,-.6){Estimate};\node at(0,1.4){Start};\node at(9,1.4){One second later};\draw[thick,<->](9,-1.2)--(10,-1.2);\node[below]at(9.5,-1.2){1 cm difference};}
\para{Illustrative drawing, not to scale: reference displacement is 1.00 m, estimate is 1.01 m, with no turning difference. Translational RPE is 1 cm.}
\para{Our evaluation selects segments ending at least one second after their start. This describes local drift over that interval, not a constant error rate.}
\lesson{ATE asks about the global path; RPE asks about individual motion segments.}
''',E,note='Pair policy: first later reference timestamp >= 1 s per eligible start, no interpolation. Actual rotational RMSE about 0.076 degrees. Arrows schematic, not to scale.')
frame('Three EuRoC runs support the build, not our camera',r'''
\para{The input is about 184 seconds of drone motion. The evaluated reference span covers about 81 metres of travel. Each run uses the same recorded sensor data.}
\begin{center}\begin{tabular}{lrr}\toprule
 & Global ATE RMSE & One-second translational RPE RMSE\\\midrule
First run & 4.15 cm & 1.33 cm\\
Second run & 3.68 cm & 1.36 cm\\
Third run & 4.16 cm & 1.40 cm\\\bottomrule
\end{tabular}\end{center}
\para{The paper's MH01 comparator is about 3.6 cm. Our mean is about 4.0 cm, but three-run mean and paper ten-run median are different statistics. The full protocols are not proven identical.}
\para{The runs support the native build on known input. They do not test D435i calibration or healthy real-time speed; under-voltage affected the Pi.}
''',S+'; '+E+'; '+P,note='Paper comparator verified in slides_progress: Campos et al. 2021 Table II, MH01 stereo-inertial 0.036 m; median of ten runs and processed GT. Local RPE independently calculated by trajectory_eval, not evo RPE. Evaluated matched span ~181.88 s and 80.606 m; full input ~184 s. All three one map, no resets, IMU initialized. Run times 301/282/284 s under power faults; no gate PASS inferred.')
recap('You can now explain what an accuracy score proves',[
'Ground truth must independently measure the quantity we want to test.',
'Rigid alignment removes an arbitrary origin; ATE and RPE answer different questions.',
'Explain why good EuRoC accuracy does not qualify the D435i, its timing or live speed.'])
frame('The first gates establish a trustworthy sensor path',r'''
\para{A \textbf{gate} is a question that must be answered with evidence before depending on that layer. It is like checking power and UART framing before debugging the application protocol.}
\begin{itemize}
\item \textbf{N0 asks whether the Pi has stable power, cooling and a usable platform.} An unstable computer makes later failures ambiguous.
\item \textbf{N1 asks whether the intended camera has correct USB access.} Its own link must be at least 5000 megabits per second; a slow fallback can limit delivery.
\item \textbf{N2 asks whether raw samples, directly from the sensor, arrive correctly over time.} A mandatory 300-second continuous run (five minutes) catches sustained faults that a brief preview can miss.
\item \textbf{N3 asks whether ROS 2 preserves those measurements through recording and replay.} This isolates middleware faults before estimation.
\end{itemize}
''',P,note='N2 exact baseline: IR1-only 640x480 Y8 at 15 Hz, gyro 200 Hz, accel 100 Hz; 20/105/300 s stages. Thresholds and profile remain unchanged in actual Phase A runbook. No command performed.')
frame('The estimation gates separate algorithm, camera and timing load',r'''
\begin{itemize}
\item \textbf{N4A asks whether the build works on known EuRoC input.} It can be investigated independently of camera transport because the dataset already supplies measurements.
\item \textbf{N4B asks whether recorded D435i input supports reliable offline estimation.} It follows sensor qualification, a reviewed stereo extension and calibration review, so identical input can be inspected repeatedly.
\item \textbf{N4C asks whether live estimation keeps up without losing trustworthy input.} It comes after offline review because live scheduling adds another possible failure source.
\end{itemize}
\para{The strict raw gate uses one infrared stream. Stereo development uses two; adding the second stream is a separate reviewed extension, not a silent change to the baseline.}
\lesson{A useful development trajectory can guide calibration without qualifying the live system.}
''',P+'; '+S,note='N4B development may expose calibration problems; repeat qualified offline review with accepted calibration before N4C. Main gate ladder is instructional, no authorization for execution.')
frame('The final gates connect timing evidence to safe use',r'''
\begin{itemize}
\item \textbf{N5 asks where computation time and resources go.} Measure processing, queues and sample age before promising a usable update rate.
\item \textbf{N6 asks whether unreliable perception is detected and handled.} A correct-looking pose is unsafe if it is stale, invalid or from a restarted map.
\item \textbf{N7 asks whether the controller integration behaves safely.} It follows timing and health checks because the STM32H7 must know when a perception input is usable.
\end{itemize}
\para{\textbf{Latency} is delay between defined events. \textbf{Sample age} is how old the measurement is when consumed. A short computation can still use old input if a queue is growing.}
\lesson{Define clock relationships and failure behavior before making a control promise.}
''',C+'; '+P,note='N5/N6/N7 planned. Existing safety ownership preserved; no public interface or numeric budget introduced.')
frame('Debug from the physical layer upward',r'''
\diagram{\foreach \x/\name/\txt in {0/a/Power,4.5/b/Raw input,9/c/Time and geometry,13.5/d/Estimator}{\node[word](\name)at(\x,0){\txt};}\draw[flow](a)--(b);\draw[flow](b)--(c);\draw[flow](c)--(d);}
\para{If raw samples already have gaps, changing SLAM parameters cannot recover missing measurements. If replay is good but live input falls behind, inspect scheduling and queues.}
\para{If identical offline input fails, inspect image quality, timestamp pairing, initialization and calibration before tuning the estimator. Change one cause at a time and preserve failed logs.}
\lesson{The next investigation should answer the first unresolved question, not the most exciting one.}
''',P+'; AGENTS.md')
recap('You can now explain why the gates have this order',[
'N0 through N3 qualify the platform and delivery; N4 separates known input, our camera and live processing.',
'N5 through N7 establish timing, health behavior and safe controller integration.',
'Explain which layer you would inspect if replay succeeds while live tracking falls behind.'])
frame('Today we have a baseline, and the next step is reliable input',r'''
\para{As of 13 October 2026, three EuRoC runs have produced initialized trajectories on the Pi. D435i recording and estimation programs are built, but this new camera path has not been run.}
\para{The Pi had under-voltage. No gate has been accepted for the current setup. A compiled program or an old test on another camera is not enough.}
\para{Next: restore stable power, preserve the OS card, qualify separate data storage, then repeat camera access, raw delivery and ROS recording checks. Only then develop the stereo recording, calibration and offline estimation before live use.}
\lesson{Camera-dependent work waits for the owner's explicit CAMERA AVAILABLE authorization.}
''',S+'; '+P+'; AGENTS.md',note='Single current-status page. MicroSD is OS/tools/small logs; large bags require separately qualified storage. Session capacity estimate is not a storage qualification. New camera identity differs from September unit; four serial-related fields remain distinct. No new capture, device access or ORB execution performed.')
recap('You can now choose and explain the next useful task',[
'Tell the story of one stereo pair and its IMU samples from capture through recording to a pose and a score.',
'Distinguish the measured EuRoC baseline from the unqualified camera pipeline and planned integration.',
'Brief a collaborator with one question, the input needed to answer it, and the condition that should stop the work.'])
frame('These terms summarize the ideas you have learned',r'''
\twocol{
\para{\textbf{Pose and trajectory.} Position plus orientation, and their history.}
\para{\textbf{Disparity.} A point's horizontal shift between stereo views.}
\para{\textbf{Feature and match.} A distinctive image region, and its correspondence.}
\para{\textbf{Keyframe and map point.} A kept viewpoint and an estimated scene point.}
\para{\textbf{Bias.} A sensor offset that may slowly change.}
\para{\textbf{Preintegration.} A summary of IMU motion between image times.}
}{
\para{\textbf{Frame and transform.} Axes and origin, and a conversion between them.}
\para{\textbf{Timestamp and clock domain.} An event's time and its clock reference.}
\para{\textbf{Intrinsics and extrinsics.} Camera projection and relations between sensors.}
\para{\textbf{Alignment.} Placing paths in one frame.}
\para{\textbf{ATE and RPE.} Global position error and error in a motion segment.}
\para{\textbf{RMSE.} The square root of the average squared errors.}
}
''')
frame('Each tool answers a different engineering question',r'''
\begin{tabular}{@{}p{42mm}p{145mm}@{}}\toprule
\textbf{Tool} & \textbf{Purpose}\\\midrule
librealsense & Reads camera measurements and SDK recordings.\\[6pt]
realsense-ros & Publishes camera data and metadata as ROS 2 messages.\\[6pt]
rosbag2 & Records and replays ROS 2 topic streams.\\[6pt]
ORB-SLAM3 & Estimates poses and a map from images and motion samples.\\[6pt]
evo & Evaluates estimated trajectories against reference trajectories.\\[6pt]
Trajectory evaluator & Calculates the documented local RPE and comparison plots.\\[6pt]
Kalibr & Fits sensor geometry and time offset from a measured target.\\[6pt]
Allan analysis & Estimates noise and bias behavior from stationary IMU data.\\\bottomrule
\end{tabular}
\lesson{Choose the tool from the question you need to answer.}
''',P+'; '+K)
frame('These commands belong to reproduction, not the teaching story',r'''
\para{Deck-only reproduction from this repository. These commands do not access the camera.}
{\small\ttfamily
cd slides\_learn\par
latexmk -xelatex -interaction=nonstopmode main.tex\par\medskip
swift -module-cache-path qa/swift-cache \textbackslash{}\par
\quad \textasciitilde/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift \textbackslash{}\par
\quad main.pdf preview\par}
\medskip\para{Future offline scoring shape, using saved files only:}
{\small\ttfamily evo\_ape tum REFERENCE.tum ESTIMATE.tum -a\par}
\medskip\para{First make times, frames and file formats compatible. The alignment option rotates and shifts; it does not correct sensor timing or establish ground truth. Camera procedures stay in the approved runbook.}
''',P,note='Command cheat-sheet includes actual deck reproduction and future evo shape from progress deck. Not executed here: trajectory scoring or physical sensor procedures. REFERENCE/ESTIMATE are placeholders; ORB output needs validated parsing/conversion.')
frame('The sources separate project evidence from general methods',r'''
{\small
\para{\textbf{Project evidence.} Session facts of 13 October 2026; the three-run trajectory evaluation summary; calibration readiness notes; the course, progress and report decks. Detailed source locations are attached to each page as speaker notes.}
\para{\textbf{SLAM.} Campos et al. (2021), \emph{ORB-SLAM3}, IEEE Transactions on Robotics. \href{https://arxiv.org/abs/2007.11898}{Paper and system design}. Table II supplies the MH01 comparison.}
\para{\textbf{Dataset.} Burri et al. (2016), \emph{The EuRoC micro aerial vehicle datasets}, International Journal of Robotics Research. \href{https://ethz-asl.github.io/datasets/}{ETH dataset archive}.}
\para{\textbf{Calibration.} ETH ASL \href{https://github.com/ethz-asl/kalibr/wiki/camera-imu-calibration}{Kalibr camera--IMU guide} and \href{https://github.com/ethz-asl/kalibr/wiki/IMU-Noise-Model}{IMU noise model}.}
\para{\textbf{Images.} Reused course illustrations are conceptual. New geometry diagrams are schematic; worked numbers are explicitly illustrative.}
}
''',S+'; '+E+'; '+K+'; '+C+'; '+P+'; slides_report/main.tex',note='Primary references accessed 14 October 2026. Course theme copied, assets P03/P04/P08/P10 copied byte-identically. Sources are not gate acceptance. Textbook geometry explained in original words.')
assert len(frames)==45,len(frames)
(root/'main.tex').write_text(preamble+'\n'.join(frames)+'\\end{document}\n')
(root/'qa/page_manifest.txt').write_text('\n'.join(f'{i+1:02d} '+f.split('\\begin{frame}{',1)[1].split('}\n',1)[0] for i,f in enumerate(frames))+'\n')
print(f'Wrote {len(frames)} frames')
