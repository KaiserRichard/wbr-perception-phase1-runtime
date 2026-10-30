"""Frozen v2 recipe with completed-update USB checkpoints. No GPU backend."""
import argparse
from functools import partial
import hashlib
import json
import os
from pathlib import Path
import pickle
import random
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'source'))
# Thread limits are set by v2 before torch/numpy import.
from sim.rl import v2
import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.logger import configure
from stable_baselines3.common.vec_env import SubprocVecEnv, VecNormalize


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def identity():
    return {p.relative_to(ROOT).as_posix(): digest(p)
            for p in sorted((ROOT / 'source/sim').rglob('*'))
            if p.is_file() and p.suffix in ('.py', '.json', '.xml')}


class PortableEnv(v2.V2Env):
    def sampler(self):
        return self._conditions.bit_generator.state, self._episode_index

    def restore_sampler(self, state):
        self._conditions.bit_generator.state, self._episode_index = state


def worker(arm, seed, rank, config, gains):
    v2.single_thread()
    return v2.ReportWorkerFailure(PortableEnv(arm, seed, rank, config, gains))


def vector(arm, seed, cfg):
    gains = v2.lqr_gains() if arm == 'residual' else None
    return SubprocVecEnv([partial(worker, arm, seed, rank, cfg, gains)
                          for rank in range(cfg['training']['n_envs'])], start_method='spawn')


def newest(run):
    candidates = []
    for path in (run / 'checkpoints').glob('*/complete.json'):
        try:
            record = json.loads(path.read_text())
            if all(digest(path.parent / name) == value for name, value in record['files'].items()):
                candidates.append((record['steps'], record['created_ns'], path.parent))
        except (OSError, ValueError, KeyError):
            continue
    if not candidates:
        raise RuntimeError(f'No verified complete checkpoint: {run}')
    return max(candidates)[2]


class PortableProgress(v2.Progress):
    def _on_training_start(self):
        self.initial_steps = self.model.num_timesteps

    def _on_step(self):
        errors = [i['worker_error'] for i in self.locals['infos'] if 'worker_error' in i]
        if errors:
            raise v2.NumericalFailure('\n'.join(errors))
        self.plant_ticks += sum(i['plant_ticks'] for i in self.locals['infos'])
        elapsed = time.perf_counter()-self.started
        if elapsed-self.last_write >= 10:
            steps = self.num_timesteps-self.initial_steps
            v2.write_json(self.out / 'progress.json', {
                'policy_transitions': self.num_timesteps, 'segment_transitions': steps,
                'target': self.budget, 'segment_plant_ticks': self.plant_ticks,
                'elapsed_s': elapsed, 'segment_transitions_per_second': steps/elapsed})
            self.last_write = elapsed
        return True


class TimedStop(Exception):
    pass


