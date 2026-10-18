# N4A controlled timing experiment

This directory is an operator-copyable package for rerunning EuRoC MH01 stereo-inertial on the Pi while recording accuracy, latency, thermal, CPU-governor, cooling-device and `vcgencmd` evidence. It does not modify either reviewed dependency under `tools/eval_pipeline/accuracy/` or `tools/eval_pipeline/profile/`.

The package is software-only and has not been run against hardware here. Fixture tests passing means the orchestration and analysis logic works; it is not a Pi timing or project-gate PASS.

## Pi run

Copy this directory into the repository checkout on the Pi, make the entry points executable, and run from the repository root. Use the exact native ORB executable, vocabulary, settings, extracted MH01 dataset, and matching `EuRoC_TimeStamps/MH01.txt`:

```sh
chmod +x experiments/templates/n4a_timing/*.sh
bash experiments/templates/n4a_timing/run_n4a_timing.sh \
  --wait-for-cooldown --require-performance \
  /home/pi/orbslam3/ORB_SLAM3/Examples/Stereo-Inertial/stereo_inertial_euroc \
  /home/pi/orbslam3/ORB_SLAM3/Vocabulary/ORBvoc.txt \
  /home/pi/orbslam3/ORB_SLAM3/Examples/Stereo-Inertial/EuRoC.yaml \
  /home/pi/datasets/euroc/MH01 \
  /home/pi/orbslam3/ORB_SLAM3/Examples/Stereo-Inertial/EuRoC_TimeStamps/MH01.txt \
  MH01 3 /home/pi/wbr-evidence/n4a-timing-$(date -u +%Y%m%dT%H%M%SZ)
```

The command performs a preflight before starting ORB. A warm SoC may be given the bounded `--wait-for-cooldown` loop. Historical `vcgencmd get_throttled` bits refuse the experiment; `--allow-prior-throttle` is an explicit exception for diagnosis and causes affected runs to be excluded from the VALID aggregate. Use that exception only when the operator wants diagnostic evidence, not a clean rerun. `--preflight-only` records the checks without launching a sequence.

Then analyze the saved experiment on the Pi or Mac:

```sh
python3 experiments/templates/n4a_timing/analyze_n4a_timing.py \
  --experiment /home/pi/wbr-evidence/n4a-timing-YYYYMMDDTHHMMSSZ \
  --sequence MH01 \
  --ground-truth /home/pi/datasets/euroc/MH01/mav0/state_groundtruth_estimate0/data.csv \
  --times /home/pi/orbslam3/ORB_SLAM3/Examples/Stereo-Inertial/EuRoC_TimeStamps/MH01.txt
```

The analysis delegates EuRoC accuracy to `evaluate.py`, latency/validity to `profile.py`, and writes `summary.json` and `report.md`. A usable `events.csv` or `run_tracking.csv` must be emitted by the selected ORB/observer integration for latency percentiles; the resource sampler alone cannot invent per-frame latency. Missing traces are explicitly INVALID/BLOCKED rather than silently treated as zero.

## Evidence and criteria

Each experiment contains a copied `config.json`, `provenance.json`, `preflight.json`, raw preflight snapshots, one `runNN/` directory per repetition, runner output, sampler output and command metadata. The profiler uses Linux `CLOCK_MONOTONIC` for sampled intervals and records UTC only as a provenance anchor. EuRoC evaluation uses the dataset time base as documented by the accuracy tool; these clock domains are not subtracted.

Preflight criteria:

- `shared_orb_lock_available`: the reviewed accuracy runner's shared lock was available at the check; the runner acquires its own lock again for the actual invocation.
- `soc_temperature_below_start_limit`: the selected SoC thermal zone was strictly below the configured start limit.
- `no_prior_throttle_bits`: no configured current or historical under-voltage/frequency-cap/throttle/soft-temperature bit was reported, unless explicitly allowed.
- `cpu_governor_recorded`: governors are captured, and `--require-performance` makes any other governor refuse the run.
- `cooling_state_recorded`: every visible Linux cooling device is recorded; no devices is recorded as `NONE_FOUND`.

The profile validity gate marks latency evidence invalid when sampled throttle/voltage history is bad or telemetry is incomplete, and when sampled maximum SoC temperature reaches the profile limit. Accuracy criteria and threshold provenance remain in `tools/eval_pipeline/accuracy/thresholds.json`; profiling criteria remain in `tools/eval_pipeline/profile/config.json`. Package-specific orchestration limits and their source/rationale are in [config.json](config.json).

These checks cannot prove conditions between sampler polls, external power stability, firmware correctness, thermal hotspots, camera-to-host clock mapping, D435i calibration, image drops before ORB receives a frame, pose correctness, or an N4/N5/N7 project gate PASS. A clean fixture or one clean run is not sufficient evidence of sustained Pi behavior.

## Tests

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s experiments/templates/n4a_timing/tests -v 2>&1 \
  | tee experiments/templates/n4a_timing/tests/last-run.log
bash -n experiments/templates/n4a_timing/run_n4a_timing.sh
bash -n experiments/templates/n4a_timing/analyze_n4a_timing.sh
```

The tests use stub launcher/sampler processes and a compact fixture derived from the saved 2026-10-13 N4A throttle evidence. No camera, serial device, SSH, package installation or network access is used.
