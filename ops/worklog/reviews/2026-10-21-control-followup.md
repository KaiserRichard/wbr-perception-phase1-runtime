# Control follow-up — 21 October 2026

Owner resumed control work and requested account priority j/k. Both were busy in the shared-session checks at 13:52 and 13:53 +07; neither was interrupted, quota-probed or dispatched. No camera task, checkout or file was accessed. The latest owner request permits j for control when idle; d/h remain excluded and g/k still share one pool.

**Completed:** generated the final saved-result table and seven SVG plots (strict success, survival, duration, recovery, penalized recovery, command/applied effort), using the existing reporting tool. Read 3,985,899 JSON bytes; no policy, trajectory replay or training. Independently checked the completed v2 seed totals, 160-case coverage, 100/500 Hz rates, single reused LQR row and SVG XML validity. Counts match PR91: direct strict 59/800, survival 760/800; residual strict 0/480, survival 480/480. Missing legacy training curves remain unavailable. The v1 aggregate reader leaves joint survival unavailable; this does not weaken its separately established strict-success count.

```sh
python3 -m sim.rl.reporting \
  --v1-aggregate ~/wbr-evidence-archive/sim-ppo-vs-lqr-20261020-01/evaluation/aggregate.json \
  --v2-archive ~/wbr-evidence-archive/sim-ppo-v2-20261020-01 \
  --out ~/wbr-evidence-archive/sim-control-followup-20261021-01/comparison
```

**Partial:** attempted the queued nine-case five-bar mechanics comparison using the unchanged `sim.fivebar.compare --run-dynamics --duration 5 --timesteps .001 .0005 .00025 --epsilons 1e-5 3e-6 1e-6`. Single-thread BLAS, nice 10, existing backend Python, 120 s wall limit. It hit that resource limit; its own child was terminated. The CLI writes its JSON only after all cases, so no completed result exists and no numerical conclusion is claimed. Log: `~/wbr-evidence-archive/sim-control-followup-20261021-01/fixed-length-dynamics.log`. No retry, environment mutation, training or rendering. Battery was 62%, on AC and charging at the start.

**Recommendation:** give the still-pending A4 mechanics study to k when idle, with an explicit longer compute budget and a fresh output path. A3's 76 designs/400 cases and full videos remain unrun. Use the saved comparison plots for interpreting v2; effort/recovery do not establish RL superiority. No v3 recipe or training is authorized by this follow-up.
