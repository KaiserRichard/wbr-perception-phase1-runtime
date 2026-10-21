"""Controller-neutral evaluation on the unchanged nominal protocol.

Controllers are callables of Observation only. Truth is used here for safety,
acceptance/error/effort reporting, never passed as privileged feedback.
"""

import csv
from dataclasses import asdict
import hashlib

import numpy as np

from sim.planar import STATE_NAMES
from sim.run_planar import write_json


def _finite_summary(values):
    """Use JSON null for unavailable components; keep finite values unchanged."""
    values = np.asarray(values)
    return np.where(np.isfinite(values), values, None).tolist()


def evaluate(runtime, controller, scenario, seed, out):
    """Stream one rollout to a NEW directory; return true-state metrics."""
    out.mkdir(parents=True, exist_ok=False)
    p, dt = runtime.plant.cfg["protocol"], runtime.dt
    count = round(p["duration_s"] / dt)
    start = round(p["push_start_s"] / dt)
    end = start + round(p["push_duration_s"] / dt)
    obs = runtime.reset(seed=seed)
    states, times = [], []
    impulse, pulse_duration, total_dt = 0., 0., 0.
    integrated_error = np.zeros(6)
    torque_effort, applied_effort, command_effort = np.zeros(2), np.zeros(2), np.zeros(2)
    saturation_duration, peak_torque, peak_mean = np.zeros(2), np.zeros(2), np.zeros(2)
    interval_count, noise_hash = 0, hashlib.sha256()
    numerical_failure, fall_time = False, None
    observation_names = [f"measured_{n}" for n in STATE_NAMES] + [
        "wheel_torque_estimate_Nm", "hip_torque_estimate_Nm"]
    observation_names += [f"previous_{i}_{actuator}_command_Nm"
                          for i in range(1, runtime.history_steps+1) for actuator in ("wheel", "hip")]
    with (out / "control.csv").open("x", newline="") as cf, (out / "intervals.csv").open("x", newline="") as sf:
        controls, segments = csv.writer(cf), csv.writer(sf)
        controls.writerow(["time_s", *STATE_NAMES, *observation_names,
                           "body_angle_noise_rad", "body_gyro_noise_rad_s",
                           "wheel_requested_Nm", "hip_requested_Nm", "wheel_clipped_Nm",
                           "hip_clipped_Nm", "wheel_torque_Nm", "hip_torque_Nm", "interval_dt_s"])
        segments.writerow(["time_s", "interval_dt_s", "wheel_applied_mean_Nm", "hip_applied_mean_Nm",
                           "wheel_torque_start_Nm", "hip_torque_start_Nm", "wheel_torque_end_Nm",
                           "hip_torque_end_Nm", "wheel_delayed_Nm", "hip_delayed_Nm",
                           "source_submitted_s", "push_N"])
        for tick in range(count+1):
            truth, time = runtime.truth(), runtime.time
            states.append(truth)
            times.append(time)
            numerical_failure |= bool(not np.all(np.isfinite(truth)) or
                                      abs(time - tick*dt) > 1e-9 or any(runtime.warning_counts))
            fallen = bool(np.rad2deg(max(abs(truth[1:3]))) >= p["fall_angle_deg"])
            if fallen and fall_time is None:
                fall_time = time
            terminal = (tick == count or fallen or numerical_failure or
                        abs(truth[0]) > p["max_displacement_m"])
            noise = runtime.sensor_noise()
            noise_hash.update(np.asarray(noise, dtype="<f8").tobytes())
            raw = np.zeros(2) if terminal or scenario == "open_loop" else np.asarray(controller(obs))
            clipped = np.clip(raw, -runtime.limits, runtime.limits)
            row = [time, *truth, *obs.vector(), *noise, *raw, *clipped, *runtime.torque()]
            if terminal:
                controls.writerow([*row, 0.])
                break
            push = p["push_force_N"] if scenario == "push" and start <= tick < end else 0.
            result = runtime.step(raw, push_N=push)
            elapsed = runtime.time-time
            controls.writerow([*row, elapsed])
            saturation_duration += (abs(raw-clipped) > 1e-12) * elapsed
            command_effort += clipped**2 * elapsed
            for segment in result.intervals:
                h = segment.dt_s
                segments.writerow([segment.time_s, h, *segment.applied_mean, *segment.torque_start,
                                   *segment.torque_end, *segment.delayed_command,
                                   segment.source_submitted_s, segment.push_N])
                impulse += segment.push_N*h
                pulse_duration += h if segment.push_N else 0.
                total_dt += h
                interval_count += 1
                integrated_error += segment.truth_start**2 * h
                torque_effort += segment.torque_squared_integral
                applied_effort += segment.applied_mean**2 * h
                peak_torque = np.maximum(peak_torque, np.maximum(abs(segment.torque_start),
                                                                abs(segment.torque_end)))
                peak_mean = np.maximum(peak_mean, abs(segment.applied_mean))
            obs = result.observation
    states, times = np.asarray(states), np.asarray(times)
    inside = np.all(abs(states) <= np.asarray(p["state_abs_tolerance"]), axis=1)
    settled = np.logical_and.accumulate(inside[::-1])[::-1]
    event_end = p["push_start_s"]+p["push_duration_s"] if scenario == "push" else 0.
    candidates = np.flatnonzero(settled & (times >= event_end-1e-9))
    recovery = float(times[candidates[0]]-event_end) if len(candidates) else None
    full_duration = bool(abs(times[-1]-p["duration_s"]) < 1e-9)
    window = times >= p["duration_s"]-p["settle_window_s"]-1e-9
    held = bool(full_duration and np.any(window) and np.all(inside[window]))
    caps_ok = bool(np.all(np.maximum(peak_torque, peak_mean) <= runtime.limits+1e-12))
    pulse_ok = scenario != "push" or (
        abs(pulse_duration-p["push_duration_s"]) < 1e-10 and
        abs(impulse-p["push_force_N"]*p["push_duration_s"]) < 1e-10)
    peak_tilt = float(np.rad2deg(np.max(abs(states[:, 1:3]))))
    growth = peak_tilt/np.rad2deg(max(abs(np.asarray(p["initial_state"])[1:3])))
    checks = {"numerics": not numerical_failure, "caps": caps_ok}
    if scenario == "open_loop":
        checks.update(fall_by_deadline=fall_time is not None and fall_time <= p["open_loop_fall_deadline_s"],
                      tilt_growth=growth >= p["open_loop_min_tilt_growth"],
                      zero_torque=not np.any(peak_torque) and not np.any(peak_mean))
    else:
        checks.update(full_duration=full_duration, no_fall=fall_time is None,
                      displacement=bool(np.max(abs(states[:, 0])) <= p["max_displacement_m"]),
                      full_pulse=pulse_ok, held_final_window=held,
                      recovery_deadline=recovery is not None and recovery <= p["recovery_deadline_s"])
    checks = {key: bool(value) for key, value in checks.items()}
    metrics = {
        "status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
        "failed_checks": [key for key, passed in checks.items() if not passed],
        "scenario": scenario, "seed": seed, "runtime": asdict(runtime.config),
        "duration_s": float(times[-1]), "sum_actual_dt_s": total_dt,
        "control_steps": len(times)-1, "integration_steps": interval_count,
        "initial_state": _finite_summary(states[0]), "final_error": _finite_summary(states[-1]),
        "final_window_max_abs_error": _finite_summary(np.max(abs(states[window]), axis=0)) if np.any(window) else None,
        "state_squared_error_integral": _finite_summary(integrated_error),
        "state_rmse_over_actual_duration": _finite_summary(np.sqrt(integrated_error/total_dt)) if total_dt else None,
        "peak_tilt_deg": _finite_summary(peak_tilt),
        "peak_tilt_after_push_start_deg": _finite_summary(np.rad2deg(np.max(abs(states[
            times >= p["push_start_s"]-1e-9, 1:3])))) if scenario == "push" and
            np.any(times >= p["push_start_s"]-1e-9) else None,
        "peak_displacement_m": _finite_summary(np.max(abs(states[:, 0]))),
        "fallen": fall_time is not None, "fall_time_s": fall_time,
        "recovery_time_after_event_s": recovery, "held_final_window": held,
        "push_impulse_Ns": impulse, "push_duration_applied_s": pulse_duration,
        "full_declared_pulse_applied": bool(pulse_ok),
        "saturation_duration_per_input_s": saturation_duration.tolist(),
        "peak_physical_torque_Nm": peak_torque.tolist(), "peak_applied_mean_torque_Nm": peak_mean.tolist(),
        "torque_squared_integral_Nm2_s": torque_effort.tolist(),
        "applied_mean_squared_integral_Nm2_s": applied_effort.tolist(),
        "clipped_command_squared_integral_Nm2_s": command_effort.tolist(),
        "caps_respected": caps_ok, "numerical_failure": numerical_failure,
        "mujoco_warning_counts": runtime.warning_counts,
        "noise_stream_sha256_float64_le": noise_hash.hexdigest(),
        "noise_samples": len(times), "acceptance_basis": "TRUE six-state errors; nominal thresholds unchanged",
        "controller_input": "cached noisy body pitch/rate; ideal other coordinates; causal torque/history",
    }
    write_json(out / "metrics.json", metrics)
    return metrics
