# R3 — Hardware, lab bookings and critical path

**Planning baseline: 14 October 2026. Status: PROPOSED / all hardware gates OPEN.**
Durations, risk ratings and budget ranges are estimates, not results or bookings. The milestone is **mounted, powered D435i/Pi live SLAM during controlled slow WBR motion, with STM32 validating health and rejecting injected failures**. Bench health integration precedes separately approved motion; navigation and jumping are later milestones. STM32 retains balance, body estimation, motor and jump safety through Pi loss. Camera/body IMUs remain separate. [L1][L2]

## 1. Hardware inventory and purchase order

Phases: **P0** camera-free preparation; **P1** platform/storage and N1–N3; **P2** calibration acquisition; **P3** offline N4A/N4B analysis; **P4** live N4C/N5 measurements; **P5** health interface N6 and mounted-robot N7. These are scheduling groups, not new gate definitions.

**Latest inventory:** the 14 Oct addendum confirms the **8 GB Pi booted**, using the 32 GB card and inadequate 5 V/3 A supply; Wi-Fi remains unresolved and Ethernet loose. Supply/card orders have no arrival evidence. Active D435i SDK serial: **317422076650**. ASIC, firmware-update ID and USB descriptor serial are separate fields, each observed as **327743061057**. September receipts and historical `PROJECT_STATE` targets do not prove current readiness/ownership. [L3][L4][L5]

Costs are **replacement/buy allowances**, USD unless marked EUR, excluding delivery/tax. Cited listings anchor our ranges. **U** means an unverified allowance needing a local quote; the citation supports the product/material, not that price. Reuse confirmed hardware.

| Item | Needed | Status on 14 Oct / acquisition action | Approximate buy range and provenance |
|---|---|---|---|
| Raspberry Pi 5 **8 GB** | P1–P5 | **Have**: boot measured; confirm same board is reserved across sessions | $175–220; current Adafruit listing $200 [H1]. Reuse it. |
| **5.1 V/5 A** bench supply and appropriate mains plug | P1–P5 bench | **Ordered**; confirm delivery first. Existing 3 A supply has measured faults | $14–25; official supply listing $14.04 [H2] |
| 128 GB V30/A2 microSD; retain 32 GB backup | P1–P5 | **Ordered**; boot migration and sustained writes unqualified; preserve original card/image | EUR 29–40; exact G3 listing EUR 34.99 [H3] |
| NVMe + **Pi 5 M.2 HAT+**, ribbon/spacers | P1 onward if card path fails; routine larger datasets | **Buy**, only if needed; lab loan first, **confirm with lab**. Historical SN530/enclosure is planned, not confirmed present | $45–90 total for 256–512 GB + HAT; SSD brief $30/$45, current 512 GB listing $55; HAT from $12 [H4][H5][H6] |
| D435i | P1/P2/P4/P5 | **Have**, loan/access reported; confirm active-unit reservation and return date | $399–500; manufacturer $399, currently out of stock [H7]. Avoid a replacement dependency. |
| Short **USB 3 data** A-to-C cable + spare | P1/P2/P4/P5 | **Have** a cable used at 5000M; spare/condition unknown, **confirm with lab** | $10–25 **U**; manufacturer 5Gbps cable reference [H8]. Connector shape alone is insufficient. |
| Active cooler/heatsink; clear airflow | P1–P5 | **Lab must provide** / inspect: historical Raspibase PWM fan reported, current 8 GB installation unknown | $13–20; official Active Cooler listing $13.50 [H9] |
| AprilGrid print + rigid flat backing | P2; reusable checks P5 | **Buy** or lab fabricate; target availability unknown | $20–60 **U** local matte print/backing; commercial rigid target reference displays $261 for its selected configuration, not our dimensions [H10][K1] |
| Camera bracket + Pi standoffs/enclosure + strain relief | P1/P2 bench; final P5 | **Lab must provide**, robot fit unknown; fabricate after dimensions confirmed | $15–60 **U**, hardware/fabrication allowance; camera has 1/4-20 and M3 mounting points [H7] |
| STM32H7 board, debugger, body IMU and existing controller | P0 spec; P5 bench/robot | **Lab must provide**; exact board, firmware, spare port and working balance baseline **confirm with lab** | $35–60 for a representative H7 development board, listed H753 Nucleo $40.81 [H11]; not a replacement for the robot controller |
| WBR chassis, actuators, emergency stop and rated support stand | P5 | **Lab must provide**; availability and readiness UNKNOWN | **Custom quote, range UNKNOWN**. Repo names WBR but has no verified chassis BOM/price [L1][L2]. Do not budget a generic wheeled chassis as an equivalent. |
| Robot battery + compatible charger/distribution | P5 | **Lab must provide**; voltage, chemistry, capacity, connectors and motor transients UNKNOWN | $70–150 pack-only illustrative budget, manufacturer 4S/5 Ah example $94.99, unavailable [H12]; **not a selected WBR pack**, charger extra |
| DC-DC supply for Pi, fuse, wiring and suitable power interface | P5; qualification before mounting | **Buy** unless lab has a qualified rail; confirm battery input range first | $35–80 **U** assembled allowance; $32.95 5 V/5 A buck is a cost anchor only [H13], **not** proof of 5.1 V regulation, derated 5 A delivery or USB-PD support |
| Wi-Fi access / Ethernet cable; local console fallback | P1–P5 | **Have** onboard network; **lab must provide** network access and monitor/keyboard if unreachable | $5–10 cable allowance; listed Ethernet cable $6.95, no longer stocked [H14]. Reuse lab infrastructure. |
| Tripod/target stand; separate rated robot stand | P2/P4; robot stand P5 | **Lab must provide**, confirm both; included D435i desktop tripod is not evidence that loan kit includes it | $30–70 camera tripod; retailer examples $29.95/$48.93 [H15]. Robot support price/load rating UNKNOWN. |
| Measuring tape, calipers, straightedge and floor markers | P2/P4/P5 | **Lab must provide**, confirm; buy small tools if absent | $5–15 tape, $20–40 **U** basic caliper allowance; tape listing $4.99 [H16]. Target metrology needs checked calipers, not only route tape. |
| External camera/phone, optional motion capture | P4/P5 only | **Lab must provide**, if already available; no owned phone/mocap assumed | Borrow first; $30–80 **U** webcam allowance [H17]; mocap **quote UNKNOWN** [H18]. Do not buy mocap for this milestone. |

