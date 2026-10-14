# Reader review of the existing 45-page deck

Date: 14 October 2026. I read every preview image in order, pages 1–45, as a fourth-year electronics student familiar with ADCs, timers, embedded C and Linux but new to SLAM. This is a simulated reader review by the assistant, not evidence from a real student. The previous review and input deck are preserved in `qa/reader-review-before/`.

The sequence is understandable, and the stereo and ATE calculations are helpful. No clipping or overlapping text was visible in the input images. The unclear pages follow; each entry quotes the input deck before revision.

| Page | Exact sentence or term that lost me | What I needed |
|---|---|---|
| 8 | “specific force: acceleration relative to free fall”; “Integrating a small bias repeatedly can create a growing motion error.” | Compare a table-resting accelerometer with free fall. Show that each integration time step adds false angle from gyro bias. |
| 11 | “A transform converts coordinates between frames by rotating the axes and shifting the origin.” | One numerical conversion for the same corner relative to camera and torso. |
| 13 | “An offset relates their origins; clock-rate drift changes that relationship over time.” | Calculate the offset from the pictured readings; explain why one paired event cannot measure rate drift. |
| 15 | “ORB features describe such regions with compact bit patterns that software can compare.” | Explain where the bits come from and why similar signatures are only candidate matches. |
| 17 | “The map and the camera poses help constrain each other.” | Follow our corner: stereo locates it in 3D, then observing it again helps locate the camera. |
| 18 | “Varied motion helps distinguish these unknowns”; “inertial drift” | Explain what varies, which unknowns must be separated, and what drift means before the next page uses it. |
| 19 | “Old places”; “these two visits should refer to the same scene” | Say that the thread recognizes places and that both visits should put the table in the same map location. |
| 22 | “the image center sets the origin” | Define the principal point as the optical axis meeting the image; it need not be exactly at the image center. |
| 23 | “Default values and a warning about unavailable IMU calibration do not become measured calibration.” | Explain that assumed parameters need measurement before trust; preserve the underlying warning. |
| 26 | “A node is a participating program; a topic is a named channel carrying a defined message type.” | Explain who sends and receives our image, using publishing and subscribing. |
| 27 | “The ROS 2 path is driver, topics, then a rosbag2 recording”; “The two bag paths need separate compatibility checks.” | Explain how replay reaches SLAM. Recording alone does not supply a SLAM input program. Say whether one route's recording is readable by the other. |
| 28 | “current direct SDK adapter” | Use the already explained librealsense input program rather than another component name. |
| 33 | “MH01 comparator”; “three-run mean and paper ten-run median”; “native build”; “The full protocols are not proven identical.” | Identify the paper and score, explain median as the middle result, and say executable running on the Pi. Make the comparison limits plain. |
| 36 | “sensor qualification, a reviewed stereo extension and calibration review”; “not a silent change to the baseline”; “qualifying the live system” | Explain the concrete order and why a second stream needs another delivery test. Preserve the one-stream N2 baseline. |
| 37 | “from a restarted map” | Explain that restarting can change the world origin even when the pose looks plausible. |
| 39 | “qualify the platform and delivery”; “health behavior” | Recap with familiar words: check the computer and delivery, detect unusable poses, and check safe controller use. |
| 40 | “initialized trajectories”; “No gate has been accepted for the current setup”; “Camera-dependent work waits for the owner's explicit CAMERA AVAILABLE authorization.” | Connect initialization to the IMU definition; state remaining checks and the camera requirement directly. |
| 41 | “unqualified camera pipeline”; “Brief a collaborator ... the condition that should stop the work.” | Ask what the camera still needs to prove and which failed measurement stops the next test. |
| 42 | “A kept viewpoint and an estimated scene point.” | Keep the keyframe definition consistent: a stored image and its pose. |
| 44 | “Future offline scoring shape” | Say example command for scoring saved trajectories. Commands and paths are appropriate in this appendix. |

Pages 1–7, 9–10, 12, 14, 16, 20–21, 24–25, 29–32, 34–35, 38, 43 and 45 were clear on this pass. Page 7's drawing is schematic; its stated disparity calculation is clear. Page 32 distinguishes segment error from an error rate. Reading these pages does not establish comprehension by an actual student.

## Wording that sounds like a log between agents

“MH01 comparator,” “The full protocols are not proven identical,” “current direct SDK adapter,” “reviewed stereo extension,” “not a silent change to the baseline,” “No gate has been accepted,” “unqualified camera pipeline,” and “Future offline scoring shape” describe internal review machinery. The calibration takeaway reads like an audit verdict rather than explaining the measurement still needed. The CAMERA AVAILABLE requirement must remain, but its surrounding sentence can address a person directly.

No evidence keys, commit hashes or paths appear on teaching pages. Notes and the references page appropriately carry provenance. The dated status page is useful and its facts should remain unchanged. Explained gate IDs serve a purpose and should stay.

## The five most important fixes

1. Explain IMU readings, initialization and drift with stationary/free-fall and time-step examples; follow the corner through map improvement and loop closure (pages 8, 17–19).
2. Work one illustrative frame conversion and clock offset; clarify the camera principal point (pages 11, 13, 22).
3. Explain binary feature signatures and how multiple matches support one motion (page 15).
4. Trace publishing, subscribing, recording and SLAM input; explain the distinct ROS and librealsense recording readers (pages 26–28).
5. Replace handoff wording with plain explanations of results, remaining checks and next tests; preserve measured scores, warnings and requirements (pages 22–23, 33, 36–37, 39–42, 44).
