# Obsidian figure review and replacement prompts

Date: 2026-10-21

Review scope: nine owner-supplied PNGs in `WBR_model_LQR_RL_9_figures`. The plates are illustrative teaching art, not robot measurements, CAD, or validated hardware data. No raster assets were edited.

## Review of supplied plates

| Figure | Status | Visual review and concrete issue | Caption qualification |
|---|---|---|---|
| `01_coordinates_and_angles.png` | Revise panel B; A/C are usable | Panel B shows the world-vertical reference, leg axis and body axis, but labels only the relative arc `φ−θ`. It omits the individual `θ` and `φ` arcs that define the subtraction and leaves the positive arc direction ambiguous. Panel A/C communicate the separate absolute angles more clearly. | Say `θ` and `φ` are absolute planar pitches from world vertical, and the relative hip coordinate is `φ−θ` (body orientation minus leg orientation). State the sign convention and call the geometry an assumed reduced planar schematic. Do not imply a measured joint encoder or hardware axis. |
| `02_geometry_and_com.png` | Keep with qualification | The COM construction and position equations are internally consistent with the planar coordinates. The table mixes a source-code-supported wheel-radius constant with assumed `L`, `a`, and `b`; the note correctly says the radius is not measured, but readers may still treat the table as identified geometry. | Call all dimensions illustrative model parameters: `r=0.0603 m` is a source-code constant, not a physical measurement; `L`, `a`, and `b` are assumptions. This is not the five-bar linkage, CAD, or a measured COM survey. |
| `03_energy_terms.png` | Keep with qualification | It correctly emphasizes that eliminating wheel angle under ideal rolling does not remove wheel rotational energy, and depicts upright gravitational potential as a local maximum. The component blocks are idealized rigid bodies and omit contact loss, compliance, and the actual linkage. | Describe this as an energy derivation for an assumed rigid, reduced planar model with ideal rolling. The stability intuition is local and open-loop; do not present it as a measurement or a complete five-bar/contact model. |
| `04_motor_reactions_and_push.png` | Keep with qualification | The generalized-force vector and equal/opposite hip reaction are useful under the stated aggregate torque and clockwise-positive generalized-coordinate convention. The push values match the simulation protocol, but the picture omits that it acts at the body COM, in world `+x`, from 3.00 to 3.15 s, with no applied moment. | Identify torques as aggregate pair / virtual inputs, not individual motor commands or measured motor capability. Describe the push as the assumed simulation case (`6 N`, `0.15 s`, `0.9 N·s` at body COM in world `+x`), not a robot test. |
| `05_mechanics_to_state_space.png` | Keep; tighten state wording | The lower model contract correctly expands the six-state vector, but the sequence first writes `ṡ=f(s,u,F)` and `s=[q; q̇]`, while the schematic also foregrounds scalar axle position `x`. A quick reader could mistake `x` for the state rather than one coordinate inside `s`. | Explicitly say the state is the six-vector `s=[x, θ, φ, ẋ, θ̇, φ̇]ᵀ`; scalar `x` is only axle position. `q=[x,θ,φ]ᵀ` is the three-coordinate configuration. The nonlinear plant is assumed and reduced; the local linear model is a controller-design approximation. |
| `06_linearization_and_sampling.png` | Keep with version note | Panel A is intentionally a teaching sketch and says it is not measured data. Panel B's 2 ms update clock accurately describes the 500 Hz plant/LQR tick, but could be read as the PPO policy update rate in the later v2 comparison. | Explain the 2 ms clock as the plant integration/control tick and 500 Hz LQR feedback schedule. For v2 PPO, actions are held across five ticks (100 Hz policy); this plate is not an RL schedule diagram. |
| `07_lqr_feedback_loop.png` | Revise title/caption when used | “The actual LQR feedback loop” overstates what is drawn: the loop explicitly says nominal before delay/noise and uses ideal state measurement. It does not show the noisy observation, actuator delay, or motor lag in the augmented runtime. | Call it a nominal simulated LQR loop with ideal full-state feedback. The local eigenvalue statement concerns the unsaturated discrete linear model; nonlinear recovery with saturation and actuator effects needs separate simulation evidence. Do not call this the complete deployed or current augmented loop. |
| `08_delay_lag_and_noise.png` | Revise truth-path annotation | The actor feedback path is appropriately based on a noisy observation, and true state is kept outside the policy input. However, the dashed true-state path terminates only at “Evaluation metrics only.” In v2, simulator truth also computes the training reward and physical termination. Calling it metrics-only would be wrong. | State that true post-step plant state is used for reward, termination, and evaluation metrics only; it is not actor input or a privileged critic observation. Sensor proxies, delay, lag, and noise levels are assumptions, not hardware characterization. |
| `09_fair_lqr_rl_comparison.png` | Replace or prominently mark historical | This is a prospective v1-style protocol figure, not a current result: “no results yet,” 2 ms shared controller period, and “at least five” RL seeds. Actual v1 used 500 Hz PPO and five 150k-step seeds; all 800 PPO evaluation cases failed strict settling while LQR passed 160/160. Actual v2 used 100 Hz PPO (five 500 Hz plant ticks per policy action), 3M transitions per seed, five direct-PPO seeds and three residual-PPO seeds; direct passed 59/800 and survived 760/800, residual passed 0/480 and survived 480/480, and reused delay-aware LQR passed 160/160. V2's residual seed count is three because the predeclared extension rule did not trigger. Its policy uses causal observations, while true state is used for reward/termination/metrics. | Call the plate a historical v1 comparison-protocol sketch, not a figure of v2 results. Any accompanying v2 caption must disclose the 100 Hz PPO versus 500 Hz LQR schedule, the five direct and three residual independent training seeds, the 3M transitions per seed, and the assumed reduced planar simulation scope. Report both strict settling and survival, and say the LQR evaluation panel is reused rather than counted as independent PPO seed replicates. |