**Spending order:** receive supply/card orders → borrow cooler/target/metrology/controller → missing cable/mount/power parts → NVMe if qualification/capacity requires it.

---

## 2. Capture capacity and lab booking plan

**Storage reconciliation:** calibration plan/HEAD `cf09251` record an **owner exception for calibration/VIO takes on the 128 GB card**. Conditions: dedicated directory; write probe larger/longer than the largest take; **≥27.6 MB/s** (1.5 × rounded 18.4); free space **≥2 × planned take + OS reserve**; per-take delivery audit; verified Mac copy before deletion. These are proposed qualification conditions, not measured performance. Routine large datasets still require qualified separate storage. [L5]

The existing external-storage gate rejects root/microSD: **do not fake its UUID/device receipt or weaken it**. Review a card-specific qualification/receipt path and N3 compatibility before booking; otherwise use external storage. Its **9.216 MB/s** raw-IR1 margin does not qualify stereo. Preserve duration, overall/worst-batch checks, hashes and headroom. [L6]

**Calculated stereo budget:** 2 × 640 × 480 × 30 = **18.432 MB/s**, 1.106 GB/min before serialization/audit overhead. Reserve the calibration plan's provisional **1.5 GB/min**, then revise from the pilot. S + C1–C3 at 120 s each and V1–V3 at 90 s total 750 s: **13.824 GB image payload / 18.75 GB provisional capture allowance**, plus failures and derived copies. Have **40 GB data space plus OS reserve** as an initial planning allowance, and recheck per take. A 300 s stereo recording is **5.53 GB payload**, exceeding the observed 3.9 GB `/dev/shm`; RAM is a bounded diagnostic workaround, not the storage plan or the mandatory N2 substitute. [L4][L5]

