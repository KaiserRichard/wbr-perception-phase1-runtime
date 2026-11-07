# WBR Perception, Phase 1

Perception and bench work for a wheel-bipedal robot (WBR), from September to early November 2026: Intel RealSense D435i bring-up on a Raspberry Pi 5, ORB-SLAM3 and RTAB-Map experiments, ROS 2 tools, calibration, and early simulation and control studies.

**Status:** archived working repository. Active simulation and control work has moved to [wheel-biped-sim](https://github.com/KaiserRichard/wheel-biped-sim). This repository keeps the Phase 1 code, experiment records and reviews as they were.

**Safety boundary:** the robot's STM32 owns balance, motor torque and safety. Nothing here commands real motors. Pi, learned, remote and simulated outputs only ever produce high-level references.

## Layout

| Folder | What's in it |
|---|---|
| [`calibration/`](calibration) | D435i IMU noise (Allan variance), AprilGrid targets, Kalibr lab scripts |
| [`docs/`](docs) | Architecture notes, bring-up guides, lessons, learning packs, proposals and reports |
| [`experiments/`](experiments) | Dated raw records of each hardware session: logs, rates, metadata |
| [`lab/`](lab) | Lab-day procedures and results, including the dated `lab-day-*` runbooks |
| [`ros2/`](ros2) | ROS 2 nodes: ORB-SLAM3 wrapper, obstacle node, planner, command bridge |
| [`sim/`](sim) | Simulation and control studies: five-bar leg, gain schedule, C controller, RL, MuJoCo twin |
| [`tools/`](tools) | Analysis and bench tools: bag tools, evaluation pipeline, link bench, IMU view, micro-ROS F446 |
| [`scripts/`](scripts) | Camera-day and laptop helper scripts |
| [`patches/`](patches) | Local patches applied to ORB-SLAM3 |
| [`research/`](research) | Roadmap, compute plan, literature scouting |
| [`ops/`](ops) | Work logs, reviews and the old task queue |
| [`tests/`](tests), [`.github/`](.github) | Fuzz tests and the CI test runner |
| [`third_party/`](third_party) | Submodules: ORB-SLAM3, ORB_SLAM3_ROS2, realsense-ros |
| [`docker/`](docker), [`data/`](data) | ROS 2 Jazzy tools image; empty placeholders for bags and datasets |

## Where to start

- [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md): hardware state and evidence, as of 14 Oct 2026
- [`docs/RPI5_NATIVE_PERCEPTION_BRINGUP.md`](docs/RPI5_NATIVE_PERCEPTION_BRINGUP.md): native Pi 5 perception bring-up
- [`docs/D435I_BASELINE_AUDIT.md`](docs/D435I_BASELINE_AUDIT.md): first D435i baseline audit
- [`docs/LAB_DAY_EXECUTION.md`](docs/LAB_DAY_EXECUTION.md): lab-day operator runbook
- [`research/ROADMAP.md`](research/ROADMAP.md): research roadmap, 31 Oct
- [`ops/worklog/CURRENT.md`](ops/worklog/CURRENT.md): last work-log summary

## Tests

```bash
bash tools/run_all_tests.sh
```

CI runs the same script on pushes and pull requests to `main`, skipping changes that only touch `docs/`, `ops/` or Markdown.

## Third-party code

ORB-SLAM3, ORB_SLAM3_ROS2 and realsense-ros are git submodules under `third_party/`, each under its own licence. `patches/orbslam3/` holds local changes to ORB-SLAM3.

## How this was made

Most code, experiments and write-ups were produced with AI coding assistants (ChatGPT, Codex and Claude) under the owner's direction, with reviews kept in `ops/worklog/reviews/`. Results labelled MEASURED were recorded on hardware or in simulation as stated in each file; everything else is assumed or calculated.