### Source checks behind the review

- `sim/planar.py`: state order is `[x_m, leg_rad, body_rad, xdot_m_s, legdot_rad_s, bodydot_rad_s]`; MuJoCo hip-joint coordinates are `[x, θ, φ−θ]` while controller state uses absolute `φ`.
- `sim/configs/assumed_planar.json`: reduced planar plant, `dt=0.002 s`, assumed body/leg masses, COM offsets and inertias, aggregate torque limits; wheel-radius constant is source-code-supported but explicitly not a measurement.
- `sim/configs/assumed_actuator_noise.json`: assumed 2–5 ms delays, 5 ms motor time constants, and body-angle/gyro noise.
- `sim/rl/v2_config.json`, `sim/rl/v2.py`, and `sim/rl/protocol.json`: PPO action hold is five 2 ms plant ticks; residual LQR feedback is recalculated on plant ticks; truth-derived cost/reward and physical termination are separate from the causal controller observation; true state also supports evaluation metrics.
- `sim/rl/RESULTS_2026-10-20.md`: historical v1 result and five-seed/150k-step protocol.
- `sim/rl/RESULTS_V2_2026-10-20.md`: final v2 setup and outcomes summarized above. The v2 records contain no episode-length/return learning curves; do not add invented curves to a replacement plate.

## Ready-to-copy standalone image prompts

Each prompt below is self-contained. Attach any relevant supplied PNGs as visual-style and topic references when submitting it. The references are not authority for labels, equations, dimensions, or results: follow the prompt's explicit definitions. Render all annotations legibly and exactly; if accurate text rendering is not possible, leave a clean blank callout rather than inventing symbols. Every plate must visibly say **“ASSUMED REDUCED PLANAR SCHEMATIC — NOT CAD, NOT TO SCALE, NO MEASURED ROBOT DATA”** unless its prompt explicitly distinguishes a conceptual assembled robot from the reduced model.

### Prompt 1 — assembled WBR overview and reduced sagittal surrogate

**Proposed filename:** `wbr_assembled_overview_and_reduced_model.png`

```text
Create one sophisticated grayscale mechanical-drafting teaching plate, landscape 16:10, with fine black ink, restrained graphite-gray fills, precise leader lines, consistent serif technical lettering, generous white space, and a clean archival engineering-book aesthetic. Use the attached reference plates only for visual style and subject context; do not copy their simplified robot as if it were the full machine.

The plate has two clearly separated panels. LEFT, larger panel, title “Conceptual assembled wheeled-biped robot (WBR)”: show a coherent upright robot as a non-dimensional concept illustration: two parallel driven wheels, left and right articulated leg mechanisms represented as paired linkages, a central hip/body assembly with plausible mounting plates and generic motor housings, and a small electronics enclosure. Use a three-quarter view so the bilateral structure is unmistakable. Do not invent exact linkage dimensions, motor models, materials, wiring, sensor placement, CAD details, or measured geometry. Label parts only with generic names: “wheel pair”, “left/right leg linkage”, “hip assembly”, “body”, “electronics (illustrative)”. Add a small note: “Conceptual assembly; detailed geometry and dimensions not established here.”

RIGHT, smaller panel, title “Reduced sagittal simulation surrogate”: show a deliberately simplified side-view wheel, one equivalent rigid leg, and one rigid body with axle O, hip H, world x horizontal and z upward, and absolute angles theta and phi from world vertical. State clearly that this surrogate is not the assembled five-bar mechanism. Include only the exact state definition s = [x, theta, phi, x-dot, theta-dot, phi-dot]^T and input definition u = [wheel-pair torque, virtual hip-pair torque]^T. Explain in a short footer that x is axle displacement and the simulator's relative hip joint angle is phi - theta.

Use a thin divider and a visual bridge arrow labeled “physical robot → reduced model for analysis”, not an implication that the model is identified. Put the exact footer: “ASSUMED REDUCED PLANAR SCHEMATIC — NOT CAD, NOT TO SCALE, NO MEASURED ROBOT DATA”. Do not include numerical dimensions, parameter values, performance curves, or hardware validation claims. Avoid decorative color, photorealism, perspective distortion that hides the paired mechanism, and illegible microtext.
```
### Prompt 2 — causal actor–critic WBR training and evaluation loop

