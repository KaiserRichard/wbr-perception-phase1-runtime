# Final PDF page inventory

| Page | Title | Evidence |
|---|---|---|
| 1 | WBR perception: understand, record, explain | KNOWN ownership / all gates OPEN |
| 2 | How to study this deck | KNOWN method |
| 3 | What an evidence label means | KNOWN method |
| 4 | System ownership: why WBR needs two computers | KNOWN method |
| 5 | Camera IMU and body IMU have different jobs | KNOWN method |
| 6 | Ownership: worked stale-input example | CALCULATED illustrative; no WBR age budget |
| 7 | Ownership: common mistake and check yourself | KNOWN method |
| 8 | D435i inputs and the identity that matters | MEASURED archived identity / fresh readback OPEN |
| 9 | Two stream profiles: never merge their evidence | SOURCE-SUPPORTED profiles / qualification OPEN |
| 10 | USB and power: inspect the camera branch | MEASURED historical / SOURCE-SUPPORTED requirement |
| 11 | Storage: calculate the payload before recording | CALCULATED payload / MEASURED USB-stick rate |
| 12 | Hardware: common mistake and check yourself | KNOWN method |
| 13 | Stereo geometry: two views constrain depth | KNOWN method |
| 14 | Stereo: worked depth and disparity | MEASURED readback / CALCULATED example |
| 15 | Stereo: small disparity makes distant depth fragile | CALCULATED first-order illustrative error |
| 16 | Stereo: common mistake and check yourself | KNOWN method |
| 17 | IMU model: what the two channels measure | KNOWN method |
| 18 | Visual-inertial prediction bridges image intervals | KNOWN method |
| 19 | IMU: worked bias and noise scaling | CALCULATED illustrative / ASSUMED candidate noise |
| 20 | Allan deviation: choose the supported region | KNOWN method |
| 21 | Allan: common mistake and check yourself | KNOWN method |
| 22 | Frames: axes and the pose origin | KNOWN method |
| 23 | Transforms: write the direction as an equation | KNOWN method |
| 24 | Transforms: worked rotated lever arm | CALCULATED illustrative |
| 25 | Frames: common mistake and check yourself | KNOWN method |
| 26 | Timestamp chain: every kind has an owner | KNOWN method |
| 27 | Timestamp chain: processing, bag and output | KNOWN method |
| 28 | Clocks: worked same-clock latency | CALCULATED illustrative |
| 29 | Clocks: common mistake and check yourself | KNOWN method |
| 30 | ROS 2: graph, typed topics and QoS | KNOWN method |
| 31 | QoS: compatibility before counting frames | KNOWN method |
| 32 | ROS topics: explicit sensor names | SOURCE-SUPPORTED names / observed graph OPEN |
| 33 | ROS bags: a durable record is an experiment input | KNOWN method |
| 34 | ROS: worked queue and common mistake | CALCULATED illustrative / KNOWN ROS semantics |
| 35 | Calibration: four questions, four evidence types | KNOWN method |
| 36 | Intrinsics and stereo: validate the operating model | MEASURED readback / ASSUMED operating choice |
| 37 | Measured target: a 6×4 printable AprilGrid | SOURCE-SUPPORTED target / measured dimensions OPEN |
| 38 | Camera–IMU calibration: excite observable motion | KNOWN method |
| 39 | Kalibr transform: worked inversion | SOURCE-SUPPORTED convention / CALCULATED example |
| 40 | Kalibr time: worked sign and application boundary | SOURCE-SUPPORTED sign / CALCULATED illustrative |
| 41 | Calibration: proposed review thresholds | ASSUMED from current calibration plan |
| 42 | Calibration: common mistake and check yourself | KNOWN method |
| 43 | ORB-SLAM3: work shared across threads | KNOWN method |
| 44 | Tracking: account for every image interval | KNOWN method |
| 45 | Initialization: stereo scale does not solve everything | KNOWN method |
| 46 | Association: worked interpolation | CALCULATED illustrative |
| 47 | ORB: common mistake and check yourself | KNOWN method |
| 48 | Gate ladder: prerequisites remain OPEN | SOURCE-SUPPORTED current project state |
| 49 | Gate ladder: measurement and controller boundary | OPEN / N5–N7 not started |
| 50 | N2 thresholds stay exactly as specified | SOURCE-SUPPORTED gate criteria |
| 51 | Dated evidence: what the sources actually establish | MEASURED source-reported diagnostics / all gates OPEN |
| 52 | Gate example, common mistake and check yourself | KNOWN method |
| 53 | Evaluation: the measured EuRoC MH01 baseline | MEASURED historical / N4A OPEN |
| 54 | ATE: worked RMS after a declared alignment | CALCULATED illustrative |
| 55 | RPE: relative pose error over a fixed interval | CALCULATED illustrative / historical RPE UNVERIFIED |
| 56 | Without ground truth: useful proxies have limits | ASSUMED review protocol / accuracy UNKNOWN |
| 57 | Evaluation: common mistake and check yourself | KNOWN method |
| 58 | Pi↔STM32 link: integrity before semantics | KNOWN method |
| 59 | UART: worked serialization floors | CALCULATED from source framing |
| 60 | CN/OS supervisor states and recovery | SOURCE-SUPPORTED OS integration / hardware UNTESTED |
| 61 | Link and supervision: common mistake and check yourself | KNOWN method |
| 62 | Lab operating contract | ASSUMED time budget / SOURCE-SUPPORTED stop rules |
| 63 | Packing checklist | SOURCE-SUPPORTED packing / availability to verify |
| 64 | Stop rules: the earliest failed layer wins | SOURCE-SUPPORTED prerequisites / ASSUMED one-retry policy |
| 65 | Session 1 timeline: 150 min maximum | ASSUMED wall-time budget |
| 66 | Before lab: prepare, do not improvise | SOURCE-SUPPORTED runbook / readiness OPEN |
| 67 | P0 / Bind prepared paths and verify tools | SOURCE-SUPPORTED procedure / execution OPEN |
| 68 | P0 / Mac / before lab (1/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 69 | P0 / Pi / each shell (2/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 70 | S1.0 / Set up and make the evidence manifest | SOURCE-SUPPORTED procedure / execution OPEN |
| 71 | S1.0 / Pi / control (1/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 72 | S1.0 / Mac / canonical checkout (2/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 73 | S1.1 / Power and storage preflight | SOURCE-SUPPORTED procedure / execution OPEN |
| 74 | S1.1 / Pi / control (1/1) | SOURCE-SUPPORTED procedure / execution OPEN |
| 75 | S1.2 / USB, serial and fresh N1 | SOURCE-SUPPORTED procedure / execution OPEN |
| 76 | S1.2 / Pi / control (1/1) | SOURCE-SUPPORTED procedure / execution OPEN |
| 77 | S1.3 / Exact N2 acquisition: inspect each stage | SOURCE-SUPPORTED procedure / execution OPEN |
| 78 | S1.3 / Pi / gate bundle, stage 1 (1/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 79 | S1.3 / Pi / only after prior stage review (2/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 80 | S1.3R / Human N2 review and acceptance | SOURCE-SUPPORTED procedure / execution OPEN |
| 81 | S1.3R / Pi / after actual review (1/1) | SOURCE-SUPPORTED procedure / execution OPEN |
| 82 | S1.4 / Active N3: baseline record and replay | SOURCE-SUPPORTED procedure / execution OPEN |
| 83 | S1.4 / Pi / prepared bundle (1/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 84 | S1.4 / Pi / after live camera has stopped (2/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 85 | Record contract: one device owner, explicit representations | SOURCE-SUPPORTED ownership / conversion gaps OPEN |
| 86 | S1.5 / ROS recipe shared by S, C1–C3 and A | SOURCE-SUPPORTED procedure / execution OPEN |
| 87 | S1.5 / Pi / camera terminal A (1/5) | SOURCE-SUPPORTED procedure / execution OPEN |
| 88 | S1.5 / Pi / control terminal B (2/5) | SOURCE-SUPPORTED procedure / execution OPEN |
| 89 | S1.5 / Pi / topic selection terminal B (3/5) | SOURCE-SUPPORTED procedure / execution OPEN |
| 90 | S1.5 / Pi / recorder terminal B, same shell (4/5) | SOURCE-SUPPORTED procedure / execution OPEN |
| 91 | S1.5 / Pi / telemetry terminal C, during each take (5/5) | SOURCE-SUPPORTED procedure / execution OPEN |
| 92 | S1.5F / Finalize, hash and preserve each ROS take | SOURCE-SUPPORTED procedure / execution OPEN |
| 93 | S1.5F / Pi / after finalization (1/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 94 | S1.5F / Mac / after all writers stop (2/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 95 | S1.6 / S stereo take: static intervals then coverage | SOURCE-SUPPORTED procedure / execution OPEN |
| 96 | S1.6 / Pi / ROS control before S1.5 (1/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 97 | S1.6 / Pi / OPTIONAL native replica, ROS stopped (2/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 98 | S1.7 / C1–C3 camera–IMU takes | SOURCE-SUPPORTED procedure / execution OPEN |
| 99 | S1.7 / Pi / ROS control, each take separately (1/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 100 | S1.7 / Pi / OPTIONAL native replicas, ROS stopped (2/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 101 | S1.8 / Allan pilot and between-session long recording | SOURCE-SUPPORTED procedure / execution OPEN |
| 102 | S1.8 / Pi / ROS camera terminal, replace stereo launch (1/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 103 | S1.8 / Pi / native alternative, BLOCKED pending companion (2/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 104 | S1.8R / Allan ROS recording: explicit IMU-only bag | SOURCE-SUPPORTED procedure / execution OPEN |
| 105 | S1.8R / Pi / recorder terminal B (1/1) | SOURCE-SUPPORTED procedure / execution OPEN |
| 106 | S1.9 / Step 9b link bench: wire and check | SOURCE-SUPPORTED procedure / execution OPEN |
| 107 | S1.9 / Mac / before wiring, prepared binary (1/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 108 | S1.9 / Pi / control, camera unplugged (2/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 109 | S1.9T / Step 9b timeouts and optional 9c | SOURCE-SUPPORTED procedure / execution OPEN |
| 110 | S1.9T / Pi / only after analyzer capture starts (1/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 111 | S1.9T / Mac / after copying capture and summary (2/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 112 | S1.10 / Session handoff: stop at 150 minutes | SOURCE-SUPPORTED procedure / execution OPEN |
| 113 | S1.10 / Mac / copy small logs too (1/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 114 | S1.10 / Mac / completed native or bench branches only (2/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 115 | Session 2 timeline: 150 min maximum | ASSUMED wall-time budget |
| 116 | S2.0 / Rerun only the earliest failed S1 condition | SOURCE-SUPPORTED procedure / execution OPEN |
| 117 | S2.0 / Pi / control, fresh bindings (1/1) | SOURCE-SUPPORTED procedure / execution OPEN |
| 118 | S2.1 / CN/OS integration: E6 two-Pi edge offloading | SOURCE-SUPPORTED procedure / execution OPEN |
| 119 | S2.1 / 8 GB server B / ~/CN prepared checkout (1/3) | SOURCE-SUPPORTED procedure / execution OPEN |
| 120 | S2.1 / 4 GB client A / local console, after READY (2/3) | SOURCE-SUPPORTED procedure / execution OPEN |
| 121 | S2.1 / 4 GB client A / selected E6 pass (3/3) | SOURCE-SUPPORTED procedure / execution OPEN |
| 122 | S2.1W / CN/OS integration: Wi-Fi / ONNX branches | SOURCE-SUPPORTED procedure / execution OPEN |
| 123 | S2.1W / 8 GB server B / existing Wi-Fi (1/3) | SOURCE-SUPPORTED procedure / execution OPEN |
| 124 | S2.1W / 4 GB client A / use server printed IPv4 (2/3) | SOURCE-SUPPORTED procedure / execution OPEN |
| 125 | S2.1W / 8 GB server B / OPTIONAL prepared ONNX branch (3/3) | SOURCE-SUPPORTED procedure / execution OPEN |
| 126 | S2.2 / CN/OS integration: E7-C UART gateway trial | SOURCE-SUPPORTED procedure / execution OPEN |
| 127 | S2.2 / 4 GB gateway A / ~/CN (1/1) | SOURCE-SUPPORTED procedure / execution OPEN |
| 128 | S2.3 / CN/OS integration: supervisor readiness | SOURCE-SUPPORTED procedure / execution OPEN |
| 129 | S2.3 / Gateway Pi / prepared OS checkout (1/1) | SOURCE-SUPPORTED procedure / execution OPEN |
| 130 | S2.4 / CN/OS integration: Wi-Fi loss while heartbeat lives | SOURCE-SUPPORTED procedure / execution OPEN |
| 131 | S2.4 / Wi-Fi transmitting peer / prepared OS scripts (1/1) | SOURCE-SUPPORTED procedure / execution OPEN |
| 132 | S2.5 / CN/OS integration: recover and test heartbeat loss | SOURCE-SUPPORTED procedure / execution OPEN |
| 133 | S2.5 / Gateway / manual controlled fault sequence (1/1) | SOURCE-SUPPORTED procedure / execution OPEN |
| 134 | S2.6 / CN/OS integration: archive and interpret honestly | SOURCE-SUPPORTED procedure / execution OPEN |
| 135 | S2.6 / Each Pi / control (1/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 136 | S2.6 / Mac / both-node CN archive, then hash review (2/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 137 | At home: analyze immutable inputs | SOURCE-SUPPORTED offline workflow |
| 138 | H0 / Home: bag metadata, replay and timestamps | SOURCE-SUPPORTED procedure / execution OPEN |
| 139 | H0 / Home Linux / sourced Jazzy (1/1) | SOURCE-SUPPORTED procedure / execution OPEN |
| 140 | H1 / Home: native SDK bag audit and EuRoC export | SOURCE-SUPPORTED procedure / execution OPEN |
| 141 | H1 / Mac / canonical WBR checkout (1/1) | SOURCE-SUPPORTED procedure / execution OPEN |
| 142 | H2 / Home: native replica → derived ROS companion | SOURCE-SUPPORTED procedure / execution OPEN |
| 143 | H2 / Home ROS / file publisher, no live camera (1/1) | SOURCE-SUPPORTED procedure / execution OPEN |
| 144 | H3 / Home: conversion boundary and preparation gaps | SOURCE-SUPPORTED procedure / execution OPEN |
| 145 | H3 / Mac / native S/C only (1/1) | SOURCE-SUPPORTED procedure / execution OPEN |
| 146 | H4 / Home: Kalibr C fits and stereo validation | SOURCE-SUPPORTED procedure / execution OPEN |
| 147 | H4 / Mac / canonical WBR checkout (1/1) | SOURCE-SUPPORTED procedure / execution OPEN |
| 148 | H5 / Home: Allan fitting on native raw channels | SOURCE-SUPPORTED procedure / execution OPEN |
| 149 | H5 / Mac / native A only after preservation requirement resolved (1/1) | SOURCE-SUPPORTED procedure / execution OPEN |
| 150 | H6 / Home: offline ORB before any live experiment | SOURCE-SUPPORTED procedure / execution OPEN |
| 151 | H6 / Mac / optional existing demo take, not a C/S path (1/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 152 | H6 / Home Pi / generic exported immutable take (2/2) | SOURCE-SUPPORTED procedure / execution OPEN |
| 153 | H7 / Home: trajectory evaluation only with a reference | SOURCE-SUPPORTED procedure / execution OPEN |
| 154 | H7 / Mac / replace only verified input paths (1/1) | SOURCE-SUPPORTED procedure / execution OPEN |
| 155 | Home ablation: preserve every controlled variable | ASSUMED calibration-plan protocol |
| 156 | Backup: printable Session 1 checklist | ASSUMED printable one-page field checklist |
| 157 | Backup: printable Session 2 checklist | ASSUMED printable one-page field checklist |
| 158 | Backup: what the two-session plan cannot promise | OPEN / UNVERIFIED |
| 159 | Sources and reading order | SOURCE-SUPPORTED provenance |
| 160 | Review standard: explain the complete evidence chain | KNOWN method |
