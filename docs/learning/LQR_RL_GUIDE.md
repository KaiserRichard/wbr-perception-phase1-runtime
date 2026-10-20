# LQR → realistic simulation → RL: today's reading

**Goal:** understand the controller before comparing algorithms. Simulation only.

## 1. Read the model (10 min)
- State: `x = [position, leg angle, body angle, velocity, leg rate, body rate]`.
- Action: `u = [wheel-pair torque, hip-pair torque]`, in N·m; angles use radians.
- Leg and body angles are independent. Mass/COM/inertia are ASSUMED.
- Code: [plant](../../sim/planar.py), [parameters](../../sim/configs/assumed_planar.json).
- Check yourself: why would fixing the body angle make this an invalid balance test?

## 2. Understand LQR (15 min) — Must Know
- Near upright: `x[k+1] ≈ A x[k] + B u[k]`; these matrices describe local dynamics.
- Choose `J = Σ (xᵀQx + uᵀRu)`. Q penalizes state errors; R penalizes effort.
- Solve for K, then apply `u = clip(−Kx)` using the same sample period and limits.
- Here: DARE, 2 ms control period. Discrete closed-loop poles must satisfy `|λ| < 1`.
- Larger Q/R changes the trade-off; it does not guarantee better recovery with saturation/delay.
- Code: [synthesis](../../sim/lqr.py). Read `K_used` and the poles in `linearization.json`.
- Exercise: predict what increasing the position weight might change before trying it in a new run.
- Source: [SciPy DARE](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_discrete_are.html).

## 3. Add missing dynamics (10 min) — Must Know
- **Delay:** the motor receives an older command, `u(t − d)`.
- **Torque lag:** `dτ/dt = (u_delayed − τ)/Tmotor`; torque cannot change instantly.
- **IMU noise:** measured body angle/rate differ from the true simulated state.
- First test the SAME K and protocol. Re-synthesize only if that baseline fails.
- Lag/noise values are illustrative assumptions, not measurements of our hardware.
- Exercise: with a 2 ms loop, why must a 3 ms delay not simply be rounded to one step?
- Source: [MuJoCo actuator dynamics](https://mujoco.readthedocs.io/en/3.3.7/computation/index.html#actuation-model).

## 4. Understand RL (15 min) — Must Know
- **Observation:** available sensor information/history, not hidden perfect state.
- **Action:** the same bounded wheel/hip torque commands as LQR.
- **Reward:** a training signal, e.g. negative state-error and effort cost.
- A policy learns actions from experience; reward improvement alone is not proof of better control.
- A fall terminates an episode; reaching its time limit truncates it.
- PPO is a candidate algorithm. Start with what it observes/controls/rewards before its loss derivation.
- Sources: [Gymnasium environments](https://gymnasium.farama.org/introduction/create_custom_env/), [PPO](https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html).

## 5. Compare fairly (5 min)
- Same plant, observations, control rate, torque limits, initial states, pushes and episode length.
- Use at least five training seeds; evaluate each on held-out, paired disturbance/noise seeds.
- Report falls/success, recovery, peak tilt, tracking error and effort with uncertainty; keep failed seeds.
- Our declared push is `6 N × 0.15 s = 0.9 N·s`. Preserve this reference case.
- Good to Know: actuator-state augmentation, partial observability and confidence intervals.
- Skip For Now: full five-bar VMC, contact tuning, complex policy architectures and hardware deployment.

**Current status:** nominal LQR is approved; delay/lag/noise work is running. RL training comes afterward.
**Your exercise:** [gain_schedule](../../sim/parity/student.py) stays yours; this guide does not solve it.
**Run/read next:** [simulation README](../../sim/README.md); keep each experiment in a new output folder.