**Proposed filename:** `wbr_actor_critic_causal_training_loop.png`

```text
Draw a publication-quality grayscale control-and-learning block diagram, landscape 16:10, using the attached references only for restrained mechanical-drafting style. Crisp vector-like boxes and arrows, clear causal direction, readable mathematical labels, no gradients or decorative color. This is an assumed simulation schematic, not measured robot data.

Make three bands: (1) causal interaction during PPO training, (2) learning update, and (3) frozen evaluation. In the interaction band, draw “causal policy observation o_k (15 values)” into a Gaussian actor pi_theta, then “raw Gaussian sample”; next explicitly clip to a normalized command in [-1,1]^2 and scale to torque limits. The rollout stores the raw sample and its old log-probability, not a replacement log-probability evaluated at the clipped command. The observation may be expanded in a side note as six sensor proxies + two causal torque estimates + three two-channel clipped-command history entries + known delay. Mark body-angle and body-rate channels noisy in the assumed sensor model; do not draw true state entering the actor or critic.

The action is held for five 2 ms plant ticks (100 Hz policy action updates). At each plant tick, for the residual arm only, compute “u_LQR = -K_d z_k” from the same causal observation; add the held, bounded learned correction “Delta u_j”; then apply a final total-command saturation. Label the direct arm as PPO action alone. Both arms enter the same assumed augmented plant: exact transport delay, first-order motor lag, reduced nonlinear MuJoCo mechanics, and assumed sensor noise. Return the next causal observation to the actor. Show LQR feedback recomputed at 500 Hz; show the learned correction held for five ticks. Do not confuse command hold period with transport delay.

From a distinct “true post-step plant state” output, draw arrows ONLY to (a) “training reward and physical termination” and (b) “evaluation metrics”. Label: “truth is scoring/evaluation only; never policy input or privileged critic state”. The reward box says “alive bonus − scaled quadratic true-state and total clipped-command cost; termination penalty on physical fall/displacement”. Do not invent a reward curve or numeric performance result.

In the learning band, show reward, next observation, and value estimate feeding GAE/return targets; advantage and old action log-probability feeding the PPO clipped actor objective; return target feeding critic V_phi; the optimizer updates actor theta and critic phi. Use dashed arrows only for parameter updates, not runtime signal flow. Include a separate frozen deterministic-policy evaluation box that reports strict settling, survival/falls, recovery, state error, and command/applied torque metrics; evaluation must not feed updates.

Use the exact footer: “ASSUMED REDUCED PLANAR SIMULATION — NOT CAD, NOT TO SCALE, NO MEASURED ROBOT DATA”. Keep arrows unambiguous, label information boundaries, and do not claim stability, superiority, deployment, or privileged-critic training.
```

### Prompt 3 — multirate residual torque timing and signal path

**Proposed filename:** `wbr_multirate_residual_torque_timing.png`

