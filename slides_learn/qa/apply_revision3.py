"""Apply the requested learning table and references to the archived Revision 2."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'qa/revision3-before/main.tex').read_text()
learning=r'''\begin{frame}{What to learn before each gate}

{\small
\begin{tabular}{@{}L{45mm}L{47mm}L{43mm}L{51mm}@{}}\toprule
\textbf{Gate and its question} & \textbf{Concepts to understand first} & \textbf{One primary source to read} & \textbf{Self-check}\\\midrule
\textbf{N0.} Is the Pi stable under load? & Power and cooling; throttling means reduced processor speed. & Raspberry Pi hardware docs: power and cooling. & Why can low voltage make a speed test misleading?\\[4pt]
\textbf{N1.} Can we access the intended camera over fast USB? & Device identity; actual USB link speed; permissions. & librealsense troubleshooting guide: USB connection. & Why does a fast USB hub not prove the camera link is fast?\\[4pt]
\textbf{N2.} Do raw samples keep arriving correctly? & Sample intervals; gaps; bias; Allan analysis compares noise across averaging times. & Kalibr IMU noise model: Allan analysis. & Why does a short, clean preview not prove sustained delivery?\\[4pt]
\textbf{N3.} Does ROS 2 preserve data through recording and replay? & Topics; QoS means delivery rules; tf2 handles frame transforms; bag replay. & ROS 2 tutorials: topics, QoS, tf2 and recording. & What must survive replay besides the image pixels?\\\bottomrule
\end{tabular}}

\note{Sources: \detokenize{slides_learn/BRIEF.md Revision 3; slides_progress/main.tex; slides_course/main.tex; docs/PERCEPTION_TOOLING_ARCHITECTURE.md}. Primary readings: Raspberry Pi hardware documentation; librealsense Troubleshooting Q\&A; ETH ASL Kalibr IMU Noise Model; official ROS 2 Jazzy tutorials. Links on references page. N2 Allan reading explains sensor noise, not transport acceptance: sample gaps and intervals still need raw delivery evidence. The 300-second soak is not an Allan calibration record. N1 USB >=5000M on the camera's own branch; N2 exact IR1-only profile and 20/105/300-second sequence unchanged. Self-check answers: N0 reduced frequency or resets confound speed; N1 downstream link can fall back independently; N2 intermittent/sustained faults require full soak; N3 preserve timestamps, clock meaning, frames, camera geometry, IMU values and completeness. Eight rows with four columns require tiny text on one page; two pages retain readable type. Reading only; no gate acceptance or hardware action.}
\end{frame}

\begin{frame}{What to learn before each gate}

{\small
\begin{tabular}{@{}L{45mm}L{47mm}L{43mm}L{51mm}@{}}\toprule
\textbf{Gate and its question} & \textbf{Concepts to understand first} & \textbf{One primary source to read} & \textbf{Self-check}\\\midrule
\textbf{N4.} Can we estimate motion on known data, camera replay, then live input? & Features; calibration; IMU preintegration; ground truth; ATE and RPE. & Campos et al. (2021), ORB-SLAM3 paper. & Why does a good EuRoC score not qualify our camera or live speed?\\[4pt]
\textbf{N5.} Where do processing time and resources go? & Latency; queue growth; sample age; clock relationships; processor load. & ROS 2 tracing tutorial: measuring execution time. & How can fast processing still deliver an old pose?\\[4pt]
\textbf{N6.} Can we detect and handle an unusable pose? & Pose transforms in 3D; map resets; invalid or old measurements. & Barfoot, \emph{State Estimation for Robotics}: pose transforms. & Why must a new map origin be detected before using a pose?\\[4pt]
\textbf{N7.} Does controller integration behave safely? & Local deadlines; watchdog timeouts; fallback behavior. & STMicroelectronics STM32H7 independent watchdog training. & If the Pi stops sending poses, which safety loops must stay local?\\\bottomrule
\end{tabular}}

\note{Sources: \detokenize{slides_learn/BRIEF.md Revision 3; slides_progress/main.tex; slides_course/main.tex; docs/ORB_SLAM3_OFFLINE_PREPARATION.md; AGENTS.md}. Primary readings: Campos et al. 2021; official ROS 2 tracing tutorial; Barfoot State Estimation for Robotics second edition, pose/SE(3) material; ST STM32H7 independent watchdog training. N4 groups N4A EuRoC, N4B D435i offline and N4C live; N4A does not need camera acquisition. Supplementary calibration and evaluation readings on references page. N5 remains timing/resources, not trajectory evaluation. ROS tracing teaches callback duration, not automatically sensor-to-controller latency or direct-SDK timing. Barfoot teaches transforms, not a complete N6 health protocol. ST teaches watchdog mechanisms, not an approved safety procedure; MCU reset is not asserted to maintain balance. Self-check answers: N4 known recordings do not validate our hardware/calibration or live scheduling; N5 queues hold old input; N6 a changed origin invalidates consumer continuity assumptions; N7 body IMU, balance loop, motor limits and watchdog/fallback stay on STM32H7. No interface, message, safety policy, budget or runtime change.}
\end{frame}

'''
anchor=r'\begin{frame}{These terms summarize the ideas you have learned}'
assert s.count(anchor)==1
s=s.replace(anchor,learning+anchor)
start=s.index(r'\begin{frame}{The sources separate project evidence from general methods}')
references=r'''\begin{frame}{The sources separate project evidence from general methods}

{\small
\textbf{Project evidence.} October 13 session facts and October 14 addendum; three-run evaluation; calibration notes; course, progress and report decks. Page notes hold detailed provenance.\par\medskip
\begin{columns}[T,onlytextwidth]
\begin{column}{.48\textwidth}
\textbf{Power and USB.} Raspberry Pi \href{https://www.raspberrypi.com/documentation/computers/raspberry-pi.html}{hardware docs}: power and cooling. RealSense \href{https://github.com/realsenseai/librealsense/wiki/Troubleshooting-Q\%26A}{librealsense troubleshooting}: USB access.\par\medskip
\textbf{ROS 2.} Official \href{https://docs.ros.org/en/jazzy/Tutorials.html}{Jazzy tutorials}: topics, QoS, tf2 and bags; \href{https://docs.ros.org/en/jazzy/Tutorials/Advanced/ROS2-Tracing-Trace-and-Analyze.html}{tracing tutorial}: execution time.\par\medskip
\textbf{SLAM and data.} Campos et al. (2021), \href{https://arxiv.org/abs/2007.11898}{ORB-SLAM3}, including Table II. Burri et al. (2016), \href{https://projects.asl.ethz.ch/datasets/doku.php?id=kmavvisualinertialdatasets}{EuRoC datasets}.\par\medskip
\textbf{Calibration and noise.} Furgale et al. (2013), \href{https://github.com/ethz-asl/kalibr/wiki}{Unified Temporal and Spatial Calibration}. Kalibr \href{https://github.com/ethz-asl/kalibr/wiki/camera-imu-calibration}{camera--IMU guide} and \href{https://github.com/ethz-asl/kalibr/wiki/IMU-Noise-Model}{IMU noise model}, including Allan analysis.\par
\end{column}
\begin{column}{.48\textwidth}
\textbf{Inertial estimation.} Forster et al. (2017), \href{https://arxiv.org/abs/1512.02363}{On-Manifold Preintegration for Real-Time Visual-Inertial Odometry}.\par\medskip
\textbf{Trajectory evaluation.} Sturm et al. (2012), \href{https://cvg.cit.tum.de/data/datasets/rgbd-dataset}{RGB-D SLAM benchmark}: ATE and RPE. Zhang and Scaramuzza (2018), \href{https://rpg.ifi.uzh.ch/docs/IROS18_Zhang.pdf}{quantitative trajectory evaluation tutorial}. Maintainer's \href{https://github.com/MichaelGrupp/evo/wiki/Metrics}{evo metric guide}.\par\medskip
\textbf{Frames and safe use.} Barfoot, \href{https://asrl.utias.utoronto.ca/~tdb/bib/barfoot_ser24.pdf}{State Estimation for Robotics}, second edition: 3D pose transforms, called SE(3). ST \href{https://www.st.com/content/st_com/en/support/learning/stm32-online-training/stm32h7-online-training.html}{STM32H7 watchdog training}.\par\medskip
\textbf{Images.} Reused course illustrations are conceptual; new diagrams are schematic. Worked numbers are illustrative.\par
\end{column}
\end{columns}}
\note{Sources: \detokenize{experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md; experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md; slides_course/qa/n4a-traj-eval-summary.md; docs/D435I_VIO_CALIBRATION_READINESS.md; slides_course/main.tex; slides_progress/main.tex; slides_report/main.tex; slides_learn/BRIEF.md Revision 3}. Primary references checked 14 October 2026. Furgale, Rehder and Siegwart: Unified Temporal and Spatial Calibration for Multi-Sensor Systems, IROS 2013 (Kalibr bibliography). Forster, Carlone, Dellaert and Scaramuzza: IEEE Transactions on Robotics 2017; linked preprint submitted 2015. Sturm et al.: A Benchmark for the Evaluation of RGB-D SLAM Systems, IROS 2012. Zhang and Scaramuzza: A Tutorial on Quantitative Trajectory Evaluation for Visual(-Inertial) Odometry, IROS 2018. Barfoot second edition 2024; linked author's updated draft compiled September 2026. ROS docs web access blocked by Anubis; content verified against official ros2/ros2\_documentation jazzy source and ROS documentation mirror. ST training contains Independent watchdog (IWDG); this reading supplies mechanisms, not a WBR safety approval. Camera methods are background reading; no camera command authorized. Theme and assets unchanged. Sources are not gate acceptance.}
\end{frame}
\end{document}
'''
(root/'main.tex').write_text(s[:start]+references)
print('Added two learning frames; updated the existing references frame.')
