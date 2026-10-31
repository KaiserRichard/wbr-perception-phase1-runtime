"""CPU PPO with completed-update accounting and verified versioned checkpoints."""
import argparse
from functools import partial
import hashlib
import json
import os
from pathlib import Path
import pickle
import platform
import random
import threading
import time
import uuid
import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.logger import configure
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv, VecNormalize
from .environment import G1Env
from .control import design
from .protocol import HERE, identity, panel, seed_wall_cap, write_json
from .parallel import one_thread


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def newest(run):
    candidates = []
    for marker in (Path(run)/'checkpoints').glob('*/complete.json'):
        try:
            rec = json.loads(marker.read_text())
            if all(sha(marker.parent/name)==digest for name,digest in rec['files'].items()):
                candidates.append((rec['steps'], rec['created_ns'], marker.parent))
        except (OSError, ValueError, KeyError):
            continue
    if not candidates:
        raise RuntimeError(f'No verified complete G1 checkpoint: {run}')
    return max(candidates)[2]


class SafeEnv(G1Env):
    def step(self, action):
        try:
            return super().step(action)
        except Exception:
            import traceback
            return np.zeros(25, np.float32), 0., True, False, {'worker_error': traceback.format_exc()}


def worker(seed, rank):
    one_thread()
    return SafeEnv(seed, rank)


def vector(seed, n_envs=8, subprocess=True):
    factories = [partial(worker, seed, rank) for rank in range(n_envs)]
    return SubprocVecEnv(factories, start_method='spawn') if subprocess else DummyVecEnv(factories)


class Progress(BaseCallback):
    def _on_step(self):
        for info in self.locals['infos']:
            if 'worker_error' in info:
                raise RuntimeError(info['worker_error'])
            if info.get('numerical_failure'):
                raise FloatingPointError('Numerical failure invalidates G1 run')
            if 'episode' in info:
                row = dict(transitions=self.num_timesteps,
                           wall_s=self.model.prior_wall+time.monotonic()-self.model.started,
                           episode=info['episode'], reward_sums=info['reward_sums'],
                           metrics=info['episode_metrics'], case=info['case'])
                with (self.model.run_dir/'episodes.jsonl').open('a') as f:
                    f.write(json.dumps(row, allow_nan=False)+'\n')
        return True


class WallStop(Exception):
    pass


class G1PPO(PPO):
    def _excluded_save_params(self):
        return super()._excluded_save_params()+['timer']

    def collect_rollouts(self, *args, **kwargs):
        def expired():
            write_json(self.run_dir/'watchdog.json', dict(status='FAILED', reason='rollout/update exceeded60s',
                                                         completed_steps=self.completed_steps))
            os._exit(124)  # Backup bound even if a worker/optimizer blocks.
        self.update_started = time.monotonic()
        self.timer = threading.Timer(self.update_limit, expired)
        self.timer.daemon = True; self.timer.start()
        return super().collect_rollouts(*args, **kwargs)

    def train(self):
        super().train()
        if any(not torch.isfinite(v).all() for v in self.policy.parameters()):
            raise FloatingPointError('Nonfinite optimizer parameters')
        self.completed_steps = self.num_timesteps
        self.max_update = max(self.max_update, time.monotonic()-self.update_started)
        self.timer.cancel()
        elapsed = time.monotonic()-self.started
        stop = ((self.seconds is not None and elapsed >= self.seconds-self.update_limit)
                or (self.run_dir/'STOP').exists()
                or (self.stop_file is not None and self.stop_file.exists()))
        final = self.completed_steps >= self.budget
        if time.monotonic()-self.last_save >= self.interval or stop or final:
            self.checkpoint()
        if self.num_timesteps//100000 > self.last_report//100000:
            elapsed = time.monotonic()-self.started
            row = dict(steps=self.num_timesteps, segment_steps=self.num_timesteps-self.initial_steps,
                       wall_s=elapsed, seconds_per_100k=elapsed*100000/(self.num_timesteps-self.initial_steps))
            with (self.run_dir/'walltime-100k.jsonl').open('a') as f:
                f.write(json.dumps(row)+'\n')
            print(json.dumps(row), flush=True)
            self.last_report = self.num_timesteps
        self.logger.dump(self.num_timesteps)
        write_json(self.run_dir/'progress.json', dict(completed_steps=self.completed_steps, elapsed_s=elapsed,
                   max_update_s=self.max_update, wall_s=self.prior_wall+elapsed))
        if stop and not final:
            raise WallStop()

    def checkpoint(self):
        started = time.monotonic()
        dest = self.run_dir/'checkpoints'/f'{self.completed_steps:09d}-{uuid.uuid4().hex[:8]}'
        dest.mkdir(parents=True)
        self.save(dest/'policy.zip')
        self.env.save(dest/'normalizer.pkl')
        state = dict(python=random.getstate(), numpy=np.random.get_state(), torch=torch.get_rng_state(),
                     samplers=self.env.env_method('sampler_state'), identity=identity(), seed=self.seed,
                     completed_steps=self.completed_steps, updates=self._n_updates, config=self.g1_config,
                     wall_s=self.prior_wall+time.monotonic()-self.started,
                     simulated_seconds=self.completed_steps*.01,
                     active_episodes_reset_on_resume=True, rollout_position=0)
        with (dest/'state.pkl').open('wb') as f:
            pickle.dump(state, f)
        loaded = PPO.load(dest/'policy.zip', device='cpu')
        probe = np.linspace(-1, 1, 25, dtype=np.float32).reshape(1, -1)
        np.testing.assert_array_equal(self.predict(probe, deterministic=True)[0], loaded.predict(probe, deterministic=True)[0])
        with (dest/'normalizer.pkl').open('rb') as f:
            normalizer = pickle.load(f)
        np.testing.assert_array_equal(self.env.normalize_obs(probe), normalizer.normalize_obs(probe))
        if loaded.num_timesteps != self.completed_steps or loaded._n_updates != self._n_updates:
            raise ValueError('Reload counters differ')
        files = {p.name:sha(p) for p in dest.iterdir()}
        write_json(dest/'complete.json', dict(steps=self.completed_steps, created_ns=time.time_ns(), files=files,
                   copy_reload='PASS', copy_seconds=time.monotonic()-started,
                   checkpoint_age_seconds=time.monotonic()-self.last_save))
        random.setstate(state['python']); np.random.set_state(state['numpy']); torch.set_rng_state(state['torch'])
        self.last_save = time.monotonic()
        print(f'G1 verified checkpoint: {dest}', flush=True)
        return dest