Prefer PCIe HAT NVMe if buying; a borrowed USB3 SSD may arrive sooner. Standard HAT: 2230/2242 M-key, clearance above Active Cooler; historical SN530 fit is unknown. Its 3.3 V/3 A rail has **9.9 W capacity, not typical consumption**. Budget **2–5 W extra provisionally (U)**, then measure idle/write/SLAM peaks; larger loads/conversion losses may exhaust the 25.5 W supply budget. Documented shared USB/fan limits are 600 mA with 3 A power versus 1.6 A with suitable 5 A power. [H5][H19][H20]

| Booking request, not yet reserved | Hardware required together | Length / personnel estimate | Ready before arrival / exit evidence |
|---|---|---|---|
| **B1: platform and fresh gates**, first suitable slot from 15 Oct | 8 GB Pi, adequate PSU, cooler, final data medium, D435i/cable, Mac; lab console/network | **3–4 h**, owner/operator + engineer | Freeze helpers and hashes; card backup/migration plan; storage receipt route; wrapper inspection; exact N1–N3 checklist. If power/access/storage unresolved, use slot for diagnosis only. Exit: actual reviewed gate receipts, not a demo screenshot. |
| **B2: calibration and held-out motion** after B1 | Same unit/profile/topology, fixed measured AprilGrid, rigid backing/stand, diffuse usable IR light, calipers/tape, Mac backup space | **3–4 h**, operator + engineer | Converter synthetic round-trip and tool import trial ready; target measured and tags visible in both IR views; capture/backup budget ready. S, C1–C3, static I diagnostics, V1–V3; inspect first take before repeating. Exit: decoded pixels/timing/coverage audit and two checksum-verified copies. |
| **B2A: stationary noise recording**, after gates and recorder pilot | Pi/PSU/cooler, D435i fixed on stable surface, qualified data path; no robot/target needed | **30 min warm-up + 15–24 h**, start/end supervision; lab-approved overnight occupancy/monitoring | New IMU-only recorder ready and tested, power/disk monitoring and normal-stop recovery ready. Short pilot measures overhead. Current four-stream recorder is limited to 120 s. If overnight occupancy unavailable, reschedule; a 4 h provisional run cannot certify unsupported long-term walk. [L5][K3] |
| **B3: live performance** after calibrated N4B review | Pi, camera, cooling, final cables/storage, textured marked route; optional external camera | **2–3 h**, operator + engineer | Selected settings/binary/data hashes, approved latency/continuity budgets and counters; repeated offline results ready. Exit: source-age/backlog/drop/power/thermal evidence, not playback speed. |
| **B4: robot installation and health faults** | B3 hardware + actual WBR/STM32/body IMU, final mounts, battery/DC-DC, link, debugger, rated stand/emergency stop | **3–4 h**, perception engineer + controller owner + operator | Interface and electrical design reviewed; receiver fixture verdicts; DC-DC load test; motors disabled for receiver bench. Exit: live health at STM32, stale/invalid/reset/disconnect traces and controller timing. |
| **B5: controlled robot motion**, separate safety authorization | B4 hardware, approved tether/support and cleared floor; tape markers; external observer/video optional | **2–3 h**, controller owner + operator/spotter + engineer | Working independent balance baseline, approved motion envelope/stop policy and prior B4 review. Exit: slow-motion tracking/health and Pi-loss fallback observations. No jumps/navigation. |

P0/P3 use Mac; reserve **native x86 workstation fallback** if Kalibr/import compatibility fails. Resolve tool/ARM64 support before B2. One hardware-session owner; overnight/target capture cannot share the camera. Acquisition stays Pi-local; later SSH is control only. No bookings/contact/execution occur here.

---

## 3. Critical path and shortest ordering

**Current evidence:** three EuRoC runs exist on the former 4 GB Pi, with saved ATE around 0.037–0.042 m; undervoltage invalidates speed conclusions. D435i replay crashed on the first frame; patch 4 is applied in the isolated Pi build copy but rebuild was interrupted. Only a 15 s RAM take has clean reported delivery. Calibration uses nominal geometry/assumed noise, and camera–IMU offset is unknown. No accepted N0–N7 state follows from those observations. [L3][L4][L7]

