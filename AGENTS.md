# WBR Phase-1 engineering rules

The Mac checkout at `~/Desktop/Research/wbr-perception-phase1-runtime` is
canonical. The Raspberry Pi is a runtime and hardware-validation target.
Preserve existing work on both machines; deploy checksummed copies of Mac
utilities into a separate runtime bundle rather than resetting either checkout.

Before edits inspect Git status, current branch, recent history and relevant
files. Use feature branches; do not commit or push without explicit permission.
Major architecture, public API, node graph, message, build, dataset, experiment
format or report-structure changes require approval. Keep first-party experiment
utilities modular and preserve historical evidence unchanged. Document meaningful
changes, reproduction commands, test results, limitations and provenance.

Phase A is camera-free preparation. No camera-dependent command, camera process,
ORB-SLAM3, firmware/calibration change, or sensor capture may run until the user
explicitly says `CAMERA AVAILABLE`. Offline/synthetic tests prove tooling only.
Use the N1 → N2 → N3 gates in the Phase A runbook. Never weaken USB >=5000M,
the exact raw profile, timing thresholds or the mandatory 300-second N2 soak.
SDK device serial, ASIC serial, firmware-update ID and USB descriptor serial
are separate fields. Preserve calibration warnings and raw logs.

Keep acquisition local to the Pi; SSH is control only. Do not modify persistent
network configuration without approval. MicroSD is for OS, tools and small logs;
large datasets/bags require separately qualified storage. No broad device/sysfs
permissions. STM32H7 owns hard-real-time control and motor/jump safety.

Use English for code/comments/docs and the prompt language for explanations.
Test first-party behavior with offline/synthetic fixtures, label them explicitly,
and provide build/test/manual validation commands. Never expose credentials,
overwrite user work, modify upstream source to hide failures, or manufacture PASS.
