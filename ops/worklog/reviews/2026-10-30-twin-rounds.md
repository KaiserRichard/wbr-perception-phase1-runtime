# 2026-10-30 twin rounds (Codex workers, Claude verifies)

- Round 1: #168 scene_twin (codex-e), #169 tilt/jump research (codex-e), #170 tilt_sweep (codex-j), #171 wbr_pose leg animation (codex-g). All tests pass. Renders were redone outside the sandbox and inspected.
- Round 2: #172 jump_gate (codex-k), 22 tests. The SYNTHETIC jump at 20 s turns STOP into UNCERTAIN (c = 0) for 20.00–21.42 s.
- Round 3: #173 foxglove_twin (codex-k), 12 tests. The twin MCAP overlaps the 3-box13 camera bag by 59.0 s.
- MEASURED on synthetic data (#170): plane-fit height MAE 0.21 mm (486 scenes) vs 121 mm with a fixed mount. The IMU's value is visibility and timing, not height correction.
- Stack: #166 is the base. #168, #171, #172 and #173 build on it. #169 and #170 are independent. Nothing is merged.
- Codex sandbox: cannot commit, push or render (CGL). The conductor did those steps for every PR.
- agy: three failed runs (flag order, `--effort` on Opus, then quota). Retry after the reset.
- Open: owner check in the Foxglove GUI; the DM-jump phi1/phi4 convention is unverified (#171); real IMU/contact telemetry is needed in November.
- Round 4: #174 simcam (codex-k): scenario JSON → MuJoCo depth → the real detector → jump gate. #175 sim_scenarios (codex-e): 13 scenarios, 12/12 scored PASS after the conductor fixed the contract (`jump_at_s` = CROUCH start; range measured from the camera; tiny box 0.015 m).
- Found in simulation: the ±2 m floor edge produced false STOPs (fixed). The box leaves the view within ~0.32 m of the camera (mount 3° down, 0.21 m, ASSUMED); round 5 studies the mount. A flicker at 0.020 m was a floor-edge artifact and is retracted.
- Round 5 (running): simcam driven by the owner's live IMU recording (archived at `~/wbr-evidence-archive/imu-view-live-20261030/`, codex-k), and the camera mount study (codex-e).
- Round 5: #176 simcam_imu (codex-k). The live IMU (38–44 s window, scale 0.3, about ±8°) keeps geometry correct (1.8 mm) but the advisory is about 80 % UNCERTAIN. Causes: the gate's 5 °/s threshold and simcam wiping history outside STAND. #177 mount_study (codex-e), 54 renders: simulated blind zone 0.125–0.275 m, some values held/optimistic, far range not measured. The D435's ~0.28 m minimum depth (UNKNOWN) probably dominates.
- Round 6 (running): gate fix (codex-k). History resets only around jumps; wobble scales confidence down instead of exiting STAND. Acceptance: re-run simcam_imu and 12/12 scenarios.
- Round 6: #178 gate fix (codex-k). On the live IMU window gated STOP is 38/48 (was 8 raw), confidence 0.52–1.0. Scenarios 12/12 PASS. Jump windows were aligned to the gate spec in #175: the earlier pass came from the history wipe.
- Stack (merge order): #166 → #168 → #171 → #172 → #173 → #174 → #176 → #178; #175 and #177 sit on #174; #169 and #170 are independent. 13 PRs open, none merged.
