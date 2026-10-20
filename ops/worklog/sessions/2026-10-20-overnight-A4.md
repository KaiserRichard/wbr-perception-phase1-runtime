# A4 — separate planar five-bar + VMC scaffold

- Dedicated branch `chatgpt/20261020-fivebar`, starting at `6fbe9a3`; initial
  status clean, no prior A4 implementation/PR. Prior events retained.
- Added only `sim/fivebar/` and this log. Existing planar/config/runtime,
  owner-only gain exercise, active backend environment and PPO evidence unchanged.
- `geometry.py`: pinned dimensions, explicit circle/elbow branches, implicit
  Jacobian, virtual-work torque mapping, endpoint and chassis/stator reactions.
- `model.py`: separate eight-coordinate MuJoCo tree with two closed ankle loops,
  three aggregate motor inputs and physical distal-link wheel reaction.
- `README.md`, `PROVENANCE.json`, `LICENSE`: frames/signs, derivation/worked
  example, assumptions, pinned DM-jump hashes and complete MIT notice.
- All Python commands used backend
  `/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python`,
  `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
  VECLIB_MAXIMUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1`.
- Actual first build: `python -m sim.fivebar.model`, exit 0; 8 coordinates,
  3 inputs; closure $7.51\times10^{-17}$ m initially and
  $2.80\times10^{-7}$ m after one finite step. No actual build/test failure.
- Actual final quick command: `WBR_FIVEBAR_C_REFERENCE=/private/tmp/wbr-parity-c-reference-20261020-01 python -m unittest discover -s sim/fivebar/tests -v`:
  **14/14 passed**, 0.163 s unittest time, 0.47 s process wall time. Earlier
  12-test stage passed before the projection/energy tests were added.
- C comparison reused checksum-verified prebuilt reference read-only; no rebuild.
  Without that optional path, CI skips the one C test and discovers the rest.
- Actual `python -m sim.fivebar.compare`: snapshot only, exit 0;
  hip-position error below $10^{-15}$ m, virtual-hip mapping error below
  $10^{-9}$. Wheel reaction and assumed link mass matrix differ from reduced.
- Queued **NOT RUN** (after training or on a provisioned Pi):
  `nice -n 10 "$PY" -m sim.fivebar.compare --run-dynamics --duration 5 --timesteps .001 .0005 .00025 --epsilons 1e-5 3e-6 1e-6 --output /private/tmp/wbr-overnight-20261020/A4/fixed-length-dynamics.json`;
  `$PY` is the backend above. This is a nine-case fixed-length projection study,
  not free-length XML/servo/contact validation or an equivalence PASS.
- Heavy dynamics/solver refinement, full equivalence and Pi execution unverified;
  no long simulation, training, dependency rebuild or physical action performed.
- Central documentation log/decisions and final milestone review remain conductor-owned.