```text
Create a precise grayscale engineering timing plate, wide landscape 16:9, with high-contrast drafting lines, readable labels, aligned time axes, and a sober technical textbook aesthetic. Use attached reference plates only as style references. Show the v2 residual-control signal path and rates exactly; all values describe an assumed simulation configuration, not hardware measurements.

Top half: a signal-flow diagram. A common causal observation feeds a delay-aware LQR controller updated every 2 ms (500 Hz). In parallel, a PPO actor emits a two-channel normalized correction every 10 ms (100 Hz); hold that correction constant across five consecutive 2 ms plant ticks. Scale the correction to caps 0.4 N m wheel-pair and 0.8 N m virtual-hip-pair. At every 2 ms tick, add the held correction to the freshly recomputed LQR command, then clip the TOTAL command to aggregate limits 2 N m and 4 N m. Label “residual arm only”; the direct PPO arm omits LQR and uses its own held torque action. Show the total command entering exact transport delay (tested 2–5 ms) and first-order motor lag (5 ms), then the assumed reduced nonlinear plant.

Bottom half: a shared precise timeline from 0 to 20 ms. Mark PPO updates at 0, 10, 20 ms. Mark LQR/plant ticks at 0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20 ms. Draw one held correction level across the full 0–10 ms policy interval and the next level across 10–20 ms, with the update boundary visually clear. Show a command issued at an arbitrary tick arriving after its chosen delay d, and distinguish that transport delay from the 10 ms policy hold and the 5 ms motor time constant. Include a small motor response inset: delay shifts arrival; lag makes realized torque approach the arrived command smoothly.

Use arrow labels “requested total command”, “clipped issued command”, and “realized motor torque” so these are not conflated. State that the learned delta is not equal to the difference between two separately diverged trajectories' total torques. Add the exact footer: “ASSUMED REDUCED PLANAR SIMULATION — NOT CAD, NOT TO SCALE, NO MEASURED ROBOT DATA”. No empirical traces, invented motor response measurements, or claim that the bounded residual guarantees stability.
```

### Prompt 4 — corrected Fig. 01B angle geometry

**Proposed filename:** `wbr_coordinates_panel_b_corrected.png`

```text
Produce a clean grayscale mechanical-drafting figure panel, landscape 4:3, suitable as a corrected replacement for the hip-angle inset in the attached coordinate reference. Use fine black technical ink, thin dashed reference lines, two distinct solid body axes, careful angle arcs, and large legible math typography. The attached figure is a style reference only; the angle definitions below are authoritative.

Draw hip point H. Through H, draw a dashed vertical world-up reference. Draw a leg centerline ray from H leaning slightly right of vertical and a body centerline ray from H leaning farther right. Label them “leg axis” and “body axis”. Mark theta as the signed clockwise angle from world vertical to the leg axis. Mark phi as the signed clockwise angle from the same world vertical to the body axis. Then mark the relative hip angle from leg axis to body axis and label it exactly “phi - theta”. Use separate, non-overlapping arcs so a reader can see that both absolute angles share one reference. Add a small note “absolute pitch angles; clockwise positive in this schematic” and an equation “q_hip = phi - theta”. Include a tiny upright inset where theta=0, phi=0, and q_hip=0.

Do not depict phi as measured from the leg axis; do not use phi-theta for either absolute angle; do not reverse the subtraction; do not add an unlabeled angle arc. Keep the geometry conceptual and explicitly state: “ASSUMED REDUCED PLANAR SCHEMATIC — NOT CAD, NOT TO SCALE, NO MEASURED ROBOT DATA”. No dimensions, hardware encoder claims, torque arrows, or decorative color.
```

### Prompt 5 — six-state model contract and notation guard

**Proposed filename:** `wbr_six_state_model_contract.png`

```text
Design a grayscale engineering-teaching plate, landscape 16:10, with a left-to-right derivation and crisp typography. Match the attached technical plates' sophisticated drafting feel without copying questionable symbols. This is an assumed reduced planar WBR surrogate, not CAD or measured data.

Panel 1, “Configuration”: draw a wheel on a flat reference floor, one equivalent rigid leg from axle O to hip H, and a rigid body above H. World x points right and z points up. Label axle displacement x, absolute leg pitch theta from world vertical, and absolute body pitch phi from world vertical. State q = [x, theta, phi]^T. Make clear that x is one scalar coordinate, not the name of the full state.

Panel 2, “State”: write prominently and exactly s = [q; q-dot] = [x, theta, phi, x-dot, theta-dot, phi-dot]^T in the declared order. Add units beneath: m, rad, rad, m/s, rad/s, rad/s. Explicitly caption: “The state is the complete six-component vector s; x alone is only axle position.”

Panel 3, “Inputs and nonlinear plant”: write u = [tau_w, tau_h]^T, where tau_w is aggregate wheel-pair torque and tau_h is virtual hip-pair torque. Show s-dot = f(s,u,F) for the assumed nonlinear plant. Add a smaller nearby linearization s-dot approximately A_c s + B_c u around upright; say it is local controller-design mathematics and does not replace the nonlinear simulation.

Add a small joint-coordinate inset stating simulator relative hip coordinate = phi - theta, while controller body state remains absolute phi. Do not use a scalar x where vector s is meant, do not relabel the relative hip angle as absolute body pitch, and do not imply five-bar kinematics. Exact footer: “ASSUMED REDUCED PLANAR SCHEMATIC — NOT CAD, NOT TO SCALE, NO MEASURED ROBOT DATA”.
```