class PortablePPO(PPO):
    def _excluded_save_params(self):
        return super()._excluded_save_params() + ['progress']

    def train(self):
        super().train()  # Save only after all frozen v2 optimizer epochs.
        if any(not torch.isfinite(p).all() for p in self.policy.parameters()):
            raise v2.NumericalFailure('Nonfinite optimizer parameters')
        update_seconds = time.monotonic() - self.last_update
        elapsed = time.monotonic() - self.started
        steps = self.num_timesteps - self.initial_steps
        self.logger.dump(step=self.num_timesteps)
        if self.num_timesteps // 100000 > self.last_report // 100000:
            print(f'{self.num_timesteps} steps; wall seconds per 100k: {elapsed*100000/steps:.3f}', flush=True)
            self.last_report = self.num_timesteps
        stop = elapsed >= self.seconds or (self.run_dir / 'STOP').exists()
        final = self.num_timesteps >= self.budget
        if time.monotonic() - self.last_save >= self.interval or stop or final:
            self.checkpoint()
        if update_seconds > 60:
            self.checkpoint()
            raise RuntimeError(f'Rollout/update exceeded 60s: {update_seconds:.3f}; checkpoint retained')
        self.last_update = time.monotonic()
        if stop and not final:
            raise TimedStop()

    def checkpoint(self):
        started = time.monotonic()
        dest = self.run_dir / 'checkpoints' / f'{self.num_timesteps:09d}-{uuid.uuid4().hex[:8]}'
        dest.mkdir(parents=True)
        self.save(dest / 'policy.zip')  # SB3 includes optimizer, scheduler and counters.
        self.env.save(dest / 'vecnormalize.pkl')
        state = {'python': random.getstate(), 'numpy': np.random.get_state(),
                 'torch': torch.get_rng_state(), 'samplers': self.env.env_method('sampler'),
                 'identity': identity(), 'arm': self.arm, 'seed': self.seed,
                 'steps': self.num_timesteps, 'updates': self._n_updates,
                 'reset_on_resume': True,
                 'plant_ticks': self.prior_ticks+self.progress.plant_ticks,
                 'simulated_seconds': (self.prior_ticks+self.progress.plant_ticks)*.002}
        with (dest / 'state.pkl').open('wb') as f:
            pickle.dump(state, f)
        # Verify copied policy + normalizer before publishing completion marker.
        loaded = PPO.load(dest / 'policy.zip', device='cpu')
        probe = np.linspace(-1, 1, 15).reshape(1, -1)
        np.testing.assert_array_equal(self.predict(probe, deterministic=True)[0],
                                      loaded.predict(probe, deterministic=True)[0])
        with (dest / 'vecnormalize.pkl').open('rb') as f:
            norm = pickle.load(f)
        np.testing.assert_array_equal(self.env.normalize_obs(probe), norm.normalize_obs(probe))
        if loaded.num_timesteps != self.num_timesteps or loaded._n_updates != self._n_updates:
            raise ValueError('Checkpoint counters differ')
        files = {p.name: digest(p) for p in dest.iterdir()}
        v2.write_json(dest / 'complete.json', {'steps': self.num_timesteps, 'created_ns': time.time_ns(),
                      'files': files, 'copy_reload': 'PASS', 'copy_seconds': time.monotonic()-started,
                      'checkpoint_age_seconds': time.monotonic()-self.last_save})
        # PPO.load seeds global RNGs while constructing its verification model.
        random.setstate(state['python'])
        np.random.set_state(state['numpy'])
        torch.set_rng_state(state['torch'])
        self.last_save = time.monotonic()
        print(f'USB checkpoint verified: {dest}', flush=True)


