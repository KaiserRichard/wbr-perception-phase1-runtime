"""Approved residual-only bounded pilot; no full-run or direct-arm entry point.

Run ``python -m sim.rl.v3_pilot diagnostic|run --help``.
V2 plant stepping, causal observations, held residuals and acceptance are reused.
Artifacts are small and external: config/source, episodes, updates, snapshots,
16-case development outcomes and plots. Failed attempts are never overwritten.
"""

import argparse
from contextlib import contextmanager
from copy import deepcopy
from functools import partial
import math
import json
from pathlib import Path
import random
import subprocess
import time
import traceback

from sim.rl import v2  # Sets thread limits before numerical-library imports.
import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.logger import configure
from stable_baselines3.common.vec_env import SubprocVecEnv, VecEnvWrapper, VecMonitor, VecNormalize

from sim.rl.environment import ROOT, NumericalFailure, encode_observation, load_protocol

CONFIG = Path(__file__).with_name("v3_pilot_config.json")
STATE_NAMES = ("x", "leg", "body", "xdot", "legdot", "bodydot")


def settings():
    return json.loads(CONFIG.read_text())


def beta_for_tolerances(protocol=None):
    p = load_protocol() if protocol is None else protocol
    fraction = settings()["reward"]["minimum_isolated_tolerance_penalty"]
    costs = np.asarray(p["reward"]["Q_diagonal"]) * np.asarray(
        p["acceptance"]["state_abs_tolerance"])**2
    return float(fraction / ((1 - fraction) * min(costs)))


def bounded_reward(cost, terminated=False, *, beta=None, termination_penalty=None):
    if not np.isfinite(cost) or cost < 0:
        raise NumericalFailure("Bounded reward needs finite nonnegative cost")
    beta = beta_for_tolerances() if beta is None else beta
    penalty = settings()["reward"]["termination_penalty"] if termination_penalty is None else termination_penalty
    # Algebraically identical to 1/(1+beta*cost), but finite costs near the
    # float64 limit must still earn a strictly positive surviving reward.
    base = (1. / (1. + beta * cost) if cost <= 1. else
            (1. / cost) / (beta + 1. / cost))
    return base - penalty * float(terminated)


class PilotEnv(v2.V2Env):
    """Same residual plant loop, with bounded reward and additive diagnostics."""

    def __init__(self, seed=42, rank=0, gains=None, record=False):
        super().__init__("residual", seed, rank, gains=gains, record=record)
        self.beta = beta_for_tolerances(self.protocol)
        self.termination_penalty = settings()["reward"]["termination_penalty"]
        self.episode_terms = {}

    def reset(self, **kwargs):
        result = super().reset(**kwargs)
        self.episode_terms = {k: 0. for k in (
            "alive", "precision_loss", "fall", "residual_penalty", "sim_seconds",
            *STATE_NAMES, "command")}
        return result

    def _tick_cost(self, state, result):
        components = np.r_[state**2 * self.q, result.clipped**2 @ self.r]
        self._components.append(components)
        return float(state**2 @ self.q + result.clipped**2 @ self.r)

    def _reward(self, costs, terminated):
        mean_cost = math.fsum(float(c) / len(costs) for c in costs)
        base = bounded_reward(mean_cost, beta=self.beta, termination_penalty=self.termination_penalty)
        mean_terms = np.sum(np.asarray(self._components) / len(costs), axis=0)
        # This allocation reconstructs the nonlinear loss exactly. Raw costs
        # remain separately named; they are not additive reward penalties.
        losses = mean_terms / mean_cost * (1. - base) if mean_cost else np.zeros(7)
        self._terms = {"alive": 1., "precision_loss": 1. - base,
                       "fall": self.termination_penalty * float(terminated), "residual_penalty": 0.,
                       **dict(zip(STATE_NAMES, mean_terms[:6].tolist())),
                       "command": float(mean_terms[6])}
        self._losses = losses.tolist()
        return base - self._terms["fall"]

    def step(self, action):
        self._components = []
        # Frozen v2 loop copied locally so v2 source/results stay untouched.
        # Only cost instrumentation and the final reward differ.
        if self._ended:
            raise RuntimeError("Call reset before stepping a finished episode")
        action = np.asarray(action, float)
        if action.shape != (2,) or not np.all(np.isfinite(action)):
            raise NumericalFailure("Nonfinite or malformed policy action")
        held = np.clip(action, -1., 1.) * self.limits
        held *= self.config["residual_cap_fraction"]
        costs = []
        terminated = truncated = False
        for _ in range(self.config["policy_hold_ticks"]):
            command = -self.gains[self.delay_s] @ self._observation.vector() + held
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
            cost = self._tick_cost(state, result)
            if not np.isfinite(cost):
                self._ended = True
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
        reward = self._reward(costs, terminated)
        obs = encode_observation(self._observation, self.protocol)
        info = {"plant_ticks": len(costs)}
        for key, value in self._terms.items():
            self.episode_terms[key] += value
        self.episode_terms["sim_seconds"] += info["plant_ticks"] * self.dt
        for index, value in enumerate(self._losses):
            key = "loss_" + (*STATE_NAMES, "command")[index]
            self.episode_terms[key] = self.episode_terms.get(key, 0.) + value
        info.update(reward_terms=self._terms, allocated_losses=self._losses)
        if terminated or truncated:
            info["episode_terms"] = dict(self.episode_terms)
        return obs, reward, terminated, truncated, info


