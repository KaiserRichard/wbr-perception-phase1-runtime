# RL for blind stair climbing

**Primary source.** Simon Chamorro et al., “Reinforcement Learning for Blind
Stair Climbing with Legged and Wheeled-Legged Robots,” ICRA 2024,
[arXiv paper](https://arxiv.org/abs/2402.06143),
[IEEE proceedings record](https://doi.org/10.1109/ICRA57147.2024.10610069), and its [supplementary
video](https://youtu.be/Ec6ar8BVJh4). The paper is openly readable. No code or
full training artifact is linked from the paper page, so exact reproduction of
its environment and training is not established by this source alone.

## Method

The authors use Proximal Policy Optimization (PPO) in Isaac Gym with an
asymmetric actor-critic. The policy actor receives deployable proprioception
(angular velocity, projected gravity, goal direction/heading, target height,
terrain-mode boolean, joint state, and last action). During training only, the
critic additionally sees privileged simulator information such as base velocity
and height, terrain grid, relative 3-D goal, wheel contact force, and friction.
Articulated-joint actions are target positions tracked by low-level proportional-
derivative loops; wheel actions are target angular rates. The task is
position-based: reach a goal at the top of a step within a six-second episode,
allowing the policy to choose an approach/step strategy instead of tracking a
fixed velocity profile. A terrain boolean lets one policy activate a learned
stair behavior. The authors randomize observations/conditions and inject a
simulated 20 ms control delay.

## Evidence

**Simulation:** the paper reports 2,000 trials per robot/step condition. For
Ascento, the reported policy success is 87.6% for 14 cm, 82.3% for 18 cm, and
69.4% for 22 cm steps; higher rows include steps beyond the training height.
The ablations show strong drops without privileged critic information or the
terrain boolean. These are simulator outcomes under the paper's definitions,
not hardware trials.

**Prototype:** the authors report successful Ascento climbs on 15 cm steps,
previously beyond that robot version's demonstrated capability. The described
behavior mixes forward momentum, slight leg split, and sequential leg lift;
the paper explicitly notes simulation mismatch in wheel-edge friction/slip and
actuator response. Thus the physical result demonstrates a selected behavior,
not a broad quantified success rate or guaranteed sim-to-real transfer.

## Relevance and limits

This is directly relevant to the WBR morphology and illustrates policy
formulation, privileged training signals, and the importance of modeling
observation/actuation delay. It addresses obstacle crossing with variable legs,
whereas the current lab comparison asks a reduced planar balance task with
fixed leg geometry. The task, action interface, simulated plant, and sensor
access differ materially; its success numbers cannot be compared with local PPO
or LQR scores. A useful transfer lesson is to measure the real delay/slip and
declare the deployable observation set before comparing policies.

