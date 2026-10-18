# WBR study-deck review — FINAL

Completed 18 October 2026. **160 PDF pages. Document quality loop PASS. All WBR hardware gates remain OPEN.**

## Deliverables and scope

- `main.tex` → `main.pdf`: 61 lecture pages, two ≤150-minute supervised sessions, home-analysis cards and backups; 32 consistently structured steps and 53 command blocks.
- `LAB_PLAN.md`: generated from the same step records, including exact command bytes, criteria, failure branches, destinations and source limitations.
- `README.md`, `PROGRESS.md`, source/command registers, ROS launch/QoS mappings, page inventories, renders, review ledger and artifact hashes.
- Printable one-page session checklists are PDF pages **156** and **157**.

No study-root main.tex or PROGRESS.md existed on arrival. Continued from the provided 91-page lecture and 78-page Phase-8 source material without modifying either. Phase 8 wins factual conflicts. Later lab observations are explicitly source-reported and dated; they do not promote a gate. The current worktree calibration plan wins over the supplied older copy. Missing worktree architecture/decision/evidence-index/AGENTS files were read from canonical equivalents; the source register records exact paths and hashes.

All writing stayed inside `slides_study/`. Existing branch retained; no commit, push, index operation, hardware contact, SSH, deployment, install, browser, GUI, camera, ORB execution or firmware change occurred. Commands printed in the deck were not executed. An attempted host process inspection was denied by the sandbox and supplied no evidence; it did not affect document QA.

## Build and review rounds

1. Authored the lecture with WBR motivations, illustrative calculations, common mistakes and check-yourself questions answered in notes. Added explicit frame/clock/noise conventions, gate ladder, MH01 measured rigid-alignment ATE, and the Phase-8 restriction on historical numeric RPE. Kept the inherited moloch/208×117 mm/Avenir Next/Menlo/palette/helper preamble, with updated metadata/footer total and normal-size listings support. No whole-frame scaling or font reduction.
2. Authored synchronized seven-field lab steps and named terminal blocks. Separated native SDK ownership from ROS ownership, physical source stamps from bag-write time, and WBR bench NO_LINK from CN/OS supervisor states. The long Allan recording is between visits at home, not hidden in either 150-minute budget.
3. Initial build succeeded but exposed missing Avenir transpose/arrow/checkbox glyphs. Replaced them with LaTeX symbols. Corrected working-directory authoring mistakes; failed operations are not counted as successful checks. Static command audit initially needed correction for argparse options assembled dynamically and positional shell arguments; actual interfaces were inspected and the checker corrected.
4. Built/rendered the full 157-page draft with the mandated Swift command. Looked at **every page** in four-page review sheets retaining each original 1280×719 render, with additional individual inspection of cover, table and dense code examples. No overflow into the footer, overlapping text, clipped code, broken diagrams or unreadable glyphs remained.
5. Review polish expanded key acronyms, changed ORB worker links to bidirectional cooperation, captured wrapper logs, checked per-terminal take IDs, added native/bench/CN archive commands and a complete optional ONNX server command. Final count became **160**.
6. Rebuilt and rendered the complete final PDF. Independently opened **all 19 changed/new final pages** at full page resolution (4, 5, 30, 43, 53, 55, 62, 87, 88, 102, 105, 113, 114, 123, 124, 125, 135, 136, 141), plus final page 160. The **141 other final page bodies** are byte-identical raster content to the previously inspected pages after excluding the common page-number strip. Their old-to-new page mapping and body hashes are in `qa/final-body-comparison.json`. All 160 footer numbers were independently extracted/checked; common final footers were also inspected visually. Final sheets contain all 160 pages. No unresolved layout defect.

## Final checks

| Check | Result / evidence |
|---|---|
| Required `latexmk -xelatex -interaction=nonstopmode main.tex` | Exit 0; 160 pages; `qa/build-final.txt` |
| `rg -n '^!\|Overfull\|Missing character\|undefined' main.log` | No output; exit 1 is the expected no-match result |
| Underfull diagnostics | No matches in final log |
| Required Swift renderer, `main.pdf preview` | Exit 0; 160 individual 1280×719 PNGs; `qa/render-final.txt` |
| Every-page visual review | All final page content covered; 19 changed/new pages individually rechecked; `qa/page-review.tsv` |
| PDFKit text/media-box audit | 160 pages; 208×117 mm; correct n/160 footer on every page; no body outside page or in footer collision zone |
| Command audit | 53/53 blocks pass Bash syntax; exact Markdown/TeX agreement; 23 first-party interface families inspected |
| Source register | 76 complete input/source hashes in `qa/source-hashes.json`; `qa/SOURCES.md` |
| ROS mappings / QoS | Flat launch mapping verified against local source; explicit topics; installed metadata/options remain UNVERIFIED |
| Authoring reproduction | Deterministic main.tex/LAB_PLAN/page/step inventories; check recorded in `qa/final-checks.txt` |
| Git scope / whitespace | Existing branch retained; only slides_study untracked; `git diff --check -- slides_study` clean |