| Phase | Prerequisite and work | Working-time range, excluding queues | Exit needed to move on |
|---|---|---|---|
| **P0: prepare now** | Read current evidence; confirm lab inventory/board/link; prepare target, converter, IMU recorder, timing/analysis tools and health contract proposals | **2–5 engineer days**, parts/lab lead times separate | Offline/synthetic fixtures, reviewed interfaces/format changes, reproducible commands and checksummed bundles. No camera or ORB execution. |
| **P1: unblock and qualify** | Adequate PSU/cooling, reachable Pi and qualified storage; N0 → **fresh N1 → N2 → N3** | **0.5–1 day** if clean; **1–3 days** if diagnosis needed | Correct identity/direct USB **≥5000M**; reviewed exact native stages; N3 readback/topic/QoS, load recording, complete isolated replay and original header/context fidelity. [L6] |
| **P2: capture once, inspect early** | P1 and attested extra stereo profile; S/C/I/V motion then IMU-only A | **1–2 days + 15–24 h elapsed** | Original `.db3`/raw channels, measured target/metadata, decoded-count/timing audit, adequate Allan support and verified backups. [L5] |
| **P3: calibrate and qualify offline** | P2 data; finish patch-4 rebuild on stable power and check linkage; bounded stable-power EuRoC reference; calibration/held-out checks and repeat N4B | **2–4 days**; incompatible tool route adds **2–5 days** contingency | Versioned camera–IMU geometry/time/noise register, retained warnings, approved calibration/continuity criteria, repeated initialization/tracking and all failure logs. [L5][L7] |
| **P4: live and resources** | Reviewed N4B; same binary/settings → N4C, characterize N5 | **1–2 days** | Live input accounted for; bounded queues/source age within owner-approved budgets; measured drops, processing tails, CPU/RSS, power/thermal behavior. [L7] |
| **P5: health and mounting** | Reviewed message/link implementation and N6 fixtures; P4 evidence; actual robot, mount and qualified battery rail | **1–3 days** plus **0.5–1 day** for separately approved motion | N7 bench receiver/fault traces, then B5 live tracking under controlled motion; stale pose cannot become fresh through a heartbeat; controller retains local authority. [L1][L7] |

Critical path: **power/storage/tools → P1 → P2 → P3 → P4 → P5**, joining **controller access → interface approval → N6 fixtures → electrical/mount readiness**. Slower branch controls delivery. Estimate **10–15 working days** with immediate inputs/approvals and frequent slots; budget **4–6 calendar weeks** from 14 Oct with recapture/integration contingency. Deliveries/robot readiness are unknown. Cancel a capture slot if prerequisites are unresolved 24 h before it.

**Parallel:** prepare target/import/IMU recorder and Mac health semantics while awaiting parts; controller owner checks ports/mount/power. After CAMERA AVAILABLE/stable power, rebuild with camera idle; no simultaneous build/SLAM during capture. Overnight A can overlap Mac analysis of secured C/V data; rerun calibration with measured noise before selection. Reviewed receiver fixtures/mount fabrication overlap P3/P4. Camera processes remain exclusive.

**Never skip:** explicit **CAMERA AVAILABLE** before camera-dependent commands or any ORB execution; stable power; current-unit identity; USB ≥5000M; exact N2 **IR1 Y8 640×480/15, gyro/200, accel/100**, **20 → 105 → 300 s** stages; IR **14.25–15.75 Hz**, gyro **190–210 Hz**, accel **95–105 Hz**, image gaps **≤0.20 s**, motion gaps **≤0.05 s**, positive timestamp/frame steps, no missing image frames and all original health/content/log review criteria. N3 is still required even if the chosen live estimator uses the native SDK. P2/P4 **IR1+IR2/30** with emitter OFF is separately attested, never substituted for N2. N4B precedes N4C; health/API and safety budgets need review before implementation/physical acceptance. [L6][L7]

