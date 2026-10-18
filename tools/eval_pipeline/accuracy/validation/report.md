# EuRoC accuracy evaluation

Status: **PASS**

Sequence: MH01

EuRoC benchmark accuracy is not a D435i result. Primary ATE is rigid SE3 aligned; Sim3 is secondary and can absorb scale error.

| Run | Init | Poses | Pose fraction | ATE RMSE SE3 (m) | ATE RMSE Sim3 (m) | RPE 1 m translation RMSE (m) | RPE 10 frames translation RMSE (m) |
|---|---:|---:|---:|---:|---:|---:|---:|
| run1 | True | 3678 | 0.9989136338946225 | 0.041461 | 0.018874 | 0.01962504992901471 | 0.008716085540005119 |
| run2 | True | 3678 | 0.9989136338946225 | 0.036844 | 0.023794 | 0.0198845823104912 | 0.008902180897269671 |
| run3 | True | 3678 | 0.9989136338946225 | 0.041604 | 0.022288 | 0.020211385299225178 | 0.009165825859855661 |

Across-run SE3 ATE RMSE [CALCULATED]: mean 0.039969840384249604, population std 0.0022108260866934267, min 0.036844344136910095, max 0.041603882857669285 m.

Clock: estimate offset is explicitly zero. The dataset time-base assumption is source-supported for EuRoC files and does not map live camera clocks.
Tracking loss and map reset counts are stdout phrase counts; missing phrases do not prove no loss or resets. Pose fraction is an output row-count proxy.
This report does not prove hardware performance, calibration, D435i accuracy, or a project gate PASS. See summary.json for hashes, thresholds and evaluator provenance.