class WorkerFailureGuard(VecEnvWrapper):
    """Reject failure sentinels before monitor metadata or learning sees them."""

    def reset(self):
        return self.venv.reset()

    def step_wait(self):
        result = self.venv.step_wait()
        errors = [info["worker_error"] for info in result[3] if "worker_error" in info]
        if errors:
            raise NumericalFailure("Worker failed before learning: " + "\n".join(errors))
        return result


class PreciseVecMonitor(VecMonitor):
    """Keep long raw episode sums in float64, not SB3's float32 accumulator."""

    def __init__(self, venv, **kwargs):
        super().__init__(WorkerFailureGuard(venv), **kwargs)

    def reset(self):
        obs = super().reset()
        self.episode_returns = self.episode_returns.astype(np.float64)
        return obs


def make_worker(seed, rank, gains):
    v2.single_thread()
    return v2.ReportWorkerFailure(PilotEnv(seed, rank, gains))


def make_vector(gains):
    seed = settings()["seed"]
    factories = [partial(make_worker, seed, rank, gains) for rank in range(8)]
    raw = SubprocVecEnv(factories, start_method="spawn")
    # Raw environmental episode returns, before observation normalization and
    # before SB3 adds timeout value bootstrap to its learning targets.
    monitored = PreciseVecMonitor(raw, info_keywords=("episode_terms",))
    return VecNormalize(monitored, **v2.load_config()["vecnormalize"])


def zero_actor_mean(model):
    with torch.no_grad():
        model.policy.action_net.weight.zero_()
        model.policy.action_net.bias.zero_()


def physical_upright(delay):
    """Fixed-divisor encoded physical upright, not a zero normalized NN input."""
    obs = np.zeros(15)
    obs[-1] = delay / load_protocol()["policy_input"]["delay_divisor_s"]
    return obs



@contextmanager
def preserve_training_rng():
    """SB3 checkpoint loading reseeds global RNGs; isolate evidence operations."""
    python_state = random.getstate()
    numpy_state = deepcopy(np.random.get_state())
    torch_state = torch.random.get_rng_state().clone()
    try:
        yield
    finally:
        random.setstate(python_state)
        np.random.set_state(numpy_state)
        torch.random.set_rng_state(torch_state)


@preserve_training_rng()
def save_snapshot(folder, model, norm):
    folder.mkdir()
    model.save(folder / "final.zip")
    norm.save(folder / "vecnormalize.pkl")
    probe = np.stack([physical_upright(d) for d in load_protocol()["plant"]["fixed_delays_s"]])
    original = model.predict(norm.normalize_obs(probe), deterministic=True)[0]
    loaded, frozen = v2.load_frozen(folder, "residual", gains=v2.lqr_gains())
    try:
        np.testing.assert_array_equal(norm.normalize_obs(probe), frozen.normalize_obs(probe))
        np.testing.assert_array_equal(original, loaded.predict(frozen.normalize_obs(probe), deterministic=True)[0])
    finally:
        frozen.close()
    return folder