**Safely defer:** ROS SLAM wrapper, Docker, GUI/RViz on Pi, depth/color/clouds, navigation, wheel/body-IMU fusion, learned scheduling, jumps and mocap purchase. Keep Jazzy for the mandatory N3 qualification; choosing native SLAM does not erase it. Do not redo the full environment/build from scratch or rebuild unchanged EuRoC tooling. Keep a bounded stable-power rerun for the patched runtime/reference. Factory stereo readback remains the operating model; optical validation and camera–IMU/time/noise work remain necessary, while EEPROM/firmware writes are outside the default path. [L2][L5]

---

## 4. Risk register — top eight

Likelihood/impact are planning judgments: H = high, M = medium, L = low. Evidence references identify why a risk is included, not its statistical probability.

| Risk | Likelihood / impact | Early warning sign | Mitigation / responsible role |
|---|---|---|---|
| **1. Supply/robot rail droop or power interruption** | H / H | New live/latched throttling bits; reboot; voltage dip on storage/CPU/motor load | Adequate bench PSU first; measure final DC-DC at battery extremes/load; preserve logs; controller owner reviews independent rail/fallback. No gate promotion under power faults. [L4][H20] |
| **2. Storage stalls or loss of irreplaceable takes** | H / H | Periodic gaps like failed 100 s take; slow fsync batches; low free space; copy/hash mismatch | Card exception requires its own reviewed qualification; pilot full recorder load; borrow/buy NVMe if inadequate; back up after each session. RAM only bounded diagnostics. [L4][L5] |
| **3. Camera/lab/controller unavailable together** | M / H | Loan return date/board reservation not confirmed; overnight access denied; robot still under repair | Owner reserves named unit and B1/B2/B2A early, controller owner attends B4/B5; perform Mac work during waits; never shorten Allan/soak to fit a slot. [L3][L5] |
| **4. USB/network/mechanical access instability** | H / M–H | Camera branch 480M/reset; loose power/USB; 8 GB board fails network discovery | Direct known cable + spare; strain relief; local console and saved host identity; inspect exact camera branch; fresh N1 after topology/storage changes. Network loss must not stop Pi-local acquisition or STM32 balance. [L4][L6] |
| **5. Calibration unobservable, wrong clocks/frames or invisible target** | H / H | Poor IR tag detections; structured residuals; inconsistent shifts; IMU gaps/scale errors | Matte measured rigid grid, adequate IR illumination, all-axis motion; retain raw domains; held-out repeats; full-precision separate IMUs. Do not copy old-unit noise or silently rewrite stamps. [L5][K1][K2] |
| **6. Tool/import incompatibility or replay fix still fails** | M / H | Build interrupted/missing libraries; SDK `.db3` unreadable by calibration importer; SIGSEGV returns | Verify patched library hashes/linkage; tiny synthetic import before booking; real-file round-trip after gates; use prepared x86 workstation fallback. Preserve upstream failures/build provenance. [L4][L5] |
| **7. Pi misses live freshness under heat/vibration/motion** | M / H | Growing queues/source age; tracking LOST/reset events; blur; thermal throttling | Native headless baseline; active cooling; rigid camera assembly and restrained cables; short approved motions; profile before adding ROS consumers. Switch algorithm/compute only on matched-data evidence. [L5][L7] |
| **8. STM32 accepts stale/reset/invalid perception or balance depends on Pi** | M / H | Fresh heartbeat with old pose; NaN/wrong frame/old session accepted; MCU loop jitter after link load | Reviewed validity/age/session semantics and CRC/framing; synthetic receiver fixtures → supported robot bench faults → separately authorized motion. Controller owns fallback, watchdog, motor and jump limits. [L1][L7] |

---

## 5. Owner decisions, provenance and validation

These are recommendations for later review, **not implemented architecture/API changes**. No lab messages, reservations, purchases, installs, SSH or hardware processes were performed.

