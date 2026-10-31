# G1 CPU bundle · Windows x64 · USB checklist

The entry point is the preregistered bounded velocity-reference governor above
fixed LQR, **not PPO v2**. MuJoCo and PPO run on CPU; the RTX3060 is unused.
The hypothetical reduced plant remains ASSUMED, with unresolved assembly/report
provenance. Actual Windows offline execution remains unverified until exercised.

1. Build off-site with `bash research/rl/bundle/build_bundle.sh /path/to/WBR-G1`.
   The builder copies the current G1 source, model/config/cases, preregistration,
   parameter manifest and review, standalone Python3.12.7, uv0.5.4, exact Windows
   CPU wheels/lock, licenses, revision/patch and SHA256SUMS. Preserve the identical
   generated ZIP and USB directory. Allow≥5GB local and≥10GB USB plus checkpoints;
   measure actual space after build. Missing exact wheels fail the build.
2. At the seat, record Windows x64 version, CPU/RAM, free local/USB space, power,
   sleep/wipe/shutdown times and permission to run extracted Python/scripts and
   write USB. No network, admin, driver/WSL install, policy/PATH/registry changes
   or compiler is required. Keep USB inserted throughout.
3. Run `run.bat` with **no minute argument**. The launcher verifies hashes,
   recreates `%LOCALAPPDATA%\WBR-G1\.venv` offline with uv, records the machine,
   then invokes G1's real ten-minute smoke followed by the gated scientific queue.
   `WBR_WORK` may specify another permitted writable runtime directory.
4. Smoke uses seed42, the actual8×250 PPO recipe, versioned checkpoint/reload,
   copy to a fresh directory, sampler/RNG/optimizer/normalizer restore, continued
   updates, deterministic zero-governor/LQR parity and development-only timing.
   The dedicated `launch.py smoke` mode includes offline setup in its600s cap;
   full queue mode records setup separately and then runs the600s training smoke.
   A rollout/update over60s is a failure; it retains the previous complete save.
5. The full queue checks the optional seed wall cap and evaluation≤120min,
   report/Windows/offline/host readiness, development baseline headroom and the
   single20min seed42 scientific pilot. Its return/length and paired precision/
   survival gates are frozen. See `source/sim/rl/g1/README.md` for the run-folder
   `host-readiness.json` evidence fields. Current unresolved boxes mean NO-GO;
   the launcher stops with the actual reason rather than starting five jobs.
6. Once prerequisites pass, train fresh seeds0–4 in parallel,1M each, unlimited seed wall time by default.
   `run.bat --jobs 5` sets seed/evaluation processes; default min(5, CPU threads/2),
   at least one. `--jobs 1` selects serial execution; `resume.bat` accepts it too.
   `--seed-wall-cap-min MINUTES` optionally caps cumulative per-seed wall time;
   `resume.bat` accepts it too. No pilot weights, task/reward changes, budget cuts
   or retry selection.
   Checkpoints go directly to USB every5 wall minutes on a completed update,
   with file hashes and copied-policy reload. Keep all prior complete versions.
   A `STOP` file in a seed directory stops at the next completed update. Only
   remove that file to continue the same job; never delete evidence.
7. After an interruption/wipe, run `resume.bat` (unlimited by default). It
   restores the newest G1 queue, reuses a valid completed smoke/pilot and resumes
   final counters within an optional seed cap, counting prior wall time. Hash/source/model/
   config mismatches reject resume; corrupt/incomplete checkpoint versions are
   skipped. Active simulator episodes reset with an explicit discontinuity.
   A failed/interrupted scientific pilot is retained and never silently retried.
8. Retain all `runs/`, receipts/errors, episode curves/metrics, hashes, manifests
   and source. Reserve the last30min for a second owner-controlled copy and hash
   verification before safe eject. All checkpoints reload before their completion
   marker is published. The old515/635min café-session deadlines no longer apply;
   a configured cap/STOP retains verified USB state and marks unfinished seeds PARTIAL. No Windows
   compatibility, physical transfer or scientific success follows from Mac smoke.
