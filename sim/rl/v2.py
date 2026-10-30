"""Lean direct/residual PPO, with an unchanged 500 Hz AugmentedRuntime.

Run: python -m sim.rl.v2 smoke|run --out NEW_DIR
Reissue a run command to resume between seeds/episodes. Completed artifacts are
validated and reused; interrupted/failed training attempts are never overwritten
or automatically retrained. A final checkpoint can finish pending evaluation.
"""

import argparse
from dataclasses import replace
from functools import lru_cache, partial
import json
import os
from pathlib import Path
import time
import traceback

# Spawned workers must not each create a BLAS thread pool.
for _variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                  "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_variable] = "1"

import gymnasium as gym
import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.logger import configure
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv, VecNormalize

from sim.augmented import AugmentedRuntime, load_experiment
from sim.augmented_lqr import synthesize_augmented
from sim.rl.environment import ROOT, NumericalFailure, encode_observation, load_protocol
from sim.rl.metrics import PHYSICAL, missing_policy


CONFIG = Path(__file__).with_name("v2_config.json")


def load_config():
    return json.loads(CONFIG.read_text())


def write_json(path, value):
    """Atomic small status updates; no trajectory hashing or capture."""
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def single_thread():
    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != 1:
        torch.set_num_interop_threads(1)


@lru_cache(maxsize=1)
def lqr_gains():
    """The existing delay-aware design, synthesized once in the parent."""
    p = load_protocol()
    base, experiment, effects = load_experiment(ROOT / p["plant_contract"]["config"])
    return {d: synthesize_augmented(base, replace(effects, delay_s=d),
                                   np.asarray(experiment["frozen_nominal"]["K"]))[0]
            for d in p["plant"]["fixed_delays_s"]}


class CompactEpisode:
    """500 Hz samples plus per-tick reductions, sufficient for v1 metrics."""

    def __init__(self, runtime):
        self.times = [runtime.time]
        self.truth = [runtime.truth()]
        self.noise = [runtime.sensor_noise()]
        self.rows = []

    def append(self, result, runtime):
        segments = result.intervals
        dt = np.asarray([s.dt_s for s in segments])
        states = np.asarray([s.truth_start for s in segments])
        mean = np.asarray([s.applied_mean for s in segments])
        force = np.asarray([s.push_N for s in segments])
        self.rows.append({
            "command_Nm": result.clipped,
            "requested_Nm": result.requested,
            "actual_dt_s": float(dt.sum()),
            "state_squared_integral": np.sum(states**2 * dt[:, None], axis=0),
            "applied_effort": np.sum([s.torque_squared_integral for s in segments], axis=0),
            "applied_mean_effort": np.sum(mean**2 * dt[:, None], axis=0),
            "peak_applied": np.maximum(np.max(np.abs([s.torque_start for s in segments]), axis=0),
                                       np.max(np.abs([s.torque_end for s in segments]), axis=0)),
            "peak_applied_mean": np.max(abs(mean), axis=0),
            "push_impulse": float(force @ dt),
            "push_duration": float(dt[force != 0].sum()),
            "integration_steps": len(segments),
        })
        self.times.append(runtime.time)
        self.truth.append(runtime.truth())
        self.noise.append(runtime.sensor_noise())

    def arrays(self):
        result = {k: np.asarray([r[k] for r in self.rows]) for k in self.rows[0]} if self.rows else {}
        return {**result, "times_s": np.asarray(self.times), "truth": np.asarray(self.truth),
                "noise": np.asarray(self.noise)}

    def save(self, path):
        with Path(path).open("xb") as stream:
            np.savez_compressed(stream, **self.arrays())