| Decision / when | Recommended default | Evidence that would change it |
|---|---|---|
| **Algorithm**, after P3/P4 | Keep existing **ORB-SLAM3 stereo-inertial** native path; reuse build and known dataset | Repeated failures on qualified/calibrated input, or approved freshness/resource bounds missed at supported profile. Timebox fault diagnosis to 2–3 days, then compare one alternative on identical saved data and revisit Pi compute. No unmeasured promise that replacement solves it. |
| **ROS 2 on the robot**, before interface design | Retain installed Jazzy/N3 qualification; run first live SLAM through the existing native SDK example and a small reviewed health bridge | A reviewed ROS wrapper matches offline behavior, preserves clocks/frames and meets live budgets, or an actual navigation consumer requires ROS. No reinstall or graph change in this ticket. [L2] |
| **Pi–STM32 physical link**, before P5 tooling | Propose a short dedicated **3.3 V UART** for health if the actual controller has a spare port; review pin/ground/EMI constraints first | Reuse an already proven controller link if present. CAN requires approved separate interface/transceiver/bus-load design; README's actuator CAN ownership does not establish a Pi health link. USB-CDC possible only with validated MCU implementation. No Wi-Fi dependency for safety. [L1][H20] |
| **Health contract and budgets**, during P0; ratify after P4 | Health-only, no balance commands; review version/session/sequence, estimator/input state, source-age/clock relation, frame/reset IDs, bounded framing/CRC and stale/invalid fallback; use receiver monotonic timeout | Controller owner selects rate, maximum useful source age and timeout from actual loop/fallback requirements; **numeric values remain UNKNOWN**. A heartbeat cannot refresh an old pose. N6 fixture implementation needs message/API approval. [L7] |
| **Buy NVMe?**, before B1 | First try already ordered **128 GB card under recorded exception**; borrow qualified external SSD for N3 if existing tooling cannot represent that exception | Card fails sustained-write or in-run delivery checks, capacity/retention exceeds short takes, or receipt/tooling route would take longer than qualifying external storage. If buying, prefer HAT NVMe and qualify its added power. [L5][L6][H5] |
| **Target/calibration tool route**, before B2 | Keep repo's **6×6, 80 mm tags, spacing ratio 0.25**; **A0 matte print** on rigid backing. Pattern is 580×580 mm; one-tag white border makes at least 740×740 mm. Use measured dimensions. Kalibr offline via tested workstation route | A smaller target only after reviewed dimensions/detection checks. Verify selected Kalibr version/import support before capture; use native x86 lab machine if Mac/ARM route blocks. Do not replace factory rectification with a fit to already rectified images. [L5][K1][K2] |
| **Battery/DC-DC/mount**, before B4 | Match actual battery limits; regulated 5.1 V/≥5 A design with derating, wiring/fusing and reviewed USB power delivery; rigid camera-to-its-IMU assembly, secured Pi and cable slack | Measured transients/load demand require a larger converter/filtering or revised mount. Generic fixed-5 V buck price is not a qualification; do not force USB current limits. [H13][H20] |
| **Robot/mocap acceptance scope**, before B4/B5 | Health-only supported robot bench first; controlled slow motion next; tape-marked route and borrowed external video | Mocap already available and calibrated with known clock/rigid-body transform enables reference trajectory evaluation. Tape closure/scale are proxies, external video is observation, neither is ATE ground truth by default. [L5][L7] |

**Owner questions to resolve before spending lab time:** supply/card arrival date; camera loan window and cooler inventory; overnight recording permission; target printing/metrology availability; actual STM32 board/spare link and controller engineer; robot/battery/stand/stop readiness; available workstation and backup space. Unknown availability shifts the table below; this document invents no lab stock or confirmed dates.

**Local source register** (relative to this file; inspected 14 Oct):

