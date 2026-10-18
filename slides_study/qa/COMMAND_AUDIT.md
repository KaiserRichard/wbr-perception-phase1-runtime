# Command audit

All 53 copyable command blocks were checked for shell syntax and exact slide/Markdown agreement. No command was executed except document generation/build/render/static QA. Names, flags, fixed runtime roots and output behavior were compared with the cited local scripts. SOURCE-SUPPORTED interface does not imply installed tooling or real-hardware validation.

## Audited interface families

| Source implementation | Checked CLI tokens |
|---|---|
| `/Users/quockaiser/.worktrees/wbr-study-deck/experiments/2026-10-13-pi5-env-snapshot/bundles/wbr-runtime-20261013T044130Z/wrapper_inspect.py` | `--output` |
| `/Users/quockaiser/Desktop/CN/hw/preflight.sh` | `${1:-wlan0}`, `${2:-preflight.json}` |
| `/Users/quockaiser/.worktrees/wbr-study-deck/experiments/2026-10-13-pi5-env-snapshot/bundles/wbr-runtime-20261013T044130Z/n1_precheck.py` | `--camera-available`, `--direct-cable-confirmed`, `--output` |
| `/Users/quockaiser/.worktrees/wbr-study-deck/experiments/2026-10-13-pi5-env-snapshot/bundles/wbr-runtime-20261013T044130Z/phase_gate.py` | `--seconds`, `--previous`, `accept-n2`, `review` |
| `/Users/quockaiser/.worktrees/wbr-study-deck/experiments/2026-10-13-pi5-env-snapshot/bundles/wbr-runtime-20261013T044130Z/n3_record.py` | `--camera-available`, `'bag'`, `--seconds`, `'output'`, `storage-result` |
| `/Users/quockaiser/.worktrees/wbr-study-deck/experiments/2026-10-13-pi5-env-snapshot/bundles/wbr-runtime-20261013T044130Z/n3_bag.py` | `replay`, `--record-result`, `--live-domain`, `--replay-domain`, `--output-dir` |
| `/Users/quockaiser/.worktrees/wbr-study-deck/calibration/lab/pi/record_calib_take.sh` | `NAME SECONDS`, `WBR_CAMERA_AVAILABLE` |
| `/Users/quockaiser/.worktrees/wbr-study-deck/calibration/allan/record_allan.sh` | `HOURS NAME`, `ALLAN_RECORDER` |
| `/Users/quockaiser/.worktrees/wbr-study-deck/calibration/lab/mac/take_to_kalibr_bag.sh` | `TAKE_DIR OUT_DIR`, `export-euroc` |
| `/Users/quockaiser/.worktrees/wbr-study-deck/calibration/lab/mac/run_kalibr_camimu.sh` | `BAG TARGET_YAML OUT_DIR`, `--cams`, `--imu-models` |
| `/Users/quockaiser/.worktrees/wbr-study-deck/calibration/lab/mac/run_kalibr_stereo_check.sh` | `BAG TARGET_YAML OUT_DIR`, `--models`, `--topics` |
| `/Users/quockaiser/.worktrees/wbr-study-deck/calibration/allan/allan_analyze.py` | `run_dir`, `out_dir` |
| `/Users/quockaiser/.worktrees/wbr-study-deck/tools/take_tools/take_tools.py` | `inspect`, `audit`, `export-euroc`, `--json`, `--markdown` |
| `/Users/quockaiser/.worktrees/wbr-study-deck/tools/trajectory_eval/traj_eval.py` | `--est`, `--ref`, `--clock-assumption`, `--align`, `--rpe-delta`, `--out` |
| `/Users/quockaiser/.worktrees/wbr-study-deck/tools/link_bench/pi/link_bench.py` | `--port`, `--out`, `--phases`, `--duration`, `--marker-gpio` |
| `/Users/quockaiser/.worktrees/wbr-study-deck/tools/link_bench/pi/la_analyze.py` | `--summary`, `--out` |
| `/Users/quockaiser/Desktop/Research/wbr-perception-phase1-runtime/experiments/2026-10-15-demo-day/demo.sh` | `check`, `record`, `offline`, `fetch`, `report`, `WBR_HOST` |
| `/Users/quockaiser/Desktop/CN/hw/edge_server.py` | `--host`, `--port`, `--transport`, `--mode`, `--sleep-ms`, `--queue`, `--service-log` |
| `/Users/quockaiser/Desktop/CN/hw/sender.py` | `--host`, `--transport`, `--frame-bytes`, `--fps`, `--duration`, `--out-dir` |
| `/Users/quockaiser/Desktop/CN/hw/run_e6.py` | `--dry-run`, `--link`, `--transport`, `--output-root` |
| `/Users/quockaiser/Desktop/CN/e7/gateway/gateway.py` | `--serial`, `--baud`, `--reply-format`, `--outDir`, `--net-status-ms` |
| `/Users/quockaiser/.worktrees/OS-wt-cn/linux/src/hea_runtime.c` | `socket`, `serial`, `baud`, `heartbeat-ms`, `net-status-ms`, `policy`, `csv` |
| `/Users/quockaiser/.worktrees/OS-wt-cn/scripts/netem_inject.sh` | `--dry-run`, `apply`, `clear`, `status`, `--loss` |