@preserve_training_rng()
def verify_zero_initialization(model, norm, snapshot, gains):
    """Prove actual normalized actor/reloaded actor match 500 Hz LQR exactly.

    A short fixed trajectory checks the composed policy+normalizer+runtime,
    beyond literal-zero-action or equilibrium-only checks. No optimization.
    """
    loaded, frozen = v2.load_frozen(snapshot, "residual", gains=gains)
    rows = []
    try:
        for delay in load_protocol()["plant"]["fixed_delays_s"]:
            actual = PilotEnv(gains=gains, record=True)
            reloaded = PilotEnv(gains=gains, record=True)
            baseline = v2.V2Env("residual", gains=gains, record=True)
            try:
                case = {"delay_s": delay, "scenario": "balance", "noise_seed": 2000}
                obs, _ = actual.reset(options=case)
                restored, _ = reloaded.reset(options=case)
                reference, _ = baseline.reset(options=case)
                np.testing.assert_array_equal(obs, reference)
                for _ in range(3):
                    action = model.predict(norm.normalize_obs(obs), deterministic=True)[0]
                    restored_action = loaded.predict(frozen.normalize_obs(restored), deterministic=True)[0]
                    np.testing.assert_array_equal(action, np.zeros(2))
                    np.testing.assert_array_equal(restored_action, np.zeros(2))
                    obs, _, terminated, truncated, _ = actual.step(action)
                    restored, _, restored_done, restored_timeout, _ = reloaded.step(restored_action)
                    reference, _, baseline_done, baseline_timeout, _ = baseline.step([0., 0.])
                    np.testing.assert_array_equal(obs, reference)
                    np.testing.assert_array_equal(restored, reference)
                    if ((terminated, truncated) != (baseline_done, baseline_timeout) or
                            (restored_done, restored_timeout) != (baseline_done, baseline_timeout)):
                        raise NumericalFailure("Zero-policy termination flags differ from LQR")
                for key in ("truth", "command_Nm", "noise", "times_s"):
                    np.testing.assert_array_equal(actual.capture.arrays()[key], baseline.capture.arrays()[key])
                    np.testing.assert_array_equal(reloaded.capture.arrays()[key], baseline.capture.arrays()[key])
                rows.append({"delay_s": delay, "plant_ticks": actual.total_plant_ticks,
                             "constructed_policy_parity": "PASS", "reloaded_policy_parity": "PASS"})
            finally:
                actual.close()
                reloaded.close()
                baseline.close()
    finally:
        frozen.close()
    return {"status": "PASS", "cases": rows}

def development_panel():
    p = load_protocol()
    return [{"delay_s": d, "scenario": case["name"], "noise_seed": n}
            for d in p["plant"]["fixed_delays_s"] for case in p["scenarios"]
            for n in settings()["development_noise_seeds"]]


def case_key(row):
    return v2.episode_key(row)


@preserve_training_rng()
def evaluate_snapshot(folder, gains):
    """Fresh fixed 16-case development panel; no held-out panel or tuning."""
    model, norm = v2.load_frozen(folder, "residual", gains=gains)
    env = PilotEnv(gains=gains, record=True)
    before = deepcopy(norm.obs_rms)
    tolerance = np.asarray(load_protocol()["acceptance"]["state_abs_tolerance"])
    rows = []
    started = time.monotonic()
    try:
        for case in development_panel():
            error = None
            env.capture = None
            try:
                obs, _ = env.reset(options=case)
                while True:
                    action, _ = model.predict(norm.normalize_obs(obs), deterministic=True)
                    obs, _, done, truncated, _ = env.step(action)
                    if done or truncated:
                        break
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
            arrays = env.capture.arrays() if env.capture is not None else {
                "times_s": np.array([]), "truth": np.empty((0, 6))}
            row = {**case, **v2.compact_metrics(arrays, case["scenario"], error)}
            if row["duration_s"] is not None and row["duration_s"] >= 10 - 1e-9:
                window = arrays["times_s"] >= 9 - 1e-9
                row["E"] = float(np.max(abs(arrays["truth"][window]) / tolerance))
                row["leg_rate_violation"] = bool(np.any(abs(arrays["truth"][window, 4]) > tolerance[4]))
            else:
                row.update(E=None, leg_rate_violation=True)
            rows.append(row)
            v2.write_json(folder / "development.json", {"outcomes": rows,
                          "expected": 16, "elapsed_s": time.monotonic() - started})
        np.testing.assert_array_equal(before.mean, norm.obs_rms.mean)
        np.testing.assert_array_equal(before.var, norm.obs_rms.var)
        assert before.count == norm.obs_rms.count
    finally:
        env.close()
        norm.close()
    return summarize_panel(rows)