- [L1] [AGENTS.md](../../AGENTS.md), [README](../../README.md), [architecture](../../docs/ARCHITECTURE.md): fixed ownership, permissions and runtime policy.
- [L2] [DECISIONS](../../docs/DECISIONS.md), [PROJECT_STATE](../../docs/PROJECT_STATE.md), [NEXT_GATE](../../docs/NEXT_GATE.md), [two-week backlog](../../docs/NEXT_TWO_WEEKS_PERCEPTION_PLAN.md): accepted separation and historical/open gate state.
- [L3] [13 Oct facts](../../experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md): build, active camera, orders and known-dataset observations.
- [L4] [14 Oct addendum](../../experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md), [15 Oct runbook](../../experiments/2026-10-14-lab-prep/LAB_RUNBOOK_2026-10-15.md), [brief slides](../../slides_brief/main.tex): latest hardware/diagnostic limitations.
- [L5] [calibration plan](../../docs/D435I_CALIBRATION_PLAN.md), [readiness](../../docs/D435I_VIO_CALIBRATION_READINESS.md): target/takes, long IMU capture, pending tools, recorded card exception. Readiness's numeric September calibration is historical, not this unit's calibration.
- [L6] [Phase A runbook](../../experiments/2026-09-12-pi5-native-sensor-validation/PHASE_A_RUNBOOK.md), [native bring-up](../../docs/RPI5_NATIVE_PERCEPTION_BRINGUP.md): exact gates and external-storage receipt constraints.
- [L7] [N4B/N4C plan](../../experiments/2026-10-13-n4b-d435i-prep/n4b_plan.md), [course slides](../../slides_course/main.tex): N4–N7 ladder and UNKNOWN budgets; later `.db3`/8 GB facts take precedence over older `.bag`/stand-in wording.

**External sources** (checked 14 Oct 2026; retailer prices are anchors, availability can change):

[H1]: https://www.adafruit.com/product/5813
[H2]: https://www.adafruit.com/product/5814
[H3]: https://www.pccomponentes.com/kioxia-exceria-g3-128gb-microsdxc-uhs-i-clase-10-u3-v30-a2
[H4]: https://datasheets.raspberrypi.com/ssd/raspberry-pi-ssd-product-brief.pdf
[H5]: https://www.raspberrypi.com/products/m2-hat-plus/
[H6]: https://www.adafruit.com/product/6089
[H7]: https://store.realsenseai.com/buy-realsense-depth-camera-d435i.html
[H8]: https://www.ugreen.com/en-ae/products/ae-20287
[H9]: https://www.adafruit.com/product/5815
[H10]: https://www.foamcoreprint.com/kalibr-targets
[H11]: https://www.digikey.com/en/products/detail/stmicroelectronics/NUCLEO-H753ZI/21348937
[H12]: https://www.spektrumrc.com/product/spektrum-14.8v-5000mah-4s-30c-smart-lipo-battery-ic5/SPMX50004S30.html
[H13]: https://www.pololu.com/product/2851
[H14]: https://www.adafruit.com/product/730
[H15]: https://www.bhphotovideo.com/c/buy/Complete-Tripods-with-Heads/ci/2635/N/4075788742
[H16]: https://www.harborfreight.com/promotions/tape-measures-levels.html
[H17]: https://www.logitech.com/en-us/shop/p/c270-hd-webcam
[H18]: https://www.optitrack.com/systems
[H19]: https://datasheets.raspberrypi.com/m2-hat-plus/raspberry-pi-m2-hat-plus-schematics.pdf
[H20]: https://www.raspberrypi.com/documentation/computers/raspberry-pi.html
[K1]: https://github.com/ethz-asl/kalibr/wiki/calibration-targets
[K2]: https://github.com/ethz-asl/kalibr/wiki/camera-imu-calibration
[K3]: https://github.com/ethz-asl/kalibr/wiki/IMU-Noise-Model

Additional technical sources: [HAT schematic][H19], [Pi power/GPIO][H20], [Kalibr targets][K1], [camera–IMU calibration][K2], [noise model][K3]. The D435i store's BMI055 text does not identify the observed BMI085 unit [L3].

**Validation:** read-only Git inspection: `claude/project-thread-rhsrup`, HEAD `cf09251`, existing dirty/untracked work preserved. COMMON prohibits Git mutations, so no branch/commit/push. Only this roadmap is authored. Camera-free document checks passed: local links, six sections, eight risks, citations and arithmetic. No runtime gate or print pagination is verified. Build/test/manual command cards are in the linked lab/calibration runbooks; missing tooling/budgets remain prerequisites. Reproduce the link/arithmetic check from repository root:

