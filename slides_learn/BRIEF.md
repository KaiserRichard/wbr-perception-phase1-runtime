# Brief: deck D — "How WBR perception works" (a teaching deck for a human reader)

Builder rules: work ONLY inside `slides_learn/`. Read anything in the repo; edit nothing outside
this folder. No git commands that change index/branches/commits. English only.

## Why this deck exists
The owner read the 44-page progress deck (`slides_progress/main.pdf`) and said it reads like a
log passed between AI agents, not something a person can learn from. Look at its pages to see
what to avoid: status labels on every page (MEASURED / OPEN / CALCULATED), evidence file paths,
source keys like "[F] sections A–F", "Reference deck p. 48–52", command lines, dense
abbreviations (IR1 Y8 640x480/15, OPEN_DIAGNOSTIC, sealed receipts, accept-n2), thresholds with
no explanation of why they exist, and sentences that compress three ideas into one line.

The reader is a 4th-year electronics/telecom student: strong in circuits, embedded C, STM32,
UART/timers/interrupts, Linux basics. New to computer vision, SLAM, visual-inertial odometry,
ROS 2 and trajectory evaluation. After this deck they must be able to explain, in their own
words, how the whole system works and why the project is ordered the way it is, so they can
make decisions and brief AI agents.

## Writing rules (these matter more than anything else)
- Write like a good lecturer's slides: one idea per page, a title that is a plain sentence
  stating that idea, then the explanation. Explain WHY before WHAT, and WHAT before HOW.
- Build from what the reader already knows (sampling, clocks, ADC noise, timers, interrupts,
  UART framing, control loops) to the new concepts. Use analogies to embedded systems where
  they are accurate.
- Use one running example through the deck: a single moment where the camera captures a
  stereo image pair and the IMU produces samples, followed through USB, the driver, ROS 2, the
  bag file, ORB-SLAM3, to a pose, and then scored against ground truth.
- Every new term is defined in plain words the first time it appears, with a picture when it
  has one (stereo disparity, feature matching, keyframe, map point, IMU preintegration, bias,
  coordinate frame, transform, timestamp, clock domain, ATE, RPE, alignment).
- Full sentences. Short paragraphs or at most 3–4 bullets. No slash-separated jargon chains.
- No file paths, evidence keys, commit hashes, command lines or tool flags on content pages.
  Sources go in `\note{}` and in one references page at the end. Commands only in an appendix.
- Status labels: only where the reader needs them, in words ("this has been measured",
  "this is planned, not done yet"). One "Where we are today" page carries the status.
- Numbers only when they teach something, and each number comes with what it means
  (e.g. "4 cm of error after a 184-second flight through an 80-metre path" style framing, but
  only with numbers that exist in the sources).
- Diagrams in TikZ: large, few labels, each label a real word. Prefer worked examples
  (e.g. compute stereo depth from baseline 5 cm and a disparity; compute one ATE residual) to
  abstract boxes. Mark example numbers clearly as illustrative.
- End each part with a one-page recap: "what you should now be able to explain".

## Content (about 35–45 pages, adjust to what teaches best)
0. Cover; a one-page map of the deck.
1. The problem: what a wheel-biped robot needs to know about its own motion and surroundings,
   and why the robot must stay balanced even if perception fails (Pi vs STM32H7 split, explained
   like an embedded engineer would: hard real-time loop vs best-effort computer).
2. The sensors: the D435i as two infrared cameras plus an IMU; how stereo gives depth; what a
   gyro and accelerometer measure, their noise and bias; why the IR projector is turned off.
3. Time and space: coordinate frames and transforms (with the robot picture), why every
   measurement needs a timestamp, different clocks on the camera, Pi and STM32 and why you
   cannot subtract times from different clocks.
4. How visual-inertial SLAM works: features, matching, tracking, keyframes, the map, why the
   IMU helps (fast motion, scale, gravity), IMU initialisation, loop closing. ORB-SLAM3's three
   threads as a simple picture. Why it fails (blur, no texture, wrong calibration, bad time).
5. Calibration: what intrinsics, extrinsics, camera–IMU time offset and IMU noise are, why
   factory values are only a start, and which tools are used later.
6. The software path: librealsense, ROS 2 topics, recording and replaying a bag, offline vs
   live, why record first.
7. How we know it works: ground truth, EuRoC, ATE and RPE with worked pictures; what our three
   EuRoC runs (about 4 cm ATE vs about 3.6 cm in the paper, RPE about 1.3 cm per second) do and
   do not tell us.
8. The plan as a story: the gate ladder N0–N7, each gate in one sentence of "what question it
   answers" and "why it comes before the next one". Bottom-up debugging order with why.
9. Where we are today (single status page) and what comes next, in plain words.
10. Appendix: glossary; tool list (one line each); command cheat-sheet; references.

## Sources (facts must come from these; do not invent)
`slides_course/main.tex` (the 91-page reference deck), `slides_progress/main.tex`,
`slides_report/main.tex`, `experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md`,
`slides_course/qa/n4a-traj-eval-summary.md`, `docs/*.md`. General textbook facts (stereo
geometry, IMU models, ORB-SLAM3 design from Campos et al. 2021, EuRoC from Burri et al. 2016)
may be explained in your own words; cite them on the references page.

