# T3 DM live bench twin review and conductor handoff

The previous partial image copied the IMU bench and contained only a RobStride
codec. The completed default image now sends DM MIT/special frames on CAN1,
emulates hips 6/8 and wheels 0/1 on CAN2, forwards DM feedback, and simultaneously
provides the existing MPU6050 I-lines and TerrainAdvisory LED/echo receiver.
All edits and artifacts are confined to `tools/bench_twin_fw/`.

## Results and evidence labels

- **MEASURED, Mac build:** Arm GNU 14.2.1, warnings treated as errors, no undefined
  symbols; final size/hash and exact commands are in WORKLOG and VALIDATION.txt.
- **MEASURED, host only:** 10 unittest cases pass, including the actual C codec,
  model, text parser/formatter, advisory policy/multiplexing and canonical IMU
  viewer parsing. Reference C bodies compile unchanged into a temporary host
  library; 408 MIT payload vectors compare byte-for-byte, and 824 converter
  vectors match before separate clipping checks. Feedback is cross-checked
  against the reference decoders for all four IDs.
- **SOURCE-SUPPORTED:** DM wire ranges/packing and selected IDs cite the supplied
  DM-jump `6855ef8` snapshot by file:line in README. Hip IDs 6/8 appear on both
  real buses; this ticket deliberately selects the right pair and both wheels.
- **CALCULATED:** nominal 115200 8N1 transmit occupancy ≤79.410%, receive ≤27.865%
  at the **ASSUMED** envelope of 100 I-lines/s, 20 commands/replies/s aggregate,
  10 advisories and up to 20 echoes per second and one STAT/s.
- **ASSUMED:** combined four-motor bus topology, reply arbitration IDs `0x700+id`,
  fake dynamics/temperatures/state meanings and command pacing. This is
  **not micro-ROS, not AGV-ready, bench 500k**.

## Review boundaries and recommendation

**Recommendation:** review the source/reference tables and firmware integration,
then have the owner validate the image only on the isolated Nucleo fixture after
a verified current-flash backup. Preserve the raw UART evidence and counters.
No physical validation, flash, motor commands, Pi access, rendering or Git writes
were attempted by this worker. No PR is opened or merged by the worker.

The reference contains enable/disable but no save-zero opcode or configured
feedback arbitration IDs. Those facts are explicit instead of silently inventing
source support. Save-zero is not implemented. The raw DM state nibble is forwarded
in the requested `err` column; synthetic 1 means enabled in this model, not a
verified fault definition. Fake commands persist until changed/disabled; no real
motor safety claim is made. Latency/loss matching assumes one outstanding command
per ID and immediate isolated fake responses; DM feedback has no command sequence.

The UID-derived diagnostic session repeats after reboot. The host must reset
its state at BOOT. At higher traffic rates, output records can drop; counters
expose this. Physical 100 Hz delivery, interrupt/I2C coexistence, transceiver
wiring, CAN arbitration/ACK, timeout aborts, UART continuity and actual latency
remain unmeasured. The RobStride flag compiles a legacy codec only, with no
AGV velocity-mode lifecycle and no AGV runtime selection.

## Exact conductor commands remaining

These commands are for the conductor in the existing ticket branch. The worker
has already run the build/tests/lint; these reproduce validation before review.
No rendering is needed for this firmware ticket.

```sh
cd ~/Desktop/Research/wbr-wt-t3-fw
make -C tools/bench_twin_fw
python3 -m unittest discover -s tools/bench_twin_fw/tests -v
python3 tools/lint_markdown.py tools/bench_twin_fw/README.md tools/bench_twin_fw/WORKLOG.md tools/bench_twin_fw/REVIEW.md
(cd tools/bench_twin_fw/firmware && shasum -a 256 -c SHA256SUMS)
git add tools/bench_twin_fw
git diff --cached --stat
git commit -m "Add DM live bench twin firmware and reference host tests"
git push -u origin chatgpt/20261030-t3-bench-twin-fw
gh pr create --base main --head chatgpt/20261030-t3-bench-twin-fw --title "T3: DM live bench twin on F446" --body-file tools/bench_twin_fw/REVIEW.md
gh pr checks --watch
```

Only the conductor merges after green CI and review; no worker merge is pending.
Owner-only backup/BOOT0-before-RESET/flash/readback steps are in README, with no
worker flash command to execute.

Claude handoff line: Review `tools/bench_twin_fw/REVIEW.md` and README protocol
citations for the completed T3 DM bench milestone; Mac validation passes,
hardware operation remains unmeasured.