class V2Env(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, arm="direct", policy_seed=0, rank=0, config=None, gains=None,
                 record=False):
        if arm not in ("direct", "residual"):
            raise ValueError("Expected direct or residual arm")
        self.arm, self.policy_seed, self.rank = arm, int(policy_seed), int(rank)
        self.config = load_config() if config is None else config
        self.protocol = load_protocol()
        self.base, _, self.effects = load_experiment(ROOT / self.protocol["plant_contract"]["config"])
        self.dt = self.base["simulation"]["dt_s"]
        self.max_ticks = round(self.protocol["scenarios"][0]["duration_s"] / self.dt)
        self.limits = np.asarray(self.protocol["plant"]["torque_limits_Nm"], float)
        self.q = np.asarray(self.protocol["reward"]["Q_diagonal"])
        self.r = np.asarray(self.protocol["reward"]["R_diagonal"])
        self.gains = (lqr_gains() if gains is None else gains) if arm == "residual" else None
        self.action_space = gym.spaces.Box(-1., 1., shape=(2,), dtype=np.float32)
        self.observation_space = gym.spaces.Box(-np.inf, np.inf, shape=(15,), dtype=np.float64)
        self.record = record
        self.capture = None
        self._runtimes = {}
        self._reset_rng(self.policy_seed)
        self._ended = True
        self.total_plant_ticks = self.total_policy_steps = 0

    def _reset_rng(self, seed):
        self._conditions = np.random.default_rng(np.random.SeedSequence(
            [self.config["training"]["condition_rng_domain"], int(seed), self.rank]))
        self._episode_index = 0

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self._reset_rng(seed)
        p, c = self.protocol, self.config["training"]
        if not options:
            rng = self._conditions
            delay = float(rng.choice(p["plant"]["fixed_delays_s"]))
            state = np.zeros(6)
            state[1:3] = np.deg2rad(rng.uniform(-c["initial_angle_abs_deg"],
                                              c["initial_angle_abs_deg"], size=2))
            force = float(rng.choice([-1., 1.]) * rng.uniform(*c["push_magnitude_range_N"]))
            start = round(rng.uniform(*c["push_start_range_s"]) / self.dt)
            duration = round(c["push_duration_s"] / self.dt)
            if self._episode_index >= c["noise_seed_stride"]:
                raise ValueError("Training noise seed range exhausted")
            noise_seed = (c["noise_seed_base"] +
                          (self.policy_seed*c["n_envs"] + self.rank)*c["noise_seed_stride"] +
                          self._episode_index)
            scenario = "random_push"
        else:
            if set(options) != {"delay_s", "scenario", "noise_seed"}:
                raise ValueError("Fixed evaluation needs delay_s, scenario, noise_seed")
            delay, scenario, noise_seed = (options[k] for k in ("delay_s", "scenario", "noise_seed"))
            cases = {s["name"]: s for s in p["scenarios"]}
            if scenario not in cases:
                raise ValueError("Unknown evaluation scenario")
            case = cases[scenario]
            state = np.asarray(case["initial_state"], float)
            pulse = case["push"]
            force = pulse["force_N"] if pulse else 0.
            start = round(pulse["start_s"] / self.dt) if pulse else 0
            duration = round((pulse["end_exclusive_s"] - pulse["start_s"]) / self.dt) if pulse else 0
        if delay not in p["plant"]["fixed_delays_s"]:
            raise ValueError("Delay outside the frozen panel")
        self.delay_s, self.scenario, self.noise_seed = delay, scenario, int(noise_seed)
        self.push_force, self.push_start, self.push_end = force, start, start + duration
        if delay not in self._runtimes:
            self._runtimes[delay] = AugmentedRuntime(self.base, replace(self.effects, delay_s=delay))
        self.runtime = self._runtimes[delay]
        self._observation = self.runtime.reset(state=state, seed=self.noise_seed)
        self._tick, self._ended = 0, False
        self.capture = CompactEpisode(self.runtime) if self.record else None
        info = {"delay_s": delay, "scenario": scenario, "noise_seed": self.noise_seed,
                "initial_state": state.tolist(), "push_force_N": force,
                "push_start_tick": start, "push_duration_ticks": duration}
        self._episode_index += 1
        return encode_observation(self._observation, p), info

    def step(self, action):
        if self._ended:
            raise RuntimeError("Call reset before stepping a finished episode")
        action = np.asarray(action, float)
        if action.shape != (2,) or not np.all(np.isfinite(action)):
            raise NumericalFailure("Nonfinite or malformed policy action")
        held = np.clip(action, -1., 1.) * self.limits
        if self.arm == "residual":
            held *= self.config["residual_cap_fraction"]
        costs = []
        terminated = truncated = False
        for _ in range(self.config["policy_hold_ticks"]):
            # Feedback is ONLY the cached common causal observation. Truth below
            # belongs to reward/termination, never to this controller.
            command = held if self.arm == "direct" else (
                -self.gains[self.delay_s] @ self._observation.vector() + held)
            force = self.push_force if self.push_start <= self._tick < self.push_end else 0.
            result = self.runtime.step(np.clip(command, -self.limits, self.limits), push_N=force)
            self._tick += 1
            self.total_plant_ticks += 1
            self._observation = result.observation
            state = self.runtime.truth()
            if (not np.all(np.isfinite(state)) or any(self.runtime.warning_counts) or
                    abs(self.runtime.time - self._tick*self.dt) > 1e-9):
                self._ended = True
                raise NumericalFailure("Nonfinite state, MuJoCo warning/reset or invalid time")
            cost = float(state**2 @ self.q + result.clipped**2 @ self.r)
            if not np.isfinite(cost):
                raise NumericalFailure("Nonfinite quadratic cost")
            costs.append(cost)
            if self.capture is not None:
                self.capture.append(result, self.runtime)
            p = self.protocol["acceptance"]
            terminated = bool(np.rad2deg(max(abs(state[1:3]))) >= p["fall_angle_deg"] or
                              abs(state[0]) > p["max_displacement_m"])
            truncated = bool(self._tick >= self.max_ticks and not terminated)
            if terminated or truncated:
                break
        self._ended = terminated or truncated
        self.total_policy_steps += 1
        r = self.config["reward"]
        reward = r["alive"] - r["cost_scale"]*float(np.mean(costs))
        reward -= r["physical_termination_penalty"] if terminated else 0.
        return (encode_observation(self._observation, self.protocol), reward, terminated, truncated,
                {"plant_ticks": len(costs)})


