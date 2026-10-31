# G1 implementation readings (2026-10-31)

These decisions fill gaps in PLAN-v2; its reward, cases, budgets and thresholds
are unchanged. No result here validates a physical robot.

- **Plant provenance:** use the candidate numbers once as hypothetical aggregate
  masses (body3.5, equivalent leg0.2, wheel lump0.7 kg), explicitly ASSUMED.
  No multiplication by two, rod allocation or invented report citation. The
  manifest remains BLOCKED_ASSEMBLY_PROVENANCE, so scientific laptop release
  remains NO-GO. `model.json` is a separate input to the existing planar MJCF
  generator. The physical `sim/wbr_model` generator needs a different, complete
  tensor/assembly manifest; it is inappropriate for this fixed-leg reduction.
  Inertias, COMs, limits and lag retain the manifest's explicit assumptions.
- **Fixed baseline:** preserve existing nominal Q/R, synthesize the existing
  augmented DARE once at5ms on the new model, then freeze the gains for every
  tested delay. Re-express its eight state/filter coefficients as a gain on a
  prediction at5ms, Kp=Kaug[:, :8] exp(-F*0.005). Online prediction uses nominal
  linear mechanics/5ms filter and the actual known command arrival timestamps.
  There is no schedule, gain retuning, future control or push oracle. Both arms
  execute exactly this same code. The actuator runtime's command-only torque
  estimate uses the declared variant lag (5 or8ms); it is causal, but assumes
  known actuator parameters. This shared assumption limits robustness claims.
- **Delay:** lump sensor-to-actuation age into the command transport path, rather
  than adding another sensor delay. The existing runtime splits integration at
  arrivals, using at most0.25ms mechanical substeps and exact filter endpoint,
  mean and squared integral. The predictor splits at the same timestamps using
  matrix exponentials. It never rounds5ms to a3-tick delay. Initial transport
  and actuator prehistory is zero. The request-age observation is the known
  constant age assigned to each episode, not a sampled future delay.
- **Reference and acceptance:** x_ref always integrates the original ramp;
  accepted delta changes only the inner velocity reference. The0.1m/s² bound
  applies to delta, not the preregistered original ramp. Delta changes by at
  most0.001m/s per100Hz action and remains within±0.03m/s. A deterministic
  ramp-aware feasibility bound starts removing positive delta before the
  +0.2m/s ramp endpoint (and symmetrically for negative commands), avoiding a
  late speed clamp that would violate delta slew. Zero action remains exact
  baseline identity. A nonfinite request is rejected to zero proposal; malformed
  shapes raise an error. Both rejections and clipping are counted.
- **Observations:** 25 float32 values, in order: six measured errors divided by
  the six tolerances; original ramp speed/0.2; five newest accepted deltas/0.03;
  five newest issued clipped torque pairs divided by pair caps; two causal
  torque estimates/caps; known request age/0.01. Histories are newest first,
  zero padded. Only pitch/gyro have IID Gaussian measurement noise, following
  the existing declared IMU model; other coordinates are ideal measurements.
  SB3 observation normalization is learned/saved with clip10; reward is neither
  clipped nor normalized. No policy gets true state, push timing or variant ID.
- **Reward:** score original-reference true errors at the end of each100Hz
  action, and the physical torque endpoint in the specified torque penalty.
  The action penalties use normalized clipped policy a, before governor slew
  acceptance. The fall penalty uses actual termination time. These choices do
  not modify coefficients: a single tolerance-sized x or v error costs1 of the
  alive1 reward; one angular error costs0.5; one rate error costs0.25. Those are
  100%,100%,50%,25% respectively, with no anti-abort guarantee.
- **Metrics:** final-window precision uses500Hz samples; sustained recovery is
  a complete1s span (501 sample points), with its **completion** required within
  5s of start and3.15s push end. This is stricter than counting the start of the
  interval. Continuous bounds are resolved at500Hz, not an analytic guarantee
  between integration nodes. Body collision is the planar body's lowest box
  corner reaching the floor; this no-contact reduction cannot model impact.
  A failed/truncated final window has E=null, and makes its stratum's E=null;
  failed counts and observed-interval E over **all** cases remain available.
  No missing-window failure is excluded to advertise survivor precision.
  Overall/reference regressions are constrained for every seed, conservatively
  stronger than an across-seed mean-only reading. The t interval uses five
  paired seed differences with df4; final baseline ceiling prevents a benefit
  PASS. Headroom checks use only development cases before training finals.
- **Resume and time:** save only after completed optimizer updates, so no partial
  rollout is promoted to completed experience. Keep versioned checksummed policy,
  optimizer/counters, normalizer, CPU/Python/NumPy RNG and independent sampler
  streams. Active episodes reset on restore, explicitly recorded as a trajectory
  discontinuity. Resume from a fresh directory is exercised in smoke; exact
  future trajectories are not promised. Stop scheduling an update when less
  than its60s maximum remains in the wall-time allowance. This can finish a
  bounded run up to60s early. Smoke fills the remaining600s window after actual
  training, restore, parity and development evaluation; it is separate from the
  single20min seed42 scientific pilot and the five fresh final seeds.
- **Forecast:** the requested1.3 ratio means laptop wall time=Mac wall time×1.3,
  hence laptop throughput=Mac throughput/1.3. It is an ESTIMATE, not a measured
  i7-11800H or Windows result. Paired final evaluation counts1200 episodes:
  one shared200-case baseline plus five200-case policies. A single development
  anchor supplies only an optimistic timing projection; Windows measurement is
  still required and all preregistration release boxes remain binding.