def train(run, arm, seed, seconds, interval, resume=False):
    run.mkdir(parents=True, exist_ok=True)
    cfg = v2.load_config()
    budget = cfg['training']['policy_transitions_per_seed']
    v2.single_thread()
    raw = vector(arm, seed, cfg)
    vec = None
    try:
        if resume:
            folder = newest(run)
            with (folder / 'state.pkl').open('rb') as f:
                state = pickle.load(f)
            if state['identity'] != identity() or (state['arm'], state['seed']) != (arm, seed):
                raise ValueError('Resume source/model/config/arm/seed mismatch')
            vec = VecNormalize.load(folder / 'vecnormalize.pkl', raw)
            model = PortablePPO.load(folder / 'policy.zip', env=vec, device='cpu')
            # Loading seeds the VecEnv; prevent that pending seed from discarding
            # restored sampler state at the first reset of resumed episodes.
            raw._reset_seeds()
            for rank, sampler in enumerate(state['samplers']):
                raw.env_method('restore_sampler', sampler, indices=rank)
            random.setstate(state['python'])
            np.random.set_state(state['numpy'])
            torch.set_rng_state(state['torch'])
            print('RESUME: sampler/RNG restored; active episodes reset; trajectory discontinuity.', flush=True)
        else:
            vec = VecNormalize(raw, **cfg['vecnormalize'])
            kwargs = dict(v2.load_protocol()['ppo_policy_kwargs'])
            kwargs.update(activation_fn=torch.nn.Tanh, optimizer_class=torch.optim.Adam)
            model = PortablePPO('MlpPolicy', vec, seed=seed, device='cpu', policy_kwargs=kwargs,
                                **{**v2.load_protocol()['ppo_hyperparameters'], **cfg['ppo_overrides']})
        if model.num_timesteps >= budget:
            print('Seed already has the full 3M transitions.', flush=True)
            return
        model.prior_ticks = state['plant_ticks'] if resume else 0
        model.progress = PortableProgress(run, budget)
        model.run_dir, model.arm, model.budget = run, arm, budget
        model.started = model.last_save = model.last_update = time.monotonic()
        model.initial_steps = model.last_report = model.num_timesteps
        model.seconds, model.interval = seconds, interval
        log = run / f'segment-{time.time_ns()}'
        model.set_logger(configure(str(log), ['csv', 'json']))
        try:
            # Remaining budget keeps SB3's total schedule at exactly 3M on resume.
            model.learn(total_timesteps=budget-model.num_timesteps, reset_num_timesteps=False,
                        callback=model.progress)
        except TimedStop:
            pass
        v2.write_json(log / 'receipt.json', {'steps': model.num_timesteps,
                      'segment_steps': model.num_timesteps-model.initial_steps,
                      'elapsed_s_including_usb': time.monotonic()-model.started,
                      'status': 'COMPLETE' if model.num_timesteps == budget else 'PARTIAL',
                      'reset_on_resume': resume, 'backend': 'cpu', 'seed': seed, 'arm': arm})
    finally:
        (vec if vec is not None else raw).close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['smoke', 'train', 'resume', 'resume-latest'])
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--minutes', type=float, default=80)
    p.add_argument('--smoke-seconds', type=float, default=600)
    p.add_argument('--checkpoint-minutes', type=float, default=5)
    p.add_argument('--arm', choices=['direct', 'residual'], default='direct')
    p.add_argument('--seed', type=int, default=0)
    args = p.parse_args()
    if args.minutes <= 0 or args.checkpoint_minutes <= 0:
        p.error('durations must be positive')
    if args.mode == 'resume-latest':
        candidates = []
        for run in args.run.glob('seed-*'):
            try:
                folder = newest(run)
                record = json.loads((folder / 'complete.json').read_text())
                candidates.append((record['created_ns'], run))
            except RuntimeError:
                continue
        if not candidates:
            raise RuntimeError('No verified seed checkpoint on USB')
        args.run = max(candidates)[1]
        args.mode = 'resume'
    # Lock held by OS and automatically released after a crash, including Windows.
    args.run.mkdir(parents=True, exist_ok=True)
    with (args.run / 'run.lock').open('a+b') as lock:
        lock.seek(0)
        if os.name == 'nt':
            import msvcrt
            lock.write(b'0')
            lock.flush()
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.mode == 'smoke':
            started = time.monotonic()
            if args.smoke_seconds < 180:
                raise RuntimeError('Offline setup consumed the smoke window')
            train(args.run, args.arm, 42, min(180, args.smoke_seconds/3), 120)
            before = json.loads((newest(args.run) / 'complete.json').read_text())['steps']
            remaining = args.smoke_seconds - (time.monotonic()-started) - 60
            if remaining <= 0:
                raise RuntimeError('Smoke exceeded ten-minute deadline before restore')
            train(args.run, args.arm, 42, remaining, 120, resume=True)
            after = json.loads((newest(args.run) / 'complete.json').read_text())['steps']
            if after <= before or time.monotonic()-started > args.smoke_seconds:
                raise RuntimeError('Smoke failed: no resumed update or ten-minute deadline missed')
            while time.monotonic()-started < args.smoke_seconds:
                time.sleep(min(1, args.smoke_seconds-(time.monotonic()-started)))
            v2.write_json(args.run / 'smoke.json', {'resume': 'PASS', 'before': before, 'after': after,
                          'elapsed_s': time.monotonic()-started, 'counts_as_training_seed': False})
        else:
            train(args.run, args.arm, args.seed, args.minutes*60, args.checkpoint_minutes*60,
                  resume=args.mode == 'resume')


if __name__ == '__main__':
    main()