def compact_metrics(a, scenario, error=None):
    """Same v1 acceptance/metrics; substep integrals were reduced per plant tick."""
    p = load_protocol()
    acceptance = p["acceptance"]
    states, times = a["truth"], a["times_s"]
    if len(times) < 2 or not np.all(np.isfinite(states)):
        return {**dict.fromkeys(PHYSICAL), "status": "EVALUATION_FAILED", "success": False,
                "survived": False, "fall_count": 0, "training_failure_count": 0,
                "numerical_failure_count": 1, "other_failure_count": 0,
                "unrecovered_count": 1, "penalized_recovery_s": 10., "control_steps": 0,
                "failure_reasons": [error or "No finite completed plant ticks"]}
    duration, actual_dt = float(times[-1]), float(a["actual_dt_s"].sum())
    full = abs(duration - p["scenarios"][0]["duration_s"]) < 1e-9
    inside = np.all(abs(states) <= acceptance["state_abs_tolerance"], axis=1)
    window = times >= 10. - acceptance["settle_window_s"] - 1e-9
    held = bool(full and np.any(window) and np.all(inside[window]))
    event_end = 3.15 if scenario == "push" else 0.
    settled = np.logical_and.accumulate(inside[::-1])[::-1]
    candidates = np.flatnonzero(settled & (times >= event_end - 1e-9))
    recovery = float(times[candidates[0]] - event_end) if full and held and len(candidates) else None
    falls = np.flatnonzero(np.rad2deg(np.max(abs(states[:, 1:3]), axis=1)) >= acceptance["fall_angle_deg"])
    fall_time = float(times[falls[0]]) if len(falls) else None
    limits = np.asarray(p["plant"]["torque_limits_Nm"])
    peak_torque = a["peak_applied"].max(axis=0)
    peak_mean = a["peak_applied_mean"].max(axis=0)
    commands = a["command_Nm"]
    caps = bool(np.all(np.maximum(peak_torque, peak_mean) <= limits + 1e-12) and
                np.all(abs(commands) <= limits + 1e-12))
    impulse, pulse_duration = float(a["push_impulse"].sum()), float(a["push_duration"].sum())
    pulse_ok = scenario != "push" or (abs(impulse - .9) < 1e-10 and abs(pulse_duration - .15) < 1e-10)
    displacement = float(np.max(abs(states[:, 0])))
    checks = {"numerics": error is None, "caps": caps, "full_duration": full,
              "no_fall": fall_time is None, "displacement": displacement <= acceptance["max_displacement_m"],
              "full_pulse": pulse_ok, "held_final_window": held,
              "recovery_deadline": recovery is not None and recovery <= acceptance["recovery_deadline_s"]}
    success = all(checks.values())
    integrated = a["state_squared_integral"].sum(axis=0)
    # v1 saturation and command effort use elapsed control time, not the
    # independently accumulated substep durations.
    control_dt = np.diff(times)
    saturation = np.sum((abs(commands) >= limits - 1e-12)*control_dt[:, None], axis=0)
    post = times >= 3. - 1e-9
    return {
        "status": "PASS" if success else "FAIL", "success": success, "checks": checks,
        "survived": bool(full and fall_time is None and checks["displacement"] and checks["numerics"]),
        "failure_reasons": [k for k, v in checks.items() if not v] + ([error] if error else []),
        "physical_metrics_reason": None, "duration_s": duration, "sum_actual_dt_s": actual_dt,
        "control_steps": len(commands), "integration_steps": int(a["integration_steps"].sum()),
        "final_error": states[-1].tolist(), "state_squared_error_integral": integrated.tolist(),
        "state_rmse": np.sqrt(integrated/actual_dt).tolist(),
        "final_window_max_abs_error": np.max(abs(states[window]), axis=0).tolist() if np.any(window) else None,
        "peak_leg_tilt_deg": float(np.rad2deg(np.max(abs(states[:, 1])))),
        "peak_body_tilt_deg": float(np.rad2deg(np.max(abs(states[:, 2])))),
        "peak_tilt_deg": float(np.rad2deg(np.max(abs(states[:, 1:3])))),
        "peak_tilt_after_push_start_deg": float(np.rad2deg(np.max(abs(states[post, 1:3]))))
            if scenario == "push" and np.any(post) else None,
        "peak_displacement_m": displacement, "fall_count": int(fall_time is not None),
        "fall_observed": fall_time is not None, "fall_time_s": fall_time,
        "training_failure_count": 0, "numerical_failure_count": int(error is not None),
        "other_failure_count": int(not success and fall_time is None and error is None),
        "recovery_time_after_event_s": recovery, "recovery_time_successes_s": recovery if success else None,
        "unrecovered_count": int(recovery is None), "penalized_recovery_s": recovery if recovery is not None else 10.,
        "push_impulse_Ns": impulse, "push_duration_applied_s": pulse_duration,
        "command_effort_Nm2_s": np.sum(commands**2*control_dt[:, None], axis=0).tolist(),
        "applied_effort_Nm2_s": a["applied_effort"].sum(axis=0).tolist(),
        "applied_mean_effort_Nm2_s": a["applied_mean_effort"].sum(axis=0).tolist(),
        "peak_command_torque_Nm": np.max(abs(commands), axis=0).tolist(),
        "peak_applied_torque_Nm": peak_torque.tolist(), "peak_applied_mean_torque_Nm": peak_mean.tolist(),
        "command_saturation_duration_s": saturation.tolist(),
        "command_saturation_fraction": (saturation/actual_dt).tolist(), "noise_samples": len(a["noise"]),
    }