The PDFKit bounds check excludes the numeric footer's font-selection rectangle: inherited font metrics extend slightly below the media box although its actual digit ink is visible and unclipped. This was visually checked. Body selection bounds and the separate bottom collision zone pass. Compilation and static/source checks qualify the document only.

## Open gaps and UNVERIFIED commands

These gaps are material. They are explicit stop conditions in the slides and Markdown; the deck does **not** claim a fully validated hardware workflow.

1. **ROS/native conversion and preservation.** Every primary S/C/A take has an explicit ROS 2 sqlite3 record command. Optional native S/C replicas are different physical takes and require a validated derived ROS companion before scheduling. Native file playback is supported by inspected wrapper source, but target db3 compatibility, startup completeness, source timestamps/domains and pixels are UNVERIFIED. Native N2/vendor CSV and native Allan CSV have no supplied ROS companion adapter. Ordinary wrapper ROS bags also lack a reviewed extractor for the supplied native-format Kalibr/Allan tools. No nonexistent program is named or silently assumed.
2. **Strict N3 card receipt.** The newer owner-approved 128 GB-card exception still requires sustained-write qualification and compatible reviewed receipt/runner support. The archived strict N3 runner expects qualified external-storage evidence; its bounded-card diagnostic does not qualify the full 30 Hz stereo protocol. The deck stops that qualification branch instead of fabricating a receipt or relaxing the 300-second N2 soak.
3. **Installed physical sensor behavior.** Wrapper/CLI availability, native runtime bundles, metadata fields, exposure/gain support/readback, global-time/motion-correction behavior and actual loaded power/storage all require lab verification. Source-checked syntax is not a physical measurement. SDK serial, ASIC serial, firmware-update ID and USB descriptor serial stay separate. SYSTEM_TIME is rejected for calibration.
4. **Calibration observations.** Actual target scale/flatness/NIR visibility, S far-distance visibility with the smaller printable grid, unit noise/walk, camera–IMU transform/time offset and held-out validation remain OPEN. The revised 6×4 target overrides the plan's stale six-row text. All proposed calibration thresholds are ASSUMED. No NVRAM write or operating-YAML replacement is prescribed.
5. **CN/OS integration.** E6 two-Pi commands are source-verified; optional ONNX requires an existing model/runtime/hash and separate configuration. E7 real UART baud, integrated firmware, local CNN and network performance remain UNTESTED. The requested original OS protocol is v1; NET_STATUS is a newer v3 extension in the read-only OS integration checkout. A built compatible board image and accepted CN-result IPC producer are not established. E7 telemetry alone sends no INFERENCE and cannot establish supervisor FRESH. Only host/loopback/virtual-serial integration is reported tested so far. Deployment SSH routes, exact OS trace path and bounded HOLD-only fault injection remain UNVERIFIED.
6. **Supervisor recovery / robot claim.** Keeping heartbeat alive while results stop can produce FRESH→HOLD→FAILSAFE at provisional result-age limits. Stopping heartbeat can produce direct FAILSAFE at its shorter limit. HOLD may recover automatically; FAILSAFE is latched and this board port requires reset. No remote rearm command is invented. These tests do not prove WBR physical balancing independence or N7.
7. **Home time and reference data.** Allan needs ≥4 h provisional, preferably 15–24 h, plus warm-up outside lab time. If no home hardware access exists, it stays OPEN. Full E6 campaign, E7 sustained qualification and V-route ablations are follow-up work. Evaluator template paths/frames/clocks require real inputs; without independent room ground truth, report closure/scale proxies, never ATE/RPE. No historical RPE or paper comparator excluded by Phase 8 was reinstated.

Detailed per-command source and unresolved-path disposition: `qa/COMMAND_AUDIT.md`. Final artifact/page hashes: `qa/final-artifacts.json` and `qa/page-review.tsv`.