```bash
python3 - <<'PY'
from pathlib import Path
import re
p = Path('slides_roadmap/research/R3_plan.md')
s = p.read_text()
assert all((p.parent / t).exists() for t in re.findall(r'\]\(([^)]+)\)', s)
assert len(re.findall(r'^\| \*\*[1-8]\. ', s, re.M)) == 8
assert 2 * 640 * 480 * 30 == 18432000
assert abs(6 * .08 + 5 * .02 + 2 * .08 - .74) < 1e-12
assert abs(18.432 * 750 / 1000 - 13.824) < 1e-12
print('PASS: camera-free document checks only')
PY
```

---

## 6. One-page week-by-week owner plan

**Week boundaries start today, Wednesday 14 Oct.** Dates below are conditional booking targets, not reservations. Roles are proposed: owner arranges hardware/access and approves changes; perception engineer prepares/analyzes utilities; controller owner implements/reviews STM32 behavior. No physical progression without its preceding evidence. Carry an unresolved phase into the next week instead of compressing gates.

| Week / dates in 2026 | Owner / lab action and hardware to reserve | Engineering work, including parallel tasks | Exit / next decision |
|---|---|---|---|
| **W1 · 14–20 Oct** | Confirm supply/card delivery, 8 GB Pi/camera loan, cooler, storage, console/network. Request **B1, 3–4 h**; 15 Oct only if ready. Reserve B2/B2A provisionally. | **P0/P1:** prepare reviewed card receipt route or external storage; target/IMU recorder/converter fixtures; draft health contract and inspect actual MCU interfaces. After authorization/power, finish interrupted build; fresh N0/N1/N2/N3. | Reviewed entry/storage/gate evidence or precise blocker. Diagnostic demo stays OPEN. Decide NVMe if card/tooling route fails; do not turn 15 s RAM into qualification. |
| **W2 · 21–27 Oct** | **B2, 3–4 h + B2A overnight 15–24 h**, same camera/Pi/PSU/storage; measured A0 grid/stand, calipers/tape and IR lighting. Reserve actual robot/controller for W4. | **P2/P3:** collect S/C1–C3/I/V1–V3, audit first take and backup; full-precision stationary A after pilot. Parallel: calibrator/import analysis, reviewed health fixtures and mount/electrical design. | Usable immutable captures and supported noise fits; calibration repeat/holdout review. Recapture now if target/timing fails. Approve interface/latency and final power design before hardware integration. |
| **W3 · 28 Oct–3 Nov** | Workstation as needed; **B3, 2–3 h**, Pi/camera/final cooling/cables, marked room route. | **P3/P4:** stable-power reference rerun, calibrate/select settings, repeated N4B then N4C/N5. Parallel: N6 receiver fixtures, mounts and DC-DC bench load checks. | Live tracking/resource/source-age evidence within reviewed bounds; receiver rejects stale/reset/invalid fixtures. Decide algorithm/compute only if qualified baseline misses bounds. |
| **W4 · 4–10 Nov** | **B4, 3–4 h**, actual WBR/STM32/body IMU, battery/rail/link, mounts, rated stand/stop, controller owner present. | **P5:** motors-disabled receiver bench; mount reviewed Pi/camera; injected disconnect, Pi/SLAM reset, delayed/invalid messages; log MCU timing/fallback and Pi health. | Bench integration complete; static health may correctly be NOT_INITIALIZED. No moving-tracking/balance claim. Authorize B5 separately; bring it forward if prerequisites are ready. |
| **W5 · 11–17 Nov** | **B5, 2–3 h**, approved tether/cleared route/operator/spotter; same hardware, optional borrowed video/mocap. | Controlled slow motion and Pi-loss fallback under controller-approved envelope; examine initialization, vibration/blur/age/loop behavior. Recapture/reprofile the failing layer. | **Target milestone:** live mounted-robot tracking plus STM32-validated health/fallback evidence. Navigation remains a new objective. If W4 slipped, finish bench integration first. |
| **W6 · 18–24 Nov · contingency** | Hold one **2–4 h** repair/recapture slot; extend camera loan if required. | Resolve calibration/tool/power/robot blockers; preserve failures; freeze reproducible bundle, raw/derived hashes and test report. | Accept only evidenced gates. Unresolved live performance or controller safety becomes a blocker/decision, not a manufactured delivery PASS. |