class ReportWorkerFailure(gym.Wrapper):
    """Send a worker traceback to the parent, which aborts before learning it.

    SB3's subprocess loop otherwise dies on an environment exception, losing the
    reason and potentially blocking close(). This sentinel is never a rollout
    sample: Progress raises before SB3 adds the transition to its buffer.
    """

    def step(self, action):
        try:
            return self.env.step(action)
        except Exception:
            return (np.zeros(self.observation_space.shape), 0., True, False,
                    {"plant_ticks": 0, "worker_error": traceback.format_exc()})


def make_worker(arm, seed, rank, config, gains):
    single_thread()
    return ReportWorkerFailure(V2Env(arm, seed, rank, config, gains))


def make_vector(arm, seed, config, gains):
    env = SubprocVecEnv([partial(make_worker, arm, seed, rank, config, gains)
                        for rank in range(config["training"]["n_envs"])], start_method="spawn")
    return VecNormalize(env, **config["vecnormalize"])


def load_frozen(folder, arm, config=None, gains=None):
    """Restore final policy and saved observation statistics, with no updates."""
    config = load_config() if config is None else config
    raw = DummyVecEnv([lambda: V2Env(arm, config=config, gains=gains)])
    try:
        norm = VecNormalize.load(Path(folder) / "vecnormalize.pkl", raw)
        norm.training = False
        norm.norm_reward = False
        if not norm.norm_obs:
            raise ValueError("Missing saved observation normalization")
        model = PPO.load(Path(folder) / "final.zip", device="cpu")
        model.policy.set_training_mode(False)
        return model, norm
    except BaseException:
        raw.close()
        raise


