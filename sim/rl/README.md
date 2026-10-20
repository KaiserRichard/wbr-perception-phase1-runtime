# Predeclared PPO versus LQR comparison

**SIMULATION / ASSUMED. No WBR training or RL performance result yet.**
[protocol.json](protocol.json) freezes five seeds, 150,000 steps each, final
checkpoints, direct torque PPO, fixed reward/hyperparameters and retained failures.
Each policy faces the same 20 held-out noise seeds in eight delay/scenario cases.
Report paired uncertainty over training seeds; episodes are not extra seed replicates.

Use the actuator worker's shared runtime after conductor verification. Both
controllers receive common noisy measurements, causal torque estimates/history
and known delay. The fixed padded policy vector has 15 entries; truth is only
for reward/evaluation. Four ideal non-IMU channels remain explicit assumptions.
The WBR Gymnasium wrapper/trainer and observation adapter are future work.

PPO limits updates with `E[min(r*A, clip(r,1-eps,1+eps)*A)]`.
Sources: [PPO paper](https://arxiv.org/abs/1707.06347),
[SB3 2.3.2 PPO](https://stable-baselines3.readthedocs.io/en/v2.3.2/modules/ppo.html),
[Gymnasium termination/truncation API](https://gymnasium.farama.org/api/env/).

From the repository root, choose a fresh environment path:

```sh
python3.12 -m venv /tmp/wbr-ppo-venv
/tmp/wbr-ppo-venv/bin/python -m pip install -r sim/rl/requirements.txt
/tmp/wbr-ppo-venv/bin/python .github/run_unittest.py sim/rl/tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /tmp/wbr-ppo-venv/bin/python - <<'PY'
import torch
from stable_baselines3 import PPO
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
model = PPO("MlpPolicy", "CartPole-v1", device="cpu", seed=17,
            n_steps=32, batch_size=32, n_epochs=1)
model.learn(total_timesteps=64)
assert model.num_timesteps == 64
model.get_env().close()
print("SMOKE ONLY: 64 CartPole steps; no WBR training")
PY
```

**Recommendation:** verify the augmented plant, then assign full-budget training.
