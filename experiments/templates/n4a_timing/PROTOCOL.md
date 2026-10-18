# N4A timing rerun protocol

## Question and hypothesis

The experiment tests whether the native Raspberry Pi 5 ORB-SLAM3 stereo-inertial MH01 run can sustain EuRoC in real time under the intended operating conditions.

**Hypothesis [ASSUMED / TO BE TESTED]:** with active cooling and the 5 V / 5 A supply, the Pi 5 sustains EuRoC MH01 stereo-inertial at the declared camera rate without throttling, while retaining the established N4A accuracy behavior.

The hypothesis is falsified if the controlled run has a configured throttle or under-voltage bit, reaches the configured thermal validity limit, fails to provide a valid latency trace, cannot maintain the declared frame budget, fails inertial initialization, exits nonzero, or produces accuracy outside the proposed EuRoC criterion. A single failure is evidence against that run's claim; repeatable failure should drive the next power/cooling/runtime investigation.

## Fixed variables

- Pi model, OS image, ORB-SLAM3 revision/build, compatibility patches and runtime libraries.
- D435i is not used in this experiment; the input is the fixed official EuRoC MH01 dataset.
- EuRoC sequence, vocabulary, settings, timestamp file, executable invocation and headless mode.
- Run count, output layout, sampler cadence, preflight limits and inter-run cooldown from `config.json`.
- Active cooling arrangement and 5 V / 5 A supply for the complete run set.
- No other ORB pipeline, benchmark, recording job or heavy workload may run concurrently.

Record any deviation before the run; do not combine deviating runs with the controlled aggregate.

## Operator procedure

1. Confirm the Pi identity, power supply, active cooling, free storage, dataset checksums, ORB executable/library checksums and governor policy. Do not start if the supply or cooling setup is not the intended setup.
2. Confirm the exact command and output directory are new. Run `run_n4a_timing.sh`; it records host provenance and performs the shared-lock, temperature, throttle, governor and cooling preflight.
3. If temperature is high, `--wait-for-cooldown` permits only the bounded wait in `config.json`. If historical throttle bits are present, stop and correct the supply/cooling state. Use `--allow-prior-throttle` only for a separately labelled diagnostic rerun.
4. For each repetition the package invokes the reviewed `run_euroc.sh` for exactly one sequence, finds the exact ORB PID, starts the reviewed sampler against that PID, waits for the runner, stops the sampler so it flushes metadata, and applies the configured cooldown before the next repetition.
5. Preserve the complete experiment directory. Do not edit raw logs or replace missing telemetry with estimates.
6. Run `analyze_n4a_timing.py` with the exact EuRoC ground truth and timestamp files. Review each run and the count/reasons for exclusions before discussing aggregate metrics.

## Recorded evidence

The package records UTC labels for provenance, Linux monotonic sampler timestamps, process/resource samples, SoC thermal zones, cooling-device state, CPU governors, raw `vcgencmd` output, runner command/output/exit status, profiler command/output, hashes and the selected configuration. The analysis records accuracy metrics from the existing trajectory evaluator, latency P50/P95/P99 from the existing profile analysis, maximum sampled temperature, throttle validity and the VALID/INVALID decision.

## Interpretation

Only runs marked VALID contribute to the aggregate. Runs with throttle/under-voltage, incomplete resource telemetry, missing latency traces, nonzero engine exit, failed initialization or accuracy/tool analysis failure are excluded with explicit reasons. The aggregate is therefore the behavior of the subset that passed the declared evidence gate, not an imputation for excluded runs.

This protocol does not establish live D435i performance, camera/IMU clock mapping, calibration, storage throughput, pose correctness beyond EuRoC evaluation, or any later native perception gate. Timing from a sampler with no frame lifecycle trace is not a latency measurement.