def summarize_panel(rows):
    expected = {case_key(r) for r in development_panel()}
    actual = [case_key(r) for r in rows]
    complete = len(rows) == 16 and len(set(actual)) == 16 and set(actual) == expected
    E = [r.get("E") for r in rows]
    return {"complete": complete, "strict": sum(bool(r.get("success")) for r in rows),
            "survived": sum(bool(r.get("survived")) for r in rows),
            "leg_rate_violations": sum(bool(r.get("leg_rate_violation", True)) for r in rows),
            "E": float(np.mean(E)) if complete and all(v is not None and np.isfinite(v) for v in E) else None}


def stop_boundary(transitions, elapsed):
    c = settings()
    return (elapsed >= c["maximum_training_seconds"] or
            (transitions >= c["target_policy_transitions"] and elapsed >= c["minimum_training_seconds"]))


class Telemetry(BaseCallback):
    """Records sampled exploration separately from the deterministic mean."""

    def __init__(self, out):
        super().__init__()
        self.out = Path(out)
        self.plant_ticks = 0
        self.episode_rows = []
        self.update_rows = []
        self.samples = []

    def _on_rollout_start(self):
        self.samples = []

    def _on_step(self):
        infos = self.locals["infos"]
        errors = [i["worker_error"] for i in infos if "worker_error" in i]
        if errors:
            raise NumericalFailure("Worker failed before learning: " + "\n".join(errors))
        self.plant_ticks += sum(i["plant_ticks"] for i in infos)
        raw = np.asarray(self.locals["actions"])
        with torch.no_grad():
            distribution = self.model.policy.get_distribution(self.locals["obs_tensor"])
            mean = distribution.distribution.mean.cpu().numpy()
        self.samples.append((np.mean(abs(np.clip(raw, -1, 1)), axis=0),
                             np.mean(abs(np.clip(mean, -1, 1)), axis=0),
                             np.mean((raw - mean)**2, axis=0),
                             np.mean(abs(raw) > 1, axis=0)))
        for info in infos:
            if "episode" not in info:
                continue
            episode = info["episode"]
            terms = info["episode_terms"]
            allocated = sum(terms["loss_" + key] for key in (*STATE_NAMES, "command"))
            if not np.isclose(allocated, terms["precision_loss"], atol=2e-4, rtol=1e-6):
                raise NumericalFailure("Allocated state/command losses do not reconstruct precision loss")
            reconstructed = terms["alive"] - terms["precision_loss"] - terms["fall"]
            if not np.isclose(reconstructed, episode["r"], atol=2e-4, rtol=1e-6):
                raise NumericalFailure("Raw episode reward components do not reconstruct return")
            row = {"policy_transitions": self.num_timesteps, "return": float(episode["r"]),
                   "length": int(episode["l"]), "sim_seconds": float(terms["sim_seconds"]),
                   "terms": terms}
            self.episode_rows.append(row)
            with (self.out / "episodes.jsonl").open("a") as stream:
                stream.write(json.dumps(row, allow_nan=False) + "\n")
        return True

    def after_update(self, elapsed):
        samples = np.asarray(self.samples)
        log_std = self.model.policy.log_std.detach().cpu().numpy()
        row = {"policy_transitions": self.model.num_timesteps,
               "training_seconds": elapsed, "plant_ticks": self.plant_ticks,
               "log_std": log_std.tolist(), "std_fraction_cap": np.exp(log_std).tolist(),
               "sampled_mean_abs_residual_fraction_cap": samples[:, 0].mean(axis=0).tolist(),
               "mean_abs_deterministic_output_fraction_cap": samples[:, 1].mean(axis=0).tolist(),
               "sampling_noise_rms_fraction_cap": np.sqrt(samples[:, 2].mean(axis=0)).tolist(),
               "action_box_clipping_fraction": samples[:, 3].mean(axis=0).tolist()}
        self.update_rows.append(row)
        with (self.out / "updates.jsonl").open("a") as stream:
            stream.write(json.dumps(row, allow_nan=False) + "\n")
        recent = self.episode_rows[-50:]
        row["recent_episode_length"] = float(np.mean([r["length"] for r in recent])) if recent else None
        row["recent_episode_return"] = float(np.mean([r["return"] for r in recent])) if recent else None
        v2.write_json(self.out / "progress.json", row)
        if recent:
            print(json.dumps({**row, "recent_reward_terms": {
                k: float(np.mean([r["terms"][k] for r in recent])) for k in recent[-1]["terms"]}}), flush=True)