class Progress(BaseCallback):
    def __init__(self, out, budget):
        super().__init__()
        self.out, self.budget = out, budget
        self.plant_ticks = 0
        self.started = time.perf_counter()
        self.last_write = 0.

    def _on_step(self):
        errors = [info["worker_error"] for info in self.locals["infos"] if "worker_error" in info]
        if errors:
            raise NumericalFailure("Subprocess environment failure:\n" + "\n".join(errors))
        self.plant_ticks += sum(info["plant_ticks"] for info in self.locals["infos"])
        elapsed = time.perf_counter() - self.started
        if elapsed - self.last_write >= 10. or self.num_timesteps == self.budget:
            write_json(self.out / "progress.json", {
                "policy_transitions": self.num_timesteps, "target": self.budget,
                "plant_ticks": self.plant_ticks, "elapsed_s": elapsed,
                "policy_transitions_per_second": self.num_timesteps/elapsed})
            self.last_write = elapsed
        return True


def train_seed(arm, seed, out, config, smoke=False, gains=None):
    out = Path(out)
    hyper = {**load_protocol()["ppo_hyperparameters"], **config["ppo_overrides"]}
    rollout_size = hyper["n_steps"]*config["training"]["n_envs"]
    budget = (config["smoke"]["rollouts"]*rollout_size if smoke
              else config["training"]["policy_transitions_per_seed"])
    if out.exists():
        status = json.loads((out / "status.json").read_text()) if (out / "status.json").exists() else {}
        if (status.get("status") == "COMPLETE" and status.get("policy_transitions") == budget
                and status.get("smoke") == smoke and status.get("arm") == arm
                and status.get("seed") == seed):
            model, norm = load_frozen(out, arm, config, gains)
            try:
                if model.num_timesteps != budget or model.n_envs != config["training"]["n_envs"]:
                    raise ValueError("Saved model budget/environment count mismatch")
            finally:
                norm.close()
            return status
        raise FileExistsError(f"Retained incomplete/failed attempt; no automatic retry: {out}")
    out.mkdir(parents=True)
    started = time.perf_counter()
    status = {"arm": arm, "seed": seed, "status": "RUNNING", "smoke": smoke,
              "counts_as_training_seed": not smoke, "policy_transitions": 0, "budget": budget,
              "n_envs": config["training"]["n_envs"], "failure_reasons": []}
    write_json(out / "status.json", status)
    vec = model = None
    progress = Progress(out, budget)
    try:
        if budget % rollout_size:
            raise ValueError("Budget must contain exactly complete PPO rollouts")
        single_thread()
        vec = make_vector(arm, seed, config, gains)
        kwargs = dict(load_protocol()["ppo_policy_kwargs"])
        kwargs.update(activation_fn=torch.nn.Tanh, optimizer_class=torch.optim.Adam)
        model = PPO("MlpPolicy", vec, seed=seed, device="cpu", policy_kwargs=kwargs, **hyper)
        model.set_logger(configure(str(out / "optimizer"), ["csv"]))
        before = {k: v.detach().clone() for k, v in model.policy.state_dict().items()}
        model.learn(total_timesteps=budget, callback=progress)
        changed = any(not torch.equal(before[k], v) for k, v in model.policy.state_dict().items())
        if not changed or any(not torch.isfinite(v).all() for v in model.policy.state_dict().values()):
            raise NumericalFailure("Optimizer failed to update finite parameters")
        if model.num_timesteps != budget or progress.plant_ticks > budget*config["policy_hold_ticks"]:
            raise ValueError("Policy/plant budget mismatch")
        model.save(out / "final.zip")
        vec.save(out / "vecnormalize.pkl")
        loaded, frozen = load_frozen(out, arm, config, gains)
        try:
            probe = np.linspace(-1., 1., 15).reshape(1, -1)
            np.testing.assert_array_equal(vec.normalize_obs(probe), frozen.normalize_obs(probe))
            np.testing.assert_array_equal(model.predict(vec.normalize_obs(probe), deterministic=True)[0],
                                          loaded.predict(frozen.normalize_obs(probe), deterministic=True)[0])
            if any(not torch.equal(value, loaded.policy.state_dict()[key])
                   for key, value in model.policy.state_dict().items()):
                raise ValueError("Policy checkpoint reload mismatch")
        finally:
            frozen.close()
        # SB3 logs before train(); dump once more to retain the LAST update too.
        model.logger.dump(step=model.num_timesteps)
        status.update(status="COMPLETE", optimizer_updated=changed, optimizer_epochs=model._n_updates,
                      rollouts=budget//rollout_size, checkpoint_reload="PASS")
    except Exception as exc:
        status.update(status="FAILED", failure_reasons=[f"{type(exc).__name__}: {exc}"])
        (out / "error.txt").write_text(traceback.format_exc())
    finally:
        status.update(policy_transitions=model.num_timesteps if model else 0,
                      plant_ticks=progress.plant_ticks, elapsed_s=time.perf_counter() - started)
        write_json(out / "status.json", status)
        if vec is not None:
            if status["status"] == "COMPLETE":
                vec.close()
            else:
                # Only this seed's own subprocesses. A broken pipe/worker can
                # leave SB3 waiting for a reply that will never arrive.
                raw = vec.venv
                for process in raw.processes:
                    if process.is_alive():
                        process.terminate()
                for process in raw.processes:
                    process.join(timeout=2)
                for remote in raw.remotes:
                    remote.close()
                raw.closed = True
    return status


def evaluation_panel():
    p = load_protocol()
    return [{"delay_s": d, "scenario": s["name"], "noise_seed": n}
            for d in p["plant"]["fixed_delays_s"] for s in p["scenarios"]
            for n in p["evaluation"]["noise_seeds"]]


def episode_key(case):
    return f'd{round(case["delay_s"]*1000)}-{case["scenario"]}-n{case["noise_seed"]}'


def evaluate_seed(arm, seed, folder, config, smoke=False, gains=None, missing=None):
    folder = Path(folder)
    directory = folder / "evaluation"
    directory.mkdir(exist_ok=True)
    panel = evaluation_panel()
    if smoke:
        panel = panel[:config["smoke"]["evaluation_cases_per_arm"]]
    model = norm = env = None
    if missing is None:
        try:
            model, norm = load_frozen(folder, arm, config, gains)
            env = V2Env(arm, config=config, gains=gains, record=True)
        except Exception as exc:
            missing = f"Final checkpoint load failed: {type(exc).__name__}: {exc}"
            (directory / "load-error.txt").write_text(traceback.format_exc())
    outcomes = []
    started = time.perf_counter()
    try:
        for case in panel:
            key = episode_key(case)
            metric_path, raw_path = directory / f"{key}.json", directory / f"{key}.npz"
            identity = {"controller": arm, "policy_seed": seed, **case}
            if metric_path.exists():
                result = json.loads(metric_path.read_text())
                if any(result.get(k) != v for k, v in identity.items()):
                    raise ValueError(f"Existing episode identity mismatch: {metric_path}")
                if not raw_path.exists() and result["status"] not in ("MISSING_POLICY", "EVALUATION_FAILED"):
                    raise ValueError(f"Missing compact trajectory: {raw_path}")
                outcomes.append(result)
                continue
            if missing:
                result = {**missing_policy(missing), "survived": False, **identity}
            elif raw_path.exists():
                # Interrupted between the atomic NPZ close and metrics write.
                # An unmarked raw file is retained but cannot establish success.
                result = {**missing_policy("Interrupted evaluation; raw retained, no automatic rerun"),
                          "status": "EVALUATION_FAILED", "training_failure_count": 0,
                          "other_failure_count": 1, "survived": False, **identity}
            else:
                error = None
                env.capture = None  # A failed reset must not reuse the prior episode.
                try:
                    obs, _ = env.reset(options=case)
                    while True:
                        action, _ = model.predict(norm.normalize_obs(obs), deterministic=True)
                        obs, _, terminated, truncated, _ = env.step(action)
                        if terminated or truncated:
                            break
                except Exception as exc:
                    error = f"{type(exc).__name__}: {exc}"
                    (directory / f"{key}-error.txt").write_text(traceback.format_exc())
                arrays = env.capture.arrays() if env.capture is not None else {
                    "times_s": np.array([]), "truth": np.empty((0, 6))}
                result = {**compact_metrics(arrays, case["scenario"], error), **identity}
                if env.capture is not None:
                    env.capture.save(raw_path)
            write_json(metric_path, result)
            outcomes.append(result)
            write_json(directory / "progress.json", {"episodes": len(outcomes), "expected": len(panel),
                       "elapsed_s": time.perf_counter() - started})
        write_json(directory / "outcomes.json", outcomes)
    finally:
        if norm is not None:
            norm.close()
        if env is not None:
            env.close()
    return outcomes


def should_extend(outcomes):
    return any(r["scenario"] == "balance" and r["status"] == "PASS"
               and r["success"] and r["policy_seed"] in (0, 1, 2) for r in outcomes)


def summarize(outcomes):
    return {"episodes": len(outcomes), "strict_successes": sum(r["success"] for r in outcomes),
            "survivals": sum(r["survived"] for r in outcomes),
            **{k: sum(r[k] for r in outcomes) for k in (
                "fall_count", "training_failure_count", "numerical_failure_count", "other_failure_count")},
            "balance_passes": sum(r["success"] and r["scenario"] == "balance" for r in outcomes)}


def experiment(out, smoke=False):
    """Sequential seeds, eight subprocess environments; never 40 training workers."""
    import fcntl  # Unix experiment supervisor; portable runner uses its own lock.

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    # Released by the OS on exit/crash; leave file intact to avoid unlink races.
    with (out / "run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        config, protocol = load_config(), load_protocol()
        declaration = {"config": config, "v1_protocol": protocol, "smoke": smoke}
        path = out / "run.json"
        if path.exists():
            if json.loads(path.read_text()) != declaration:
                raise ValueError("Existing run declaration differs; use a new directory")
        else:
            if any(p.name != "run.lock" for p in out.iterdir()):
                raise FileExistsError("Undeclared existing output directory")
            write_json(path, declaration)
        gains = lqr_gains()
        started = time.perf_counter()
        all_outcomes, statuses = {}, {}

        def run_one(arm, seed):
            folder = out / arm / f"seed-{seed}"
            print(f"{'SMOKE' if smoke else 'FULL'} {arm} seed {seed}", flush=True)
            try:
                status = train_seed(arm, seed, folder, config, smoke, gains)
            except Exception as exc:
                status = {"status": "FAILED", "failure_reasons": [f"{type(exc).__name__}: {exc}"]}
            statuses[f"{arm}-{seed}"] = status
            missing = "; ".join(status["failure_reasons"]) if status["status"] != "COMPLETE" else None
            rows = evaluate_seed(arm, seed, folder, config, smoke, gains, missing)
            all_outcomes.setdefault(arm, []).extend(rows)
            write_json(out / "progress.json", {"seeds": statuses,
                       "panels": {a: summarize(r) for a, r in all_outcomes.items()},
                       "elapsed_s": time.perf_counter() - started})

        initial = [0] if smoke else config["training"]["initial_seeds"]
        # Both arms' initial stage completes before any extension starts.
        for seed in initial:
            for arm in config["arms"]:
                run_one(arm, seed)
        extensions = {arm: not smoke and should_extend(all_outcomes[arm]) for arm in config["arms"]}
        for arm in config["arms"]:
            if extensions[arm]:
                for seed in config["training"]["extension_seeds"]:
                    run_one(arm, seed)
        failed = (any(s["status"] != "COMPLETE" for s in statuses.values()) or
                  any(r["status"] == "EVALUATION_FAILED" or r["numerical_failure_count"]
                      or r["training_failure_count"]
                      for rows in all_outcomes.values() for r in rows))
        report = {"status": "COMPLETE_WITH_FAILURES" if failed else "COMPLETE",
                  "smoke": smoke, "counts_as_training_run": not smoke, "extensions": extensions,
                  "seeds": statuses, "panels": {a: summarize(r) for a, r in all_outcomes.items()},
                  "seed_panels": {
                      f"{arm}-{seed}": summarize([r for r in rows if r["policy_seed"] == seed])
                      for arm, rows in all_outcomes.items()
                      for seed in sorted({r["policy_seed"] for r in rows})},
                  "lqr_baseline": "Not rerun; prior unchanged 500 Hz LQR panel remains the v1 reference",
                  "elapsed_s": time.perf_counter() - started}
        write_json(out / "status.json", report)
        print(json.dumps({k: report[k] for k in ("status", "smoke", "panels", "elapsed_s")}), flush=True)
        return int(failed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "run"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    return experiment(args.out, smoke=args.command == "smoke")


if __name__ == "__main__":
    raise SystemExit(main())