## Manual path and semantic checks

- Native calib `NAME SECONDS`, 1–120 s, exact fixed recorder/analyzer bundle; output `~/wbr-evidence/2026-10-15-calib-NAME/take`. 60/120 s tmpfs reserves are 1,987,200,000 / 3,974,400,000 bytes; fresh paths only.
- Native Allan `HOURS NAME`, 0.01–30 h; output `~/wbr-evidence/allan-NAME`. The binary must already be built. It writes raw CSV, not ROS bags; 207.36 MB/h plus logs and 3× free reserve. No native/ROS camera co-ownership.
- `common.sh` hard-codes Foundation, Kalibr source and image paths; no invented environment override. Native S/C input is TAKE_DIR/stereo_imu.db3; take_to_kalibr creates take.bag. Both fit wrappers take BAG TARGET OUT [IMU] and retain candidate outputs without replacing settings.
- `phase_gate.py` review field is timezone-aware `utc`, no more than 2 h old, actual strings and true booleans. Capture completion is not manual acceptance. N3 strict external-storage policy does not silently accept the newer card exception.
- Source ROS record uses `--storage sqlite3 --output ... --qos-profile-overrides-path ... --topics ...`. Study arrays enumerate each exact topic, including metadata; there is no `-a`. S/C primary bags are ordinary wrapper ROS bags and cannot be fed to native-format take_tools.
- Local wrapper launch expects a flat `config_file`, not nested ros__parameters. Serial underscore is removed by the node factory. Individual IR streams, raw rates, formats and static TF follow inspected source. Emitter option is an SDK dynamic parameter; support/readback must be verified. Camera namespace/name remain launch defaults camera/camera.
- Manual exposure 2000 us is ASSUMED from the calibration plan; gain 16 is the inspected launch default, not measured optimal/minimum gain. Exposure support, global-time/motion-correction readback and available metadata must be checked before calibration. Motion-only config selects no images.
- Wrapper metadata publisher source emits frame_number, clock_domain and timestamp fields. Installed publisher/message/metadata support remains UNVERIFIED; equal domains alone do not qualify clocks. No unverified conversion shifts source stamps silently.
- Generic ORB entry takes vocabulary, reviewed settings, exported sequence and times_ns.txt. Both stereo PNG names must match the times entries and be within combined IMU coverage. No unsupported --cam-imu-shift-ms or --bag is supplied.
- Demo offline/fetch/report operate only their fixed demo-day NAME tree. Fetch excludes raw .db3 and euroc-export; it is not a full backup. Native calib directories cannot simply be renamed to demo record paths. Offline owner authorization remains a precondition even though wrapper guards differ.
- E6 uses 8 GB server / 4 GB client, 4 ms synthetic service and explicit transport. Config matrix is 3 sizes×2 fps×5 repeats =30 runs/pass, not 120 completed runs. ONNX is separate and needs a real model/runtime/hash; network bytes are load, not image inference.
- E7 gateway CLI uses case-sensitive --outDir and selected timed/legacy response profile. Firmware is CubeMX integration source, no supplied fully built CN/OS image. E7 emits no INFERENCE; its optional NET_STATUS alone cannot create supervisor FRESH.
- OS hea_bridge option names were read in Linux bridge source/docs. NET_STATUS v3 and original OS v1 framing are distinguished. Stopping HB causes direct FAILSAFE; network age with HB alive permits HOLD then FAILSAFE. Board recovery requires reset; no invented remote-rearm command.
- netem wrapper acts on outbound root qdisc; run on transmitting result peer to affect reply delivery. clear deletes, does not restore prior qdisc. Linux/local console and pre-reviewed interface are required. >500ms is an operating fault interval, not a measurement guarantee.
- Standard shell, Linux/macOS provenance/hash/rsync commands were checked for correct platform and fresh destination semantics. Explicit P0 locations are chosen deployment paths and tested for presence, not claimed existing runtime paths.

## Per-step command blocks