def pilot_screens(panels, episodes, transitions):
    """Engineering screens, not a significance test or a full-run launcher."""
    required = {"snapshot-0", "snapshot-100k", "final"}
    if set(panels) != required or any(not p["complete"] for p in panels.values()):
        return {"pass": False, "reason": "Missing/incomplete development snapshot"}
    start, middle, end = (panels[k] for k in ("snapshot-0", "snapshot-100k", "final"))
    window = settings()["screen_window_transitions"]
    first = [r for r in episodes if r["policy_transitions"] <= window]
    last = [r for r in episodes if r["policy_transitions"] > transitions - window]
    enough = transitions >= 2 * window and bool(first) and bool(last)
    weak_return = enough and np.mean([r["return"] for r in last]) > np.mean([r["return"] for r in first])
    length = enough and np.mean([r["length"] for r in last]) >= np.mean([r["length"] for r in first])
    finite_E = all(p["E"] is not None and np.isfinite(p["E"]) for p in (start, middle, end))
    checks = {"zero_baseline_strict_16": start["strict"] == 16,
              "final_strict_16": end["strict"] == 16, "final_survival_16": end["survived"] == 16,
              "leg_rate_no_regression": end["leg_rate_violations"] <= start["leg_rate_violations"],
              "E_improves_from_100k": finite_E and end["E"] <= (1-settings()["E_improvement_fraction"]) * middle["E"],
              "E_no_regression_from_zero": finite_E and end["E"] <= start["E"],
              "weak_return_improves": bool(weak_return), "length_no_collapse": bool(length)}
    return {"pass": all(checks.values()), "checks": checks,
            "note": "Return is weak evidence: exploration SD may shrink. No automatic full run."}


def close_vector(vec, failed=False):
    raw = vec
    while isinstance(raw, VecEnvWrapper):
        raw = raw.venv
    if not isinstance(raw, SubprocVecEnv):
        vec.close()
        return
    if failed:
        # A worker dying while SB3 waits must not block shutdown on recv().
        # Only processes owned by this vector are signalled.
        for process in raw.processes:
            if process.is_alive():
                process.terminate()
        for process in raw.processes:
            process.join(timeout=2)
            if process.is_alive():
                process.kill()
                process.join(timeout=2)
        for remote in (*raw.remotes, *raw.work_remotes):
            remote.close()
        raw.waiting = False
        raw.closed = True
        return
    try:
        vec.close()
    except (BrokenPipeError, EOFError):
        close_vector(vec, failed=True)


def external_output(path):
    path = Path(path).expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError("Outputs must be outside git")
    path.mkdir(parents=True, exist_ok=False)
    return path


