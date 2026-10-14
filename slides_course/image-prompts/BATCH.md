# WBR illustration batch — P01–P12

Phase 1 deliverable. These are conceptual teaching illustrations, not photographs, CAD drawings, verified wiring, experiments or results. Technical architecture/data paths/transform trees/clocks/timing/queues/gates/state machines/boundary fields remain exact TikZ in Phase 2.

## Generation and download workflow

Paste the STYLE GUIDE and HARDWARE REFERENCE blocks below into ChatGPT once; request acknowledgement without generating an image. Then send the fenced P01 prompt, one prompt per message, in strict P-id order through P12. Never send “continue” or several prompts at once. If a subject repeats, start a new chat with the same setup and resend the explicit P-id prompt.

Download each image into `slides_course/images/` **without renaming** (for example `ChatGPT Image Oct 10, 2026, 03_12_45 PM.png`). Keep one accepted download per P-id in chronological order; do not mix unrelated/rejected generations into that folder. In Phase 2, `images/assign.py` will map unassigned ChatGPT-named files by filename timestamp, falling back to mtime, to the next missing P-ids, copy into Pxx.png without overwriting originals/existing slots, and print each mapping. Inspect subject/hardware against the table before accepting the mapping; chronology is not visual verification. Missing Pxx assets must compile as visible named placeholders. No image generation or assign.py implementation is part of Phase 1.

## STYLE GUIDE

```text
Use a consistent flat editorial technical illustration style for an academic engineering deck. Off-white background #FAFAF7; navy #1F3A5F outlines and structure, teal #2A9D8F emphasis, ink #22262B, muted gray #6B7280, light gray #D6D9DE. Orange #E76F51 appears only for an explicitly requested fault, never decoration. Hardware PCB green and metal silver may retain recognizable natural colors.
Clean simplified shapes, controlled shallow isometric perspective, generous whitespace around one strong subject; fill the wide image slot with readable hardware or scene detail. Crisp high-resolution raster, no photorealistic people, gradients, neon effects, dramatic lighting, logos, watermarks, signatures, fake tiny text or captions. Labels are optional and may only be the exact English strings listed by the P-id prompt, large and legible; prefer no text when it is not needed. Do not print the P-id itself inside the image.
Generate exactly one image per explicit P-id request, 16:9 landscape. Do not add frame borders, slide titles, page numbers, measurements, charts, pass marks, speed/rate readouts, debug screens, code or invented experiment outcomes. All scenes are conceptual/PLANNED. No exact circuit, wiring, protocol, clock, transform, queue or state diagrams: those will be drawn in TikZ separately.
```

## HARDWARE REFERENCE

```text
Raspberry Pi 5: recognizable green rectangular PCB, 40-pin header along a long edge, metal Ethernet connector, two blue USB3 Type-A ports and two USB2 Type-A ports, USB-C power and two small micro-HDMI connectors. Add a low-profile silver aluminum finned active cooler with a small dark blower/fan on top; preserve the board's port silhouette. NOT a blue Arduino PCB, NOT a Pi 4 label, NO full-size HDMI, NO laptop-sized GPU fan. The cooler is a reference illustration, not a claim about the owner's measured setup or exact installed fan model. Do not invent pin routing.
Intel RealSense D435i: compact horizontal silver/gray rounded camera bar, dark front face with separated stereo lens windows and other small optical apertures, USB-C connection. NOT a webcam ball, Kinect, T265 fisheye pair, lidar puck or DSLR. Use simplified visible apertures rather than inventing an exact optical drawing. Do not mark internal IMU location, lens specifications or precise dimensions as known. Vendor appearance reference only; this unit's archived SDK metadata reports BMI085, so do not label it BMI055.
Generic STM32H7 board: explicitly generic unbranded rectangular green/neutral PCB, one central square microcontroller package, modest headers and a small connector. Exact board model, package, pinout, dimensions and firmware are UNKNOWN. NOT an asserted Nucleo model, NOT a blue STM32F103 Blue Pill, NOT STM32F446RE from the OS deck. Label only STM32H7 when requested; do not show pin labels or electrical schematics.
Wheel-biped robot: conceptual compact torso with two articulated legs, one wheel at each foot, balanced left/right silhouette. No humanoid arms, quadruped, tracked chassis or four-wheel car. Camera can be shown on the torso only when requested. Link lengths, mass, actuator model, mounting dimensions, balance performance and wiring are UNKNOWN. This is a silhouette concept, not an existing prototype photograph.
Where connecting cables appear, draw generic insulated cables only; do not imply approved controller transport, pin assignment, verified power distribution or a deployed integration. Boards are spatially distinct and never a shared control chip. No motors shown moving during a lab qualification scene.
```