| Step / block | Terminal | Syntax | Has explicit UNVERIFIED marker |
|---|---|---|---|
| P0 / 1 | Mac / before lab | PASS | no |
| P0 / 2 | Pi / each shell | PASS | no |
| S1.0 / 1 | Pi / control | PASS | no |
| S1.0 / 2 | Mac / canonical checkout | PASS | no |
| S1.1 / 1 | Pi / control | PASS | no |
| S1.2 / 1 | Pi / control | PASS | no |
| S1.3 / 1 | Pi / gate bundle, stage 1 | PASS | no |
| S1.3 / 2 | Pi / only after prior stage review | PASS | no |
| S1.3R / 1 | Pi / after actual review | PASS | no |
| S1.4 / 1 | Pi / prepared bundle | PASS | yes |
| S1.4 / 2 | Pi / after live camera has stopped | PASS | no |
| S1.5 / 1 | Pi / camera terminal A | PASS | yes |
| S1.5 / 2 | Pi / control terminal B | PASS | no |
| S1.5 / 3 | Pi / topic selection terminal B | PASS | no |
| S1.5 / 4 | Pi / recorder terminal B, same shell | PASS | yes |
| S1.5 / 5 | Pi / telemetry terminal C, during each take | PASS | no |
| S1.5F / 1 | Pi / after finalization | PASS | no |
| S1.5F / 2 | Mac / after all writers stop | PASS | no |
| S1.6 / 1 | Pi / ROS control before S1.5 | PASS | no |
| S1.6 / 2 | Pi / OPTIONAL native replica, ROS stopped | PASS | yes |
| S1.7 / 1 | Pi / ROS control, each take separately | PASS | no |
| S1.7 / 2 | Pi / OPTIONAL native replicas, ROS stopped | PASS | yes |
| S1.8 / 1 | Pi / ROS camera terminal, replace stereo launch | PASS | no |
| S1.8 / 2 | Pi / native alternative, BLOCKED pending companion | PASS | yes |
| S1.8R / 1 | Pi / recorder terminal B | PASS | no |
| S1.9 / 1 | Mac / before wiring, prepared binary | PASS | no |
| S1.9 / 2 | Pi / control, camera unplugged | PASS | no |
| S1.9T / 1 | Pi / only after analyzer capture starts | PASS | no |
| S1.9T / 2 | Mac / after copying capture and summary | PASS | no |
| S1.10 / 1 | Mac / copy small logs too | PASS | no |
| S1.10 / 2 | Mac / completed native or bench branches only | PASS | no |
| S2.0 / 1 | Pi / control, fresh bindings | PASS | no |
| S2.1 / 1 | 8 GB server B / ~/CN prepared checkout | PASS | no |
| S2.1 / 2 | 4 GB client A / local console, after READY | PASS | no |
| S2.1 / 3 | 4 GB client A / selected E6 pass | PASS | no |
| S2.1W / 1 | 8 GB server B / existing Wi-Fi | PASS | no |
| S2.1W / 2 | 4 GB client A / use server printed IPv4 | PASS | no |
| S2.1W / 3 | 8 GB server B / OPTIONAL prepared ONNX branch | PASS | yes |
| S2.2 / 1 | 4 GB gateway A / ~/CN | PASS | yes |
| S2.3 / 1 | Gateway Pi / prepared OS checkout | PASS | yes |
| S2.4 / 1 | Wi-Fi transmitting peer / prepared OS scripts | PASS | yes |
| S2.5 / 1 | Gateway / manual controlled fault sequence | PASS | yes |
| S2.6 / 1 | Each Pi / control | PASS | no |
| S2.6 / 2 | Mac / both-node CN archive, then hash review | PASS | yes |
| H0 / 1 | Home Linux / sourced Jazzy | PASS | yes |
| H1 / 1 | Mac / canonical WBR checkout | PASS | no |
| H2 / 1 | Home ROS / file publisher, no live camera | PASS | yes |
| H3 / 1 | Mac / native S/C only | PASS | yes |
| H4 / 1 | Mac / canonical WBR checkout | PASS | no |
| H5 / 1 | Mac / native A only after preservation requirement resolved | PASS | no |
| H6 / 1 | Mac / optional existing demo take, not a C/S path | PASS | no |
| H6 / 2 | Home Pi / generic exported immutable take | PASS | no |
| H7 / 1 | Mac / replace only verified input paths | PASS | no |

## Open / UNVERIFIED paths

1. Installed ROS wrapper/CLI readiness and metadata/exposure behavior; target db3 file playback with lossless first/last/count/stamp/pixel preservation.
2. Strict N3 storage receipt/runner acceptance for the approved qualified 128 GB-card exception.
3. Ordinary wrapper ROS bag→Kalibr/raw-Allan extraction; native Allan/N2 CSV→ROS companions. No supplied executable is invented. Native replicas/pilots remain blocked until preservation requirements are resolved.
4. E7 firmware deployment/baud qualification and full real-UART CN/OS v3 image + accepted result IPC producer; only host/PTY/loopback integration is reported tested.
5. Exact bounded short network fault timing for HOLD-only recovery; full measured WBR physical independence remains OPEN.
6. Actual copyable template input paths/clock/frame attestations need real data. The generic evaluator is not a claim those files or independent D435i ground truth exist.

The UNVERIFIED markers are intentional operator stop conditions, not failures of the document shell-syntax check.
