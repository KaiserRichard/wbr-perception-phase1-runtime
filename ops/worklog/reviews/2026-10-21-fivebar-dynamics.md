# A4 fixed-length dynamics — 21 October 2026

**Study complete; models are not dynamically equivalent.** Source `140a11b45e035190d89f4af0905b70975dce9f7c`, unchanged assumed mechanics. Exit0,150.709s wall time, nice10, single-thread BLAS,600s cap. The earlier120s attempt produced no final JSON; both attempts are retained.

```sh
# Existing backend Python3.12.13 / NumPy1.26.4 / MuJoCo3.3.7
python -m sim.fivebar.compare --run-dynamics --duration 5 \
  --timesteps .001 .0005 .00025 --epsilons 1e-5 3e-6 1e-6 \
  --output ~/wbr-evidence-archive/sim-fivebar-dynamics-20261021-01/fixed-length-dynamics.json
```

Nine unique cases, finite vectors and step/time accounting checked. All stop on the **reduced model's leg tilt reaching45°**, with null numerical-failure fields. Initial state `[0,.02,-.015,0,0,0]`, fixed length0.16m; wheel/hip pulse `[.02,-.05]`Nm for0.1s, then zero. No controller. These are~0.296s open-loop falls, **not5s of balance**.

| dt(ms) | epsilon | steps | stop(s) | max Δx(m) | max Δtheta(rad) | max Δphi(rad) |
|---:|---:|---:|---:|---:|---:|---:|
|1|1e-5|296|.29600|.003418200|.062710884|.029850415|
|.5|1e-5|592|.29600|.003418200|.062710884|.029850415|
|.25|1e-5|1183|.29575|.003418233|.062592121|.029775726|
|1|3e-6|296|.29600|.003418204|.062710928|.029850425|
|.5|3e-6|592|.29600|.003418204|.062710928|.029850425|
|.25|3e-6|1183|.29575|.003418237|.062592165|.029775736|
|1|1e-6|296|.29600|.003418205|.062710940|.029850428|
|.5|1e-6|592|.29600|.003418205|.062710940|.029850428|
|.25|1e-6|1183|.29575|.003418238|.062592177|.029775739|

Δ means maximum absolute five-bar–reduced difference before stopping. Finest-case peak rate differences: `[.0315746m/s,.479236rad/s,.298670rad/s]`. Epsilon refinement changes terminal five-bar theta by at most5.66e-8rad at fixed dt. At1→.5ms, equal-time terminal theta changes are≤6.19e-10rad. The.25ms case stops.00025s earlier; endpoint differences mix integration and event-time effects. No common-time trajectories, convergence order or equivalence tolerance is claimed.

Snapshot kinematics/hip mapping agree, but angular mass entry is.05653175 versus.05560000kg·m²; wheel input maps are `[16.58375,-.83298,-.16702]` versus `[16.58375,-1,0]` (first entry1/m). Assumed rod mass distribution and distal-link wheel reaction differ from the rigid virtual leg; contributions were not isolated.

Conductor independently checked all9 artifacts and reproduced the1ms/1e-6 case **exactly** in6.96s. Receipts, commands and detailed parser diagnostics remain in the external output directory; no environment/implementation changes or full suites.

**Recommendation:** retain the reduced baseline; establish matched mass/bearing provenance before controller transfer. No full five-bar closed-loop, free-length, contact, jumping, hardware or policy-transfer validation. A separate common-time refinement study would need its own scope.
