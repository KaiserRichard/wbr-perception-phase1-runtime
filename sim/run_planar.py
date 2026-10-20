"""Run balance, timed push and zero-control experiments; retain all artifacts."""

import argparse
import csv
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import subprocess
import sys
import traceback

import mujoco
import numpy as np

from sim.lqr import synthesize
from sim.planar import Plant, STATE_NAMES, load_config


ROOT = Path(__file__).resolve().parents[1]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def provenance(config_path):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()
    files = sorted(p for p in (ROOT / "sim").rglob("*")
                   if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    hashes = {str(p.relative_to(ROOT)): sha256(p.read_bytes()) for p in files}
    return {
        "git_commit": git("rev-parse", "HEAD"),
        "git_status": git("status", "--porcelain=v1"),
        "simulation_file_sha256": hashes,
        "simulation_tree_sha256": sha256(json.dumps(hashes, sort_keys=True).encode()),
        "config_sha256": sha256(config_path.read_bytes()),
        "python": sys.version, "platform": platform.platform(),
        "packages": {p: importlib.metadata.version(p) for p in ("mujoco", "numpy", "scipy", "matplotlib")},
        "command": [sys.executable, "-m", "sim.run_planar", *sys.argv[1:]],
        "evidence": "SIMULATION / ASSUMED physical model",
        "gain_parity": "PENDING independent learning work; not tested here",
    }


def evaluate(plant, K, scenario, out):
    p = plant.cfg["protocol"]
    dt = plant.cfg["simulation"]["dt_s"]
    d = plant.data(p["initial_state"])
    count = round(p["duration_s"] / dt)
    start = round(p["push_start_s"] / dt)
    end = start + round(p["push_duration_s"] / dt)
    rows, states, times = [], [], []
    saturation = np.zeros(2, int)
    peak_torque = np.zeros(2)
    impulse, pulse_steps = 0., 0
    fallen, numerical_failure = False, False
    fall_time = None
    header = ["time_s", *STATE_NAMES, "wheel_command_Nm", "hip_command_Nm",
              "wheel_applied_Nm", "hip_applied_Nm", "push_N", "interval_dt_s",
              "potential_J", "kinetic_J", "wheel_rolling_angle_rad"]
    # Stream samples so an unexpected error still leaves the preceding trajectory.
    with (out / f"{scenario}.csv").open("x", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        for step in range(count + 1):
            state = plant.state(d)
            time = float(d.time)
            numerical_failure |= (not np.all(np.isfinite(state)) or
                                  abs(time - step * dt) > 1e-9 or
                                  any(w.number for w in d.warning))
            tilt = np.rad2deg(max(abs(state[1:3])))
            fallen = bool(tilt >= p["fall_angle_deg"])
            if fallen and fall_time is None:
                fall_time = time
            terminal = (step == count or fallen or numerical_failure or
                        abs(state[0]) > p["max_displacement_m"])
            raw = np.zeros(2) if scenario == "open_loop" or terminal else -K @ state
            control = np.clip(raw, -plant.limits, plant.limits)
            push = p["push_force_N"] if scenario == "push" and start <= step < end and not terminal else 0.
            plant.forward(d, control, push)
            applied = d.actuator_force.copy()
            interval = 0. if terminal else dt
            row = [time, *state, *raw, *applied, push, interval, *d.energy,
                   state[0] / plant.cfg["physics"]["wheel_radius"]["value"]]
            writer.writerow(row)
            rows.append(row)
            states.append(state)
            times.append(time)
            if terminal:
                break
            saturation += np.abs(raw - control) > 1e-12
            peak_torque = np.maximum(peak_torque, abs(applied))
            impulse += push * dt
            pulse_steps += int(push != 0)
            mujoco.mj_step(plant.model, d)
    states, times = np.array(states), np.array(times)
    numerical_failure |= any(w.number for w in d.warning)
    tol = np.asarray(p["state_abs_tolerance"])
    inside = np.all(np.abs(states) <= tol, axis=1)
    settled_suffix = np.logical_and.accumulate(inside[::-1])[::-1]
    event_end = p["push_start_s"] + p["push_duration_s"] if scenario == "push" else 0.
    candidates = np.flatnonzero(settled_suffix & (times >= event_end - 1e-9))
    recovered_at = float(times[candidates[0]]) if len(candidates) else None
    recovery_time = recovered_at - event_end if recovered_at is not None else None
    full_duration = bool(abs(times[-1] - p["duration_s"]) < 1e-9)
    window = times >= p["duration_s"] - p["settle_window_s"] - 1e-9
    held_final = bool(full_duration and np.any(window) and np.all(inside[window]))
    caps_ok = bool(np.all(peak_torque <= plant.limits + 1e-12))
    pulse_ok = scenario != "push" or (
        pulse_steps == end - start and
        abs(impulse - p["push_force_N"] * p["push_duration_s"]) < 1e-10
    )
    peak_tilt = float(np.rad2deg(np.max(np.abs(states[:, 1:3]))))
    growth = peak_tilt / np.rad2deg(max(abs(np.asarray(p["initial_state"])[1:3])))
    if scenario == "open_loop":
        passed = (fallen and fall_time <= p["open_loop_fall_deadline_s"] and
                  growth >= p["open_loop_min_tilt_growth"] and
                  not np.any(peak_torque) and not numerical_failure)
    else:
        passed = (full_duration and not fallen and not numerical_failure and caps_ok and
                  pulse_ok and held_final and recovery_time is not None and
                  recovery_time <= p["recovery_deadline_s"])
    result = {
        "status": "PASS" if passed else "FAIL", "scenario": scenario,
        "duration_s": float(times[-1]), "integration_steps": len(times) - 1,
        "initial_state": states[0].tolist(), "final_error": states[-1].tolist(),
        "peak_tilt_deg": peak_tilt,
        "peak_leg_tilt_deg": float(np.rad2deg(max(abs(states[:, 1])))),
        "peak_body_tilt_deg": float(np.rad2deg(max(abs(states[:, 2])))),
        "peak_tilt_after_push_start_deg": (
            float(np.rad2deg(np.max(np.abs(states[times >= p["push_start_s"] - 1e-9, 1:3]))))
            if scenario == "push" and np.any(times >= p["push_start_s"] - 1e-9) else None
        ),
        "peak_displacement_m": float(max(abs(states[:, 0]))),
        "tilt_growth_factor": float(growth),
        "fallen": fallen, "fall_time_s": fall_time,
        "recovery_time_after_event_s": recovery_time, "held_final_window": held_final,
        "final_window_max_abs_error": np.max(np.abs(states[window]), axis=0).tolist() if np.any(window) else None,
        "push_start_s": p["push_start_s"] if scenario == "push" else None,
        "push_duration_applied_s": pulse_steps * dt, "push_impulse_Ns": float(impulse),
        "push_force_N": p["push_force_N"] if scenario == "push" else 0.,
        "full_declared_pulse_applied": bool(pulse_ok),
        "saturated_steps_per_input": saturation.tolist(),
        "saturation_duration_per_input_s": (saturation * dt).tolist(),
        "peak_applied_torque_Nm": peak_torque.tolist(),
        "actuator_limits_Nm": plant.limits.tolist(), "caps_respected": caps_ok,
        "numerical_failure": bool(numerical_failure),
        "mujoco_warning_counts": [int(w.number) for w in d.warning],
        "trajectory": f"{scenario}.csv",
    }
    return result, np.array(rows)


def plot_runs(out, runs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(4, 3, figsize=(13, 10), sharex="col")
    for col, (name, rows) in enumerate(runs.items()):
        axes[0, col].set_title(name)
        axes[0, col].plot(rows[:, 0], np.rad2deg(rows[:, 2:4]), label=["leg", "body"])
        axes[1, col].plot(rows[:, 0], rows[:, 1])
        axes[2, col].plot(rows[:, 0], rows[:, 9:11], label=["wheel", "hip"])
        axes[3, col].plot(rows[:, 0], rows[:, 11])
        axes[3, col].set_xlabel("Time (s)")
        axes[0, col].legend()
        axes[2, col].legend()
        for ax in axes[:, col]:
            ax.grid(True, alpha=0.3)
    for ax, label in zip(axes[:, 0], ["Pitch (deg)", "Wheel x (m)", "Applied torque (N m)", "Body force (N)"]):
        ax.set_ylabel(label)
    fig.suptitle("ASSUMED reduced planar WBR / NEW LQR / ideal rolling / no gain-parity claim")
    fig.tight_layout()
    fig.savefig(out / "trajectories.png", dpi=150)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="New directory outside repository; never overwritten")
    args = parser.parse_args(argv)
    out = args.out.resolve()
    if out == ROOT or ROOT in out.parents:
        parser.error("--out must be outside the repository")
    out.mkdir(parents=True, exist_ok=False)
    result = {"status": "ERROR"}
    try:
        cfg = load_config(args.config)
        result["provenance"] = provenance(args.config)
        write_json(out / "config.json", cfg)
        plant = Plant(cfg)
        (out / "model.xml").write_text(plant.xml)
        result["model_sha256"] = sha256(plant.xml.encode())
        result["model_dimensions"] = {"nq": plant.model.nq, "nv": plant.model.nv, "nu": plant.model.nu}
        K, synthesis = synthesize(plant)
        write_json(out / "linearization.json", synthesis)
        result["scenarios"] = {}
        runs = {}
        for name in ("balance", "push", "open_loop"):
            metrics, rows = evaluate(plant, K, name, out)
            result["scenarios"][name] = metrics
            runs[name] = rows
            write_json(out / f"{name}.json", metrics)
            print(f"{name.upper()} {metrics['status']}: peak tilt={metrics['peak_tilt_deg']:.3f} deg, "
                  f"recovery={metrics['recovery_time_after_event_s']}, fallen={metrics['fallen']}", flush=True)
        plot_runs(out, runs)
        result["status"] = "PASS" if all(v["status"] == "PASS" for v in result["scenarios"].values()) else "FAIL"
        result["artifact_sha256"] = {p.name: sha256(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()}
    except Exception:
        result["error"] = traceback.format_exc()
        (out / "error.txt").write_text(result["error"])
        print(result["error"], file=sys.stderr)
    write_json(out / "result.json", result)
    print(f"Artifacts: {out}", flush=True)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