def train(run, seed, seconds=None, resume=False, config=None, subprocess=True,
          seed_wall_cap_min=None, stop_file=None):
    seed_wall_cap_min = seed_wall_cap(seed_wall_cap_min)
    cfg = json.loads((HERE/'config.json').read_text()) if config is None else config
    one_thread()
    run = Path(run); run.mkdir(parents=True, exist_ok=True)
    if not resume and (run/'checkpoints').exists():
        raise FileExistsError('Retained G1 run: use resume; no silent retry')
    # Freeze protocol/model/baseline before the first learning transition.
    declaration = dict(identity=identity(), config=cfg, seed=seed,
               streams=['command','pitch','push','delay','episode_IMU_seed'],
               panels=dict(development=panel(True), final=panel()), baseline=design()[3])
    declaration_path = run/'declaration.json'
    if declaration_path.exists():
        old = json.loads(declaration_path.read_text())
        if any(old[k] != declaration[k] for k in ('identity','config','seed','panels')):
            raise ValueError('G1 declaration source/config/seed mismatch')
    else:
        write_json(declaration_path, declaration)
    raw = vector(seed, cfg['n_envs'], subprocess)
    vec = None; model = None
    started = time.monotonic()
    try:
        if resume:
            dest = newest(run)
            with (dest/'state.pkl').open('rb') as f:
                state = pickle.load(f)
            if state['identity'] != identity() or state['seed'] != seed or state['config'] != cfg:
                raise ValueError('G1 resume source/model/protocol/seed mismatch')
            vec = VecNormalize.load(dest/'normalizer.pkl', raw)
            model = G1PPO.load(dest/'policy.zip', env=vec, device='cpu', force_reset=True)
            raw._reset_seeds()
            for rank, sampler in enumerate(state['samplers']):
                raw.env_method('restore_sampler', sampler, indices=rank)
            random.setstate(state['python']); np.random.set_state(state['numpy']); torch.set_rng_state(state['torch'])
            prior_wall = state['wall_s']
            print('RESUME: RNG/samplers/optimizer/normalizer restored; active episodes reset (discontinuity).', flush=True)
        else:
            prior_wall = 0.
            vec = VecNormalize(raw, norm_obs=True, norm_reward=False, clip_obs=10., gamma=.99)
            model = G1PPO('MlpPolicy', vec, seed=seed, device='cpu',
                           n_steps=cfg['n_steps'], batch_size=cfg['batch_size'], n_epochs=cfg['n_epochs'],
                           learning_rate=cfg['learning_rate'], gamma=cfg['gamma'], gae_lambda=cfg['gae_lambda'],
                           clip_range=cfg['clip_range'], policy_kwargs=dict(net_arch=dict(pi=[64,64],vf=[64,64]),
                           activation_fn=torch.nn.Tanh, log_std_init=float(np.log(.05))))
            # Exact initial deterministic identity; stochastic samples remain Gaussian.
            with torch.no_grad():
                model.policy.action_net.weight.zero_(); model.policy.action_net.bias.zero_()
        model.run_dir, model.budget = run, cfg['transitions']
        model.g1_config = cfg
        model.started = model.last_save = time.monotonic()
        model.prior_wall = prior_wall
        remaining_cap = None if seed_wall_cap_min is None else seed_wall_cap_min*60-prior_wall
        if remaining_cap is not None:
            seconds = remaining_cap if seconds is None else min(seconds, remaining_cap)
        model.seconds, model.interval = seconds, cfg['checkpoint_seconds']
        model.stop_file = None if stop_file is None else Path(stop_file)
        model.update_limit = cfg['max_update_seconds']
        model.initial_steps = model.last_report = model.completed_steps = model.num_timesteps
        model.max_update = 0.
        model.cpu_start = time.process_time()
        model.set_logger(configure(str(run/f'optimizer-{time.time_ns()}'), ['csv']))
        status = 'PARTIAL'
        try:
            remaining = model.budget-model.num_timesteps
            capped = remaining_cap is not None and remaining_cap <= model.update_limit
            stopped = (run/'STOP').exists() or (model.stop_file is not None and model.stop_file.exists())
            if remaining > 0 and not capped and not stopped:
                model.learn(remaining, reset_num_timesteps=False, callback=Progress())
            elif remaining > 0 and not resume:
                model.checkpoint()
            status = 'COMPLETE' if model.completed_steps == model.budget else 'PARTIAL'
        except WallStop:
            pass
        finally:
            if hasattr(model, 'timer'):
                model.timer.cancel()
        elapsed = time.monotonic()-model.started
        steps = model.completed_steps-model.initial_steps
        receipt = dict(status=status, seed=seed, completed_steps=model.completed_steps, segment_steps=steps,
                       elapsed_s_including_checkpoints=elapsed, transitions_per_second=steps/elapsed,
                       max_rollout_update_s=model.max_update, reset_on_resume=resume,
                       seed_wall_cap_min=seed_wall_cap_min, cumulative_wall_s=prior_wall+elapsed,
                       parent_process_cpu_s=time.process_time()-model.cpu_start,
                       worker_process_cpu_s=raw.env_method('cpu_seconds') if subprocess else [],
                       environment_backend='subprocess' if subprocess else 'in_process',
                       host=platform.platform(), device='cpu',
                       torch_num_threads=torch.get_num_threads(),
                       thread_env={key:os.environ[key] for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')},
                       source_identity=identity(), cold_start_s=model.started-started)
        write_json(run/f'receipt-{time.time_ns()}.json', receipt)
        write_json(run/'receipt.json', receipt)
        return receipt
    except BaseException as exc:
        write_json(run/'failure.json', dict(error=repr(exc), completed_steps=getattr(model,'completed_steps',0)))
        raise
    finally:
        if model is not None and hasattr(model, 'timer'):
            model.timer.cancel()
        if model is not None:
            model.logger.close()
        # Avoid a hanging close when a worker died; terminate only our processes.
        if hasattr(raw, 'processes'):
            for process in raw.processes:
                if process.is_alive():
                    process.terminate()
            for process in raw.processes:
                process.join(timeout=2)
            raw.closed = True
        elif vec is not None:
            vec.close()
        else:
            raw.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--seed', type=int, required=True)
    p.add_argument('--seconds', type=float, help='Optional segment duration (smoke/benchmark use)')
    p.add_argument('--seed-wall-cap-min', type=seed_wall_cap,
                   help='Cumulative per-seed wall cap in minutes, including resumed segments (default unlimited)')
    p.add_argument('--resume', action='store_true')
    args = p.parse_args()
    print(json.dumps(train(args.out,args.seed,args.seconds,args.resume,
                           seed_wall_cap_min=args.seed_wall_cap_min)), flush=True)

if __name__ == '__main__':
    main()