def run_pilot(out):
    wall_started = time.monotonic()
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--", "sim"],
                                    cwd=ROOT, text=True).strip()
    if dirty:
        raise ValueError("Commit the tested simulation implementation before a pilot")
    out = external_output(out)
    c = settings()
    status = {"status": "RUNNING", "counts_as_training_seed": False,
              "arm": "residual", "seed": c["seed"], "policy_transitions": 0,
              "panels": {}, "training_seconds": 0., "budget_elapsed_s": 0., "evaluation_seconds": 0.}
    v2.write_json(out / "config.json", {"pilot": c, "inherited_v2": v2.load_config(),
                  "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                  "source_dirty": bool(dirty),
                  "beta": beta_for_tolerances()})
    v2.write_json(out / "status.json", status)
    vec = None
    try:
        v2.single_thread()
        gains = v2.lqr_gains()
        vec = make_vector(gains)
        hyper = {**load_protocol()["ppo_hyperparameters"], **v2.load_config()["ppo_overrides"]}
        kwargs = dict(load_protocol()["ppo_policy_kwargs"])
        kwargs.update(activation_fn=torch.nn.Tanh, optimizer_class=torch.optim.Adam)
        model = PPO("MlpPolicy", vec, seed=c["seed"], device="cpu", policy_kwargs=kwargs, **hyper)
        zero_actor_mean(model)
        model.set_logger(configure(str(out / "optimizer"), ["csv"]))
        callback = Telemetry(out)
        # Populate initial observation stats without a physical rollout; reset
        # is the same random reset used by the first learning update.
        model._last_obs = vec.reset()
        model._last_episode_starts = np.ones(vec.num_envs, dtype=bool)
        probe = np.stack([physical_upright(d) for d in load_protocol()["plant"]["fixed_delays_s"]])
        np.testing.assert_array_equal(model.predict(vec.normalize_obs(probe), deterministic=True)[0], np.zeros((4, 2)))
        snapshot = save_snapshot(out / "snapshot-0", model, vec)
        status["initialization"] = verify_zero_initialization(model, vec, snapshot, gains)
        v2.write_json(out / "initialization-parity.json", status["initialization"])
        t = time.monotonic()
        status["panels"]["snapshot-0"] = evaluate_snapshot(snapshot, gains)
        status["evaluation_seconds"] += time.monotonic() - t
        if status["panels"]["snapshot-0"]["strict"] != 16:
            raise NumericalFailure("Zero actor baseline is not strict16/16; stop before training")
        rollout = hyper["n_steps"] * vec.num_envs
        initial = {k: v.detach().clone() for k, v in model.policy.state_dict().items()}
        budget_started = time.monotonic()
        while True:
            t = time.monotonic()
            # All LR/clip schedules are constant in the inherited recipe.
            # Repeated one-rollout learn calls preserve observations, RNG,
            # optimizer state, normalizer, episode buffers and counters.
            model.learn(total_timesteps=rollout, reset_num_timesteps=False, callback=callback)
            status["training_seconds"] += time.monotonic() - t
            callback.after_update(status["training_seconds"])
            model.logger.dump(step=model.num_timesteps)
            status.update(policy_transitions=model.num_timesteps, plant_ticks=callback.plant_ticks)
            if model.num_timesteps == c["snapshot_policy_transitions"]:
                snapshot = save_snapshot(out / "snapshot-100k", model, vec)
                t = time.monotonic()
                status["panels"]["snapshot-100k"] = evaluate_snapshot(snapshot, gains)
                status["evaluation_seconds"] += time.monotonic() - t
            # Budget includes the 100k evaluation pause and update overhead.
            # Initial preparation/snapshot-0 and final evaluation are separate.
            status["budget_elapsed_s"] = time.monotonic() - budget_started
            v2.write_json(out / "status.json", status)
            if stop_boundary(model.num_timesteps, status["budget_elapsed_s"]):
                break
        snapshot = save_snapshot(out / "final", model, vec)
        changed = any(not torch.equal(initial[k], v) for k, v in model.policy.state_dict().items())
        if not changed or any(not torch.isfinite(v).all() for v in model.policy.state_dict().values()):
            raise NumericalFailure("No finite optimizer change")
        t = time.monotonic()
        status["panels"]["final"] = evaluate_snapshot(snapshot, gains)
        status["evaluation_seconds"] += time.monotonic() - t
        status["screens"] = pilot_screens(status["panels"], callback.episode_rows, model.num_timesteps)
        status.update(status="COMPLETE", optimizer_updated=True, checkpoint_reload="PASS",
                      stop_reason=("maximum_duration" if status["budget_elapsed_s"] >= c["maximum_training_seconds"]
                                   else "target_transitions_and_minimum_duration"),
                      minimum_duration_overshoot_s=max(0., status["budget_elapsed_s"] - c["minimum_training_seconds"]),
                      maximum_budget_overrun_s=max(0., status["budget_elapsed_s"] - c["maximum_training_seconds"]))
        plot_curves(out, callback.episode_rows, callback.update_rows)
    except BaseException as exc:
        status.update(status="FAILED", error=f"{type(exc).__name__}: {exc}")
        (out / "error.txt").write_text(traceback.format_exc())
    finally:
        status["total_wall_seconds"] = time.monotonic() - wall_started
        v2.write_json(out / "status.json", status)
        if vec is not None:
            close_vector(vec, failed=status["status"] == "FAILED")
    print(json.dumps(status), flush=True)
    return 0 if status["status"] == "COMPLETE" else 1


