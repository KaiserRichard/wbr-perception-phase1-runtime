"""Fixed SB3 PPO training, exact budgets, retained failures and final policies."""

import time
import traceback

import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.logger import configure

from sim.rl.environment import WbrEnv, load_protocol
from sim.rl.provenance import capture, manifest, new_output, sha256, write_json
from sim.rl.trace import TraceRecorder


def single_thread():
    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != 1:
        torch.set_num_interop_threads(1)


def make_model(env, seed):
    p = env.protocol
    kwargs = dict(p['ppo_policy_kwargs'])
    kwargs['activation_fn'] = torch.nn.Tanh
    kwargs['optimizer_class'] = torch.optim.Adam
    return PPO(p['ppo']['policy'], env, seed=seed, device='cpu',
               policy_kwargs=kwargs, **p['ppo_hyperparameters'])


class CaptureActions(BaseCallback):
    def __init__(self, recorder, out):
        super().__init__()
        self.recorder, self.out = recorder, out
        self.started = time.perf_counter()

    def _on_step(self):
        # SB3's unbounded actions and clipped env actions share this same tick,
        # even when DummyVecEnv has already auto-reset a terminal episode.
        self.recorder.attach_raw(self.locals['actions'][0])
        if self.num_timesteps % 1000 == 0:
            elapsed = time.perf_counter() - self.started
            write_json(self.out / 'progress.json', {'actual_env_steps': self.num_timesteps,
                       'elapsed_s': elapsed, 'steps_per_second': self.num_timesteps / elapsed})
        return True


def train(seed, out, authorization, smoke=False):
    out = new_output(out)
    p = load_protocol()
    status = {'seed': seed, 'status': 'FAILED', 'counts_as_training_seed': not smoke,
              'label': 'WBR OPTIMIZER SMOKE ONLY' if smoke else 'FROZEN FULL TRAINING',
              'actual_env_steps': 0, 'checkpoint_sha256': None, 'failure_reasons': []}
    started = time.perf_counter()
    env = recorder = model = None
    try:
        if seed not in p['training']['policy_seeds']:
            raise ValueError('Seed outside frozen slots')
        capture(out, authorization, full=not smoke)
        single_thread()
        recorder = TraceRecorder(out / 'trace', p)
        env = WbrEnv(policy_seed=seed, recorder=recorder)
        model = make_model(env, seed)
        model.set_logger(configure(str(out / 'optimizer'), ['csv', 'json']))
        initial = {k: v.detach().clone() for k, v in model.policy.state_dict().items()}
        # Smoke performs one real WBR rollout/update using all frozen parameters.
        # It is never a candidate checkpoint for the comparison.
        budget = p['ppo_hyperparameters']['n_steps'] if smoke else p['training']['steps_per_seed']
        if budget % model.n_steps or model.n_envs != 1:
            raise ValueError('Budget must be an exact multiple of one-environment rollouts')
        model.learn(total_timesteps=budget, callback=CaptureActions(recorder, out))
        if model.num_timesteps != budget or recorder.total_steps != budget or env.total_steps != budget:
            raise ValueError('Actual step budget mismatch')
        changed = any(not torch.equal(initial[k], v) for k, v in model.policy.state_dict().items())
        if not changed or any(not torch.isfinite(v).all() for v in model.policy.state_dict().values()):
            raise ValueError('PPO parameters failed to update or became nonfinite')
        checkpoint = out / ('smoke-final.zip' if smoke else 'final.zip')
        model.save(checkpoint)
        loaded = PPO.load(checkpoint, device='cpu')
        probe = np.zeros(15)
        np.testing.assert_array_equal(model.predict(probe, deterministic=True)[0],
                                      loaded.predict(probe, deterministic=True)[0])
        for key, value in model.policy.state_dict().items():
            if not torch.equal(value, loaded.policy.state_dict()[key]):
                raise ValueError('Checkpoint reload changed parameters')
        if loaded.num_timesteps != budget:
            raise ValueError('Checkpoint timestep mismatch')
        status.update(status='SMOKE_COMPLETE' if smoke else 'COMPLETE', actual_env_steps=budget,
                      checkpoint_sha256=sha256(checkpoint), checkpoint=checkpoint.name,
                      optimizer_updated=changed, optimizer_epochs=model._n_updates,
                      budget=budget, checkpoint_reload='PASS')
    except BaseException as exc:
        status['failure_reasons'] = [f'{type(exc).__name__}: {exc}']
        (out / 'error.txt').write_text(traceback.format_exc())
        if env is not None and hasattr(env, 'runtime'):
            with (out / 'failure-state.npz').open('xb') as stream:
                np.savez_compressed(stream, truth=env.runtime.truth(), time_s=env.runtime.time,
                                    noise=env.runtime.sensor_noise(),
                                    attempted_action=getattr(env, 'attempted_action', np.full(2, np.nan)),
                                    warnings=env.runtime.warning_counts)
    finally:
        if recorder is not None:
            recorder.close()
            status['recorded_steps'] = recorder.total_steps
        if env is not None:
            status['actual_env_steps'] = env.total_steps
            env.close()
        status['sb3_env_steps'] = model.num_timesteps if model is not None else 0
        status['elapsed_s'] = time.perf_counter() - started
        status['steps_per_second'] = status['actual_env_steps'] / status['elapsed_s']
        status['exit_code'] = 0 if status['status'] in ('COMPLETE', 'SMOKE_COMPLETE') else 1
        write_json(out / 'status.json', status)
        manifest(out)
    return status
