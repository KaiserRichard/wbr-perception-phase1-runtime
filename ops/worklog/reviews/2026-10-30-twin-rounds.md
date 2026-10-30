# 2026-10-30 twin rounds (Codex workers, Claude verifies)

- Round 1: #168 scene_twin (codex-e), #169 tilt/jump research (codex-e), #170 tilt_sweep (codex-j), #171 wbr_pose leg animation (codex-g). All tests pass. Renders were redone outside the sandbox and inspected.
- Round 2: #172 jump_gate (codex-k), 22 tests. The SYNTHETIC jump at 20 s turns STOP into UNCERTAIN (c = 0) for 20.00–21.42 s.
- Round 3: #173 foxglove_twin (codex-k), 12 tests. The twin MCAP overlaps the 3-box13 camera bag by 59.0 s.
- MEASURED on synthetic data (#170): plane-fit height MAE 0.21 mm (486 scenes) vs 121 mm with a fixed mount. The IMU's value is visibility and timing, not height correction.
- Stack: #166 is the base. #168, #171, #172 and #173 build on it. #169 and #170 are independent. Nothing is merged.
- Codex sandbox: cannot commit, push or render (CGL). The conductor did those steps for every PR.
- agy: three failed runs (flag order, `--effort` on Opus, then quota). Retry after the reset.
- Open: owner check in the Foxglove GUI; the DM-jump phi1/phi4 convention is unverified (#171); real IMU/contact telemetry is needed in November.