## Style
Same preamble/theme/palette/fonts as `slides_course/main.tex` (copy it), but a lighter page
design: more whitespace, larger figures, fewer boxes. Images: reuse `slides_course/images/P03.png`,
`P04.png`, `P05.png`, `P08.png`, `P10.png` where they genuinely help. Do not use P01, P02, P07,
P12 (they show a wheeled cart, not a wheel-biped). Never generate images. If a new
illustration is truly needed, use a named placeholder and add a prompt to
`image-prompts/BATCH.md` (format of `slides_course/image-prompts/BATCH.md`; the robot must be
a wheel-biped: torso on two articulated legs with a wheel at each foot).

## Build, then a reader test
1. Build `cd slides_learn && latexmk -xelatex -interaction=nonstopmode main.tex`; render with
   `swift -module-cache-path qa/swift-cache ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview`.
2. Read every page image as the target student would. For each page ask: could they explain this
   page aloud after reading it once? Is any term used before it is defined? Is there any agent
   jargon, path, label noise or compressed sentence? Fix and repeat.
3. Layout QA as usual (overflow, overlaps, tiny text). Write REVIEW_LOG.md ending "FINAL".

## REVISION 2: 2026-10-14 facts and small fixes
1. Update every status statement with `experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md`: 8 GB Pi
   now in use, camera streams correctly, microSD too slow for 18.4 MB/s so recording goes into
   RAM first (explain why in plain words with a small picture: a writer that cannot keep up,
   the buffer fills, frames are dropped), the offline ORB-SLAM3 crash and its fix (explain an
   uninitialised pointer in embedded terms), power still not fixed.
2. Page 8: the "Unbiased reference" label touches the noise curve; fix the diagram.
3. Keep the teaching style of BRIEF.md. Rebuild, render, inspect changed pages, log "REVISION 2 FINAL".

## REVISION 3: "What to learn before each gate" (owner request)
Add ONE page (two only if it cannot be read on one) near the end of the main part, before the
appendix, titled "What to learn before each gate". A table: Gate (N0–N7, with the one question
each gate answers in plain words) | Concepts to understand first | One primary source to read
(e.g. Raspberry Pi power/throttling docs; USB 3 basics and librealsense docs; Allan variance /
IMU noise; ROS 2 tutorials on topics, QoS, tf2, rosbag2; ORB-SLAM3 paper (Campos et al. 2021)
and EuRoC paper (Burri et al. 2016); Kalibr papers (Furgale et al. 2013) and IMU preintegration
(Forster et al. 2017); evo / ATE-RPE (Sturm et al. 2012, Zhang & Scaramuzza 2018); Barfoot,
State Estimation for Robotics, for SE(3)) | Self-check (one question the owner should be able to
answer before starting the gate). Keep it readable: short phrases, no paths or commands. Also
add these sources to the references page. Rebuild, render, inspect the new page(s) and the
references page, log "REVISION 3 FINAL".

## REVISION 4: the infrared projector, around page 9 (owner request)
The owner did not understand page 9 ("why the IR projector is turned off") and needed an outside
explanation. Add 1–2 new slides right after the current page 9 (do not crowd page 9 itself):
1. What the projector does: the D435i has a left IR camera, a right IR camera and an IR projector.
   The projector produces no image; it shines an invisible dot pattern onto surfaces so the two IR
   cameras see texture even on a plain white wall. Small illustration: white wall seen with
   projector OFF (featureless) vs ON (illustrative dots). You may reuse `slides_course/images/P04.png`.
2. Why dots help depth: stereo disparity d, depth Z = f·b/d (f focal length in pixels, b baseline
   ≈ 5 cm on our unit per the config, d disparity in pixels); on a plain wall matching fails, dots
   make matching possible.
3. The key diagram (TikZ, side by side, two camera positions t1 and t2 with arrows): LEFT panel
   "Physical table corner": the corner is fixed in the room; as the D435i moves right, the corner's
   pixel position changes in the image but the corner itself does not move. RIGHT panel "Projected IR
   dot": the projector is rigidly attached to the camera, so the dot pattern is fixed relative to the
   camera, not to the world; when the camera moves, the lit spot slides across the table surface.
   Label world positions and image positions clearly.
4. Why that matters: ORB-SLAM3 assumes matched features are static points in the world; tracking a
   dot that moves with the camera gives wrong motion. Summary table: Stereo depth on textureless
   surfaces → projector often helpful; ORB-SLAM3 feature tracking → potentially misleading; our first
   natural-feature SLAM tests → OFF. Note: this is an experimental choice, not a universal rule; we can
   later compare ON vs OFF by tracking quality and depth. End with the check question: "If the D435i
   moves right, does the table corner move in the room, or only in the image?"
Keep the deck's teaching style and look. Update any page references and the reading map for the
shift. Rebuild, render, inspect the new slides and their neighbours at full size, fix visual or
technical issues, log "REVISION 4 FINAL".

## REVISION 5: polish page 11 (corner vs dot diagram)
Page 11 is too crowded: the "Moves right" labels sit on top of the camera boxes and arrow, "Same
world point" collides with the dashed sight line, and the green/orange captions crowd the image
boxes. Give the diagram more vertical room (move the summary table and the note to a cleaner
layout, or split the table onto page 12 if needed), place "Moves right" above the arrow with clear
space, and keep every label clear of lines. Keep the content and the check question. Rebuild,
render, inspect pages 10–12 at full size, log "REVISION 5 FINAL".
