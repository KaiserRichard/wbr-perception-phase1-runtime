| Run | Align | ATE RMSE [m] | Mean [m] | Median [m] | Max [m] | RPE trans RMSE [m] | RPE rot RMSE [deg] | n pairs |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| run1 | se3 | 0.041461 | 0.038090 | 0.042723 | 0.081394 | 0.013295 | 0.076464 | 3639 |
| run1 | sim3 | 0.018874 | 0.016678 | 0.013880 | 0.047083 | 0.013233 | 0.076464 | 3639 |
| run2 | se3 | 0.036844 | 0.034089 | 0.036917 | 0.076001 | 0.013559 | 0.076776 | 3639 |
| run2 | sim3 | 0.023794 | 0.020977 | 0.017888 | 0.057120 | 0.013602 | 0.076776 | 3639 |
| run3 | se3 | 0.041604 | 0.038548 | 0.042754 | 0.087709 | 0.014021 | 0.074883 | 3639 |
| run3 | sim3 | 0.022288 | 0.020033 | 0.017256 | 0.054671 | 0.013999 | 0.074883 | 3639 |

Across-run statistics (unweighted, per alignment; null RPE runs excluded):

| Run | Align | ATE RMSE [m] | Mean [m] | Median [m] | Max [m] | RPE trans RMSE [m] | RPE rot RMSE [deg] | n pairs |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| across runs: mean | se3 | 0.039970 | 0.036909 | 0.040798 | 0.081701 | 0.013625 | 0.076041 | 3639.0 |
| across runs: mean | sim3 | 0.021652 | 0.019229 | 0.016341 | 0.052958 | 0.013611 | 0.076041 | 3639.0 |
| across runs: min | se3 | 0.036844 | 0.034089 | 0.036917 | 0.076001 | 0.013295 | 0.074883 | 3639 |
| across runs: min | sim3 | 0.018874 | 0.016678 | 0.013880 | 0.047083 | 0.013233 | 0.074883 | 3639 |
| across runs: max | se3 | 0.041604 | 0.038548 | 0.042754 | 0.087709 | 0.014021 | 0.076776 | 3639 |
| across runs: max | sim3 | 0.023794 | 0.020977 | 0.017888 | 0.057120 | 0.013999 | 0.076776 | 3639 |

Evidence label: CALCULATED
Assumptions (plain text):
clock_assumption: "EuRoC timestamps share one clock; offset 0 s."
est_frame: "imu_body"
ref_frame: "imu_body"
frames_differ_textually: false
extrinsics_applied: false
pose_convention: "active body-to-world rotations; translations in metres"
t_offset_s: "0"
t_offset_ns: 0
t_max_diff_s: "0.02"
t_max_diff_ns: 20000000
offset_convention: "add offset to estimate timestamps before association"
est_time_unit: "ns"
ref_time_unit: "ns"
alignments: ["se3", "sim3"]
n_to_align_requested: null
alignment_evaluation: "fit first n pairs, evaluate all associated pairs"
rpe_delta: "1"
rpe_unit: "s"
rpe_pair_selection: "one endpoint per start; frames: i+delta; s: first reference timestamp >= t_i+delta; m: first matched-reference cumulative distance >= d_i+delta; no interpolation"
rpe_convention: "E = (Ref_i^-1 Ref_j)^-1 (Est_i^-1 Est_j); global rigid alignment cancels; Sim3 scale is applied to estimate translations before RPE"
std_convention: "population (ddof=0)"
scope: "Does not establish frames, extrinsics, clock synchronization, sensor readiness or gate PASS."
estimate parsing: {"path": "/Users/quockaiser/Desktop/Research/wbr-perception-phase1-runtime/experiments/2026-10-13-n4a-euroc-mh01/run1/f_mh01_stereoi.txt", "sha256": "feb43173ca49a2b15eebfba98e3b06413800878fcfa6361fcff21c0dd5ca5ddb", "format": "orbslam3", "time_unit": "ns", "time_unit_source": "explicit", "timestamp_parser": "decimal.Decimal, no float round-trip; int64 nanoseconds", "sub_nanosecond_policy": "round to nearest nanosecond, ties to even (ROUND_HALF_EVEN)", "timestamps_rounded": 0, "max_rounding_ns": 0.0, "input_quaternion_order": "xyzw", "internal_quaternion_order": "xyzw", "quaternion_norm_tolerance": 0.001, "quaternion_max_norm_deviation": 1.1287192869247065e-07, "quaternion_normalized_after_validation": true}
reference parsing: {"path": "/Users/quockaiser/Desktop/Research/wbr-perception-phase1-runtime/experiments/2026-10-13-n4a-euroc-mh01/eval/gt_data.csv", "sha256": "aae2d7c5684724c8afe364d2fd8499a6ed77a9169adf03736531f67d8e7b2117", "format": "euroc_gt", "time_unit": "ns", "time_unit_source": "explicit", "timestamp_parser": "decimal.Decimal, no float round-trip; int64 nanoseconds", "sub_nanosecond_policy": "round to nearest nanosecond, ties to even (ROUND_HALF_EVEN)", "timestamps_rounded": 0, "max_rounding_ns": 0.0, "input_quaternion_order": "wxyz", "internal_quaternion_order": "xyzw", "quaternion_norm_tolerance": 0.001, "quaternion_max_norm_deviation": 6.754059313407446e-05, "quaternion_normalized_after_validation": true}
association: {"est_poses": 3678, "ref_poses": 36382, "matched_pairs": 3639, "unique_est_matched": 3639, "unique_ref_matched": 3639, "unmatched_est": 39, "unmatched_ref": 32743, "reference_sample_reused": false, "estimate_sample_reused": false, "reference_reuse_count": 0, "estimate_reuse_count": 0, "max_abs_dt_s": 0.02, "mean_abs_dt_s": 5.547229458642484e-06, "max_abs_dt_ns": 20000000, "iteration_side": "estimate", "semantics": "shorter-side nearest neighbour, inclusive tolerance, earliest tie, reuse allowed; equal lengths iterate reference", "t_offset_ns": 0, "t_max_diff_ns": 20000000}
trajectory: {"est_time_span": {"start_ns": 1403636579963555584, "end_ns": 1403636763813555456, "duration_s": 183.849999872}, "ref_time_span": {"start_ns": 1403636580838555648, "end_ns": 1403636762743555584, "duration_s": 181.904999936}, "est_offset_time_span": {"start_ns": 1403636579963555584, "end_ns": 1403636763813555456, "duration_s": 183.849999872}, "est_matched_time_span": {"start_ns": 1403636580863555584, "end_ns": 1403636762763555584, "duration_s": 181.9}, "ref_matched_time_span": {"start_ns": 1403636580863555328, "end_ns": 1403636762743555584, "duration_s": 181.880000256}, "duration_s": 181.880000256, "reference_length_matched_span_m": 80.60597718125896, "reference_matched_polyline_length_m": 80.52455433064866, "length_convention": "matched-span length includes all original reference poses between first and last matched reference; matched polyline uses associated samples only"}
plots: {"status": "created", "matplotlib_version": "3.10.9", "files": ["trajectory_xy_se3.png", "ate_over_time_se3.png", "rpe_over_time_se3.png", "trajectory_xy_sim3.png", "ate_over_time_sim3.png", "rpe_over_time_sim3.png"]}

Per-run parsing, hashes, alignment and warnings: each run/result.json.