def plot_curves(out, episodes, updates):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(9, 6))
    for ax, key, label in [(axes[0, 0], "return", "Raw episode return"),
                            (axes[0, 1], "length", "Episode policy actions")]:
        if episodes:
            ax.plot([r["policy_transitions"] for r in episodes], [r[key] for r in episodes], ".", ms=2)
        else:
            ax.text(.5, .5, "No completed episodes", ha="center", transform=ax.transAxes)
        ax.set_ylabel(label)
    for index in range(2):
        x = [r["policy_transitions"] for r in updates]
        axes[1, 0].plot(x, [r["std_fraction_cap"][index] for r in updates], label=f"axis{index}")
        axes[1, 1].plot(x, [r["sampled_mean_abs_residual_fraction_cap"][index] for r in updates], label=f"axis{index}")
    axes[1, 0].set_ylabel("Gaussian SD / residual cap")
    axes[1, 1].set_ylabel("Mean sampled |residual| / cap")
    for ax in axes.ravel():
        ax.set_xlabel("Aggregate policy transitions")
        ax.grid(alpha=.2)
    axes[1, 0].legend()
    fig.tight_layout()
    fig.savefig(out / "learning-curves.svg")
    plt.close(fig)


def diagnostic(archive, lqr_trace, out):
    """No simulation/training: query all three saved policies on saved inputs."""
    out = external_output(out)
    v2.single_thread()
    archive, trace = Path(archive), Path(lqr_trace)
    observations = []
    for path in sorted(trace.glob("chunk-*.npz")):
        with np.load(path) as arrays:
            observations.append(arrays["observation_before"][::5])
    if not observations:
        raise ValueError("Need archived LQR observation_before chunks")
    trajectory = np.concatenate(observations)
    report = {"kind": "offline output diagnostic; not a causal attribution", "seeds": []}
    caps = np.asarray(load_protocol()["plant"]["torque_limits_Nm"]) * .2
    for seed in range(3):
        folder = archive / "residual" / f"seed-{seed}"
        model, norm = v2.load_frozen(folder, "residual")
        before = deepcopy(norm.obs_rms)
        try:
            upright = []
            for delay in load_protocol()["plant"]["fixed_delays_s"]:
                raw = physical_upright(delay)
                normalized = norm.normalize_obs(raw)
                output, _ = model.predict(normalized, deterministic=True)
                upright.append({"delay_s": delay, "physical_raw_observation": raw.tolist(),
                                "saved_normalized_observation": normalized.tolist(),
                                "residual_fraction_cap": output.tolist(),
                                "residual_Nm": (output * caps).tolist()})
            actions, _ = model.predict(norm.normalize_obs(trajectory), deterministic=True)
            series_name = f"residual-seed-{seed}-lqr-inputs.npz"
            with (out / series_name).open("xb") as stream:
                np.savez_compressed(stream, observation=trajectory,
                                    residual_fraction_cap=actions, residual_Nm=actions*caps)
            row = {"seed": seed, "upright": upright, "saved_LQR_inputs": len(trajectory),
                   "saved_LQR_residual_series": series_name,
                   "saved_LQR_mean_residual_fraction_cap": actions.mean(axis=0).tolist(),
                   "saved_LQR_mean_abs_residual_fraction_cap": abs(actions).mean(axis=0).tolist(),
                   "saved_LQR_std_residual_fraction_cap": actions.std(axis=0).tolist(),
                   "saved_LQR_max_abs_residual_fraction_cap": abs(actions).max(axis=0).tolist()}
            np.testing.assert_array_equal(before.mean, norm.obs_rms.mean)
            np.testing.assert_array_equal(before.var, norm.obs_rms.var)
            assert before.count == norm.obs_rms.count
            report["seeds"].append(row)
            print(json.dumps(row), flush=True)
        finally:
            norm.close()
    report["interpretation"] = ("Nonzero physical-upright output shows an offset at that input. "
                                "Saved-LQR queries are off-policy, not rollouts of this residual controller; "
                                "neither proves the cause of every angular-rate violation.")
    v2.write_json(out / "diagnostic.json", report)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    for mode in ("run",):
        p = sub.add_parser(mode)
        p.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("diagnostic")
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--lqr-trace", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.mode == "diagnostic":
        return diagnostic(args.archive, args.lqr_trace, args.out)
    return run_pilot(args.out)


if __name__ == "__main__":
    raise SystemExit(main())
