# Hierarchical RL path tracking for a wheeled biped

**Primary sources.** Wei Zhu, Fahad Raza, and Mitsuhiro Hayashibe, “Reinforcement
Learning based Hierarchical Control for Path Tracking of a Wheeled Bipedal
Robot with Sim-to-Real Framework,” IEEE/SICE International Symposium on System
Integration (SII), 2022, [IEEE record and DOI](https://doi.org/10.1109/SII52469.2022.9708882);
[authors' publication page and paper/code links](https://www.weizhu996.com/publication/example/), [authors' public
repository](https://github.com/zw199502/WheeledBipedalRobotRLPathTrack).
The authors' page describes both simulation and real-world path-tracking
experiments; its public code repository includes a README and zipped source/
mesh artifacts. It does not by itself expose the complete experimental dataset
or a self-contained reproduction environment.

## Control architecture

This is explicitly a three-layer design. A high-level RL policy selects path
tracking behavior in simulation. A middle-level Lyapunov-based nonlinear
controller tracks a desired line and provides a stability argument for the
tracking layer. A low-level proportional-integral-derivative (PID) controller
on the physical wheeled biped handles balance and velocity tracking. The
authors' central sim-to-real choice is to transfer the high-level policy across
a stable control interface rather than ask it to directly replace the balance
loop. They report the policy can be used on hardware without tuning its
parameters after transfer.

## Evidence and interpretation

**Author-reported simulation and real-world evidence:** the authors state that
the hierarchy yields quick, robust, stable path tracking in both settings. This
is a path-tracking result on their platform; it is not a controlled PPO-versus-
LQR comparison, and the public abstract does not give enough sample counts,
uncertainty intervals, or full physical parameters to independently assess the
size of the claimed improvement. The repository's presence supports code
availability, not automatic reproducibility.

## Relevance and limits

The architecture is relevant if learned navigation is later added above the
lab's safety-critical STM32 balance controller: constrain the learned policy to
a supervisory command (for example, a target line/velocity), and keep fast
stabilization in a separately validated lower layer. It does not establish
safety of arbitrary commands or transfer to another robot. The local PPO v2
currently controls the assumed simulator policy task directly and is evaluated
separately; this paper's hierarchy is a different experiment and must not be
treated as evidence for that result. The hardware-specific Lyapunov and PID
layers, timing, sensors, and robot model would need their own source audit.