Hardware appearance sources: [official Pi 5](https://www.raspberrypi.com/products/raspberry-pi-5/) and [Active Cooler](https://www.raspberrypi.com/products/active-cooler/) verified 2026-10-10; [vendor camera comparison](https://www.realsenseai.com/compare-all-cameras/) and [Intel D435i specification record](https://www.intel.com/content/www/us/en/products/sku/190004/intel-realsense-depth-camera-d435i/specifications.html) located through primary search records. Direct D435i product fetch failed; avoid fine optical/dimension claims. STM32H7 board and robot are generic concepts, not externally verified models.

## P-id → page → subject

All slots are 16:9 wide; use roughly half-page column width, preserve aspect ratio and keep one scene per slot. Cover P01 may use a balanced right column. Exact slot heights will be checked during Phase 2 rendering.

| P-id | Page | Unique subject / argument | Aspect ratio | Assigned copy |
|---|---:|---|---|---|
| P01 | 1 | Platform portrait: the hardware objects that the guide concerns. | 16:9 | images/P01.png |
| P02 | 4 | Robot in a textured indoor route: why perception is useful. | 16:9 | images/P02.png |
| P03 | 10 | Camera motion through a textured scene: complementary visual/inertial cues. | 16:9 | images/P03.png |
| P04 | 12 | Isolated D435i portrait: identify the stereo sensor package. | 16:9 | images/P04.png |
| P05 | 19 | Pi cooling and supply bench: platform readiness requires physical care. | 16:9 | images/P05.png |
| P06 | 24 | Separate data storage on a bench: evidence needs qualified storage. | 16:9 | images/P06.png |
| P07 | 29 | Two sensor mounting contexts: camera IMU and body IMU stay distinct. | 16:9 | images/P07.png |
| P08 | 37 | Measured calibration target and guided motion scene. | 16:9 | images/P08.png |
| P09 | 51 | Preflight inspection bench: check before capture. | 16:9 | images/P09.png |
| P10 | 59 | Offline dataset analysis desk: frozen inputs separate algorithm diagnosis. | 16:9 | images/P10.png |
| P11 | 67 | Bounded agent work packet: tasks require evidence and stop conditions. | 16:9 | images/P11.png |
| P12 | 87 | Conditional journey with closed checkpoints: progress requires evidence. | 16:9 | images/P12.png |

## Individual prompts

### P01 — Platform portrait

```text
Generate exactly ONE image for P01.
ASPECT RATIO: 16:9 landscape, wide half-slide illustration.
Apply the STYLE GUIDE and HARDWARE REFERENCE above.
UNIQUE SUBJECT: Platform portrait.
COMPOSITION: Arrange a cooled Raspberry Pi 5, a D435i camera bar, a generic STM32H7 board and a small wheel-biped silhouette as four distinct objects in one balanced wide composition. The robot is subordinate to the hardware portrait.
MUST SHOW: All four recognizable objects; Pi active cooler; camera bar; generic controller; no connections implying deployed integration.
MUST NOT SHOW: P02 indoor navigation scene; P05 supply/cooling bench; P07 IMU mounting comparison; architecture arrows, wiring, charts, PASS marks.
ALLOWED LABELS ONLY: Raspberry Pi 5, D435i, STM32H7.
No added labels, P-id text, numbers, measurements, captions, watermarks or miniature text. This is a conceptual illustration, not experimental evidence.
```

### P02 — Textured indoor route

```text
Generate exactly ONE image for P02.
ASPECT RATIO: 16:9 landscape, wide half-slide illustration.
Apply the STYLE GUIDE and HARDWARE REFERENCE above.
UNIQUE SUBJECT: Textured indoor route.
COMPOSITION: Show a wheel-biped silhouette facing a short indoor route with textured walls, shelf edges and a simple obstacle. A small torso-mounted D435i faces the route; subtle teal viewing cone is illustrative only.
MUST SHOW: Exactly two articulated legs with foot wheels; visible natural scene texture and navigation relevance; calm grounded pose.
MUST NOT SHOW: P01 board collection; P03 camera-motion close-up; P08 calibration grid; path coordinates, measured trajectories, confirmed autonomous driving.
ALLOWED LABELS ONLY: None.
No added labels, P-id text, numbers, measurements, captions, watermarks or miniature text. This is a conceptual illustration, not experimental evidence.
```

### P03 — Visual and inertial motion cues

```text
Generate exactly ONE image for P03.
ASPECT RATIO: 16:9 landscape, wide half-slide illustration.
Apply the STYLE GUIDE and HARDWARE REFERENCE above.
UNIQUE SUBJECT: Visual and inertial motion cues.
COMPOSITION: Show a handheld D435i moving gently through a textured room. Two faint ghost positions and a simple curved motion cue suggest camera movement; emphasize stationary scene corners and changed viewpoint.
MUST SHOW: Camera moving relative to fixed texture; no robot; complementary visual scene and camera motion, no exact mathematical axes.
MUST NOT SHOW: P02 robot route; P04 isolated hardware portrait; P08 calibration target; inertial integration graph, pose output or internal IMU location.
ALLOWED LABELS ONLY: None.
No added labels, P-id text, numbers, measurements, captions, watermarks or miniature text. This is a conceptual illustration, not experimental evidence.
```

### P04 — D435i sensor portrait

```text
Generate exactly ONE image for P04.
ASPECT RATIO: 16:9 landscape, wide half-slide illustration.
Apply the STYLE GUIDE and HARDWARE REFERENCE above.
UNIQUE SUBJECT: D435i sensor portrait.
COMPOSITION: Show one large three-quarter front portrait of the horizontal silver/dark D435i camera bar with separated visible optical windows and a modest USB-C cable end, isolated on paper background.
MUST SHOW: Recognizable compact stereo camera bar filling the wide slot; two separated stereo lens windows, simplified remaining apertures.
MUST NOT SHOW: P01 hardware ensemble; P03 room motion; P07 dual-IMU robot; camera cutaway, hidden IMU placement, lens measurements or BMI055 label.
ALLOWED LABELS ONLY: D435i.
No added labels, P-id text, numbers, measurements, captions, watermarks or miniature text. This is a conceptual illustration, not experimental evidence.
```

### P05 — Platform supply and cooling

```text
Generate exactly ONE image for P05.
ASPECT RATIO: 16:9 landscape, wide half-slide illustration.
Apply the STYLE GUIDE and HARDWARE REFERENCE above.
UNIQUE SUBJECT: Platform supply and cooling.
COMPOSITION: Show only a Pi 5 on a clean bench with visible active cooler, a generic suitable USB-C supply block and cable strain relief. A small airflow cue conveys cooling without temperature values.
MUST SHOW: Green Pi; silver active cooler/dark fan; power connection visibly separate from unused USB-A data ports; no exact circuitry.
MUST NOT SHOW: P01 four-object portrait; P06 storage devices; P09 full preflight checklist; numerical voltage/current/temperature, oscilloscope results, approved supply model.
ALLOWED LABELS ONLY: Power, Cooling.
No added labels, P-id text, numbers, measurements, captions, watermarks or miniature text. This is a conceptual illustration, not experimental evidence.
```

### P06 — Separate research data storage

```text
Generate exactly ONE image for P06.
ASPECT RATIO: 16:9 landscape, wide half-slide illustration.
Apply the STYLE GUIDE and HARDWARE REFERENCE above.
UNIQUE SUBJECT: Separate research data storage.
COMPOSITION: Show a generic closed external NVMe enclosure beside a small microSD card and archival folder motif on a clean bench; enclosure visually dominant, microSD secondary. No computer board is necessary.
MUST SHOW: Distinct bulk-data enclosure and small operating-system card; conceptual separation without implying throughput qualification.
MUST NOT SHOW: P05 powered Pi cooling bench; P10 analysis laptop; photographed files, brand/model/serial/UUID labels, disks with capacity/speed numbers, PASS badge.
ALLOWED LABELS ONLY: Data, OS.
No added labels, P-id text, numbers, measurements, captions, watermarks or miniature text. This is a conceptual illustration, not experimental evidence.
```

### P07 — Separate camera and body sensor contexts

```text
Generate exactly ONE image for P07.
ASPECT RATIO: 16:9 landscape, wide half-slide illustration.
Apply the STYLE GUIDE and HARDWARE REFERENCE above.
UNIQUE SUBJECT: Separate camera and body sensor contexts.
COMPOSITION: Use one wheel-biped torso silhouette with a clearly external D435i mount, plus two large separate magnified context bubbles: camera package context and a generic torso-mounted body sensor/controller context.
MUST SHOW: Camera and body sensing visibly separate; generic STM32H7 board near body context; no shared internal sensor or exact installation claim.
MUST NOT SHOW: P01 loose hardware array; P04 isolated camera; P08 calibration scene; exact transform tree, axes, clock links, internal D435i IMU location or fusion arrows.
ALLOWED LABELS ONLY: Camera IMU, Body IMU.
No added labels, P-id text, numbers, measurements, captions, watermarks or miniature text. This is a conceptual illustration, not experimental evidence.
```

### P08 — Target-based calibration preparation

```text
Generate exactly ONE image for P08.
ASPECT RATIO: 16:9 landscape, wide half-slide illustration.
Apply the STYLE GUIDE and HARDWARE REFERENCE above.
UNIQUE SUBJECT: Target-based calibration preparation.
COMPOSITION: Show a fixed high-contrast AprilGrid-like target on a rigid flat board and a D435i held at an oblique viewpoint. A plain ruler lying beside target suggests dimensions must be measured, without scale numerals.
MUST SHOW: Fixed well-lit target, camera tilted relative to it, room for safe cable slack; a real calibration scene distinct from generic VIO motion.
MUST NOT SHOW: P03 textured-room camera motion alone; P09 preflight bench; fake decoded AprilTag ids, exact grid dimensions, corner residuals, successful calibration certificate.
ALLOWED LABELS ONLY: Calibration target.
No added labels, P-id text, numbers, measurements, captions, watermarks or miniature text. This is a conceptual illustration, not experimental evidence.
```

### P09 — Fresh preflight inspection

```text
Generate exactly ONE image for P09.
ASPECT RATIO: 16:9 landscape, wide half-slide illustration.
Apply the STYLE GUIDE and HARDWARE REFERENCE above.
UNIQUE SUBJECT: Fresh preflight inspection.
COMPOSITION: Show a powered-down-looking inspection bench with cooled Pi and D435i laid out, a short direct USB-A-to-USB-C data cable and a blank checklist sheet bearing empty boxes. No active data display.
MUST SHOW: Cable connectors distinguish power from camera data; careful physical inspection scene; every checklist box empty.
MUST NOT SHOW: P05 cooling-only close-up; P08 target; P10 dataset analysis; live sensor output, filled checks, 5000M readout, measurements or gate PASS.
ALLOWED LABELS ONLY: Preflight.
No added labels, P-id text, numbers, measurements, captions, watermarks or miniature text. This is a conceptual illustration, not experimental evidence.
```

### P10 — Offline analysis of frozen inputs

```text
Generate exactly ONE image for P10.
ASPECT RATIO: 16:9 landscape, wide half-slide illustration.
Apply the STYLE GUIDE and HARDWARE REFERENCE above.
UNIQUE SUBJECT: Offline analysis of frozen inputs.
COMPOSITION: Show a laptop workstation with one simple grayscale stereo image pair on screen, immutable-looking data folders and a magnifying-glass motif. No attached live camera or robot.
MUST SHOW: Two different left/right views of one textured scene; offline input inspection; screen contains images only, no generated code or result graph.
MUST NOT SHOW: P06 physical drive portrait; P09 live hardware bench; P11 ticket packet; fabricated terminal logs, measured trajectories, accuracy curves, PASS badges.
ALLOWED LABELS ONLY: Recorded input, Offline analysis.
No added labels, P-id text, numbers, measurements, captions, watermarks or miniature text. This is a conceptual illustration, not experimental evidence.
```

### P11 — Bounded engineering task packet

```text
Generate exactly ONE image for P11.
ASPECT RATIO: 16:9 landscape, wide half-slide illustration.
Apply the STYLE GUIDE and HARDWARE REFERENCE above.
UNIQUE SUBJECT: Bounded engineering task packet.
COMPOSITION: Show one organized work packet: three large paper cards and a small evidence folder, framed by a modest boundary outline. Only short approved headings, no body text or signatures.
MUST SHOW: Task, evidence and stop-condition cards visually equal; packet bounded and reviewable; no hardware or autonomous robot imagery.
MUST NOT SHOW: P10 laptop analysis; P12 checkpoint route; AI humanoid, fake code, approval signatures, completed checkmarks or manufactured test output.
ALLOWED LABELS ONLY: Task, Evidence, Stop condition.
No added labels, P-id text, numbers, measurements, captions, watermarks or miniature text. This is a conceptual illustration, not experimental evidence.
```

### P12 — Conditional evidence journey

```text
Generate exactly ONE image for P12.
ASPECT RATIO: 16:9 landscape, wide half-slide illustration.
Apply the STYLE GUIDE and HARDWARE REFERENCE above.
UNIQUE SUBJECT: Conditional evidence journey.
COMPOSITION: Show a conceptual gently ascending path with a few clearly closed neutral checkpoint barriers toward a distant wheel-biped silhouette. Gates stay unnumbered; no exact gate ladder or flowchart.
MUST SHOW: Closed checkpoints and restrained robot destination; sense of conditional progress; no checkpoint shown completed.
MUST NOT SHOW: P02 room navigation; P11 paper tickets; exact N0–N7 labels/arrows/timelines, open passed gates, finish trophy, deadline or measured progress.
ALLOWED LABELS ONLY: Next gate.
No added labels, P-id text, numbers, measurements, captions, watermarks or miniature text. This is a conceptual illustration, not experimental evidence.
```

## Prompt review

Twelve distinct subjects are mapped to twelve unique pages. P01 identifies the platform; P02 motivates navigation; P03 explains motion cues; P04 isolates the camera; P05 explains physical platform care; P06 explains storage separation; P07 distinguishes IMUs; P08 depicts calibration preparation; P09 depicts fresh preflight; P10 depicts offline inspection; P11 explains ticket boundaries; P12 depicts conditional progress. Neighbor exclusions prevent repeated board collages, camera scenes or bench scenes. Technical diagrams and measured plots are deliberately absent. Every image must be visually checked after download; prompts cannot certify generator accuracy.
