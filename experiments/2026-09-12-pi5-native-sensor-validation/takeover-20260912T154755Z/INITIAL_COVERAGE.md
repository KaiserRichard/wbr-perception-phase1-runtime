# Recovered preparation coverage before edits

All statuses describe tooling, never hardware qualification. Existing code was inspected and 31 offline tests passed before editing.

| Category | Initial status | Remaining work |
|---|---|---|
| A Repository reconciliation | PARTIAL | Preserve takeover hashes, complete broken runbook references |
| B Ethernet / SSH | PARTIAL | Verify direct link, deploy isolated checksummed bundle |
| C N1 USB | PARTIAL | Nonfinite speed rejection, complete failed-path diagnostics |
| D Permissions | COMPLETE | Existing serial-scoped read-only inspection/helper retained; physical access remains untested |
| E N2 smoke | PARTIAL | Evidence sealing and staged gate integration |
| F N2 reproduction | PARTIAL | Evidence sealing and staged gate integration |
| G N2 300-second soak | PARTIAL | Missing reviewed acceptance path; no hardware pass |
| H N2 analyzer | COMPLETE | Whole-window/gap/sequence checks already implemented and tested |
| I Image validation | PARTIAL | Compile checked sampler on Pi; test full synthetic content analysis |
| J Kernel monitoring | COMPLETE | Existing raw follower/classifier and calibration warning separation |
| K Pi health | COMPLETE | Existing bounded one-Hz monitor; power history is a runtime blocker |
| L Storage qualification | PARTIAL | Missing tests and blkid evidence |
| M NVMe/JMS583 procedure | NOT STARTED | Missing current runbook and budget procedure |
| N ROS wrapper preparation | PARTIAL | Wrapper absent on Pi; source/config and install-cost review |
| O N3 observer | PARTIAL | QoS validation and camera availability guard |
| P Topic/type/QoS | PARTIAL | Verify source-resolved names and parameter readback path |
| Q Explicit recorder | NOT STARTED | No first-party gated recorder |
| R Bag finalization | PARTIAL | Inspector exists; recorder clean shutdown integration absent |
| S Stop-live boundary | PARTIAL | Replay guard exists; missing executable runbook integration |
| T Isolated replay | PARTIAL | Existing orchestration needs synthetic ROS test and provenance |
| U Provenance | PARTIAL | Missing bundle builder and final N2 hashes |
| V Fail-closed gates | PARTIAL | Missing dispatcher referenced by n3_bag.py; incomplete prerequisite chain |

Architecture stays native Pi acquisition, ROS raw delivery then explicit bags and isolated replay; STM32H7 owns real-time control/safety. No packages, public ROS interfaces, formats of historical evidence, upstream source, firmware, calibration or network configuration will change. New receipts use the existing stage/verdict/UTC/evidence_sha256 pattern. Rollback restores only modified preparation utilities from a local pre-edit archive or removes new files after comparing before.json; never reset either checkout.
