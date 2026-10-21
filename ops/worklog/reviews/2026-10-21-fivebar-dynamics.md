# A4 fixed-length dynamics — 2026-10-21

**DONE: one authorized study, exit 0, 150.708591 s wall (600 s cap).** Source
`140a11b45e035190d89f4af0905b70975dce9f7c`; branch `chatgpt/20261021-fivebar-dynamics`.
No implementation/physics/threshold changes. The earlier 120 s attempt produced
no final JSON: a resource limit, not an established numerical failure.

Evidence directory and exact commands (wrapper/child argv also in `run-result.json`):

```sh
PY=/private/tmp/wbr-augmented-20261020/protocol-backend-z6w_hksl/.venv/bin/python
OUT=/Users/quockaiser/wbr-evidence-archive/sim-fivebar-dynamics-20261021-01
PYTHONDONTWRITEBYTECODE=1 "$PY" "$OUT/run_study.py"
PYTHONDONTWRITEBYTECODE=1 "$PY" "$OUT/parse_results.py" > /dev/null
# Child command executed once by run_study.py:
"$PY" -m sim.fivebar.compare --run-dynamics --duration 5 \
  --timesteps .001 .0005 .00025 --epsilons 1e-5 3e-6 1e-6 \
  --output "$OUT/fixed-length-dynamics.json"
```

Wrapper set/verified nice 10 and capped `Popen.wait(timeout=600)`; OPENBLAS, OMP,
MKL, VECLIB_MAXIMUM, BLIS and NUMEXPR thread variables were 1; bytecode disabled.
Existing read-only Python 3.12.13 / NumPy 1.26.4 / MuJoCo 3.3.7; no concurrent
heavy job observed. UTC 07:05:10–07:07:40.744. `study.stdout.log` and
`study.stderr.log` are empty; `run-start.json`, `run-result.json`, both scripts,
raw JSON and `parsed-results.json` remain outside git. No retry or source fix.

**Independent artifact checks:** 9/9 unique expected pairs; all 260 saved numeric
values finite; six-state vectors, step/time consistency and recorded tilt stops
checked. Every `failure` is null. Table status `45°` means `45_degree_stop`,
triggered by **reduced-model theta**; times are simulated, not per-case wall
times (unrecorded). Initial state `[0,.02,-.015,0,0,0]`; fixed length 0.16 m;
wheel/hip pulse `[.02,-.05]` N m for 0.1 s, then zero; no controller.

| dt (ms) | epsilon | status | steps | time (s) | max absolute Δ[x, theta, phi] (m, rad, rad) |
|---:|---:|---|---:|---:|---|
| 1 | 1e-5 | 45° | 296 | .29600 | .003418200, .062710884, .029850415 |
| .5 | 1e-5 | 45° | 592 | .29600 | .003418200, .062710884, .029850415 |
| .25 | 1e-5 | 45° | 1183 | .29575 | .003418233, .062592121, .029775726 |
| 1 | 3e-6 | 45° | 296 | .29600 | .003418204, .062710928, .029850425 |
| .5 | 3e-6 | 45° | 592 | .29600 | .003418204, .062710928, .029850425 |
| .25 | 3e-6 | 45° | 1183 | .29575 | .003418237, .062592165, .029775736 |
| 1 | 1e-6 | 45° | 296 | .29600 | .003418205, .062710940, .029850428 |
| .5 | 1e-6 | 45° | 592 | .29600 | .003418205, .062710940, .029850428 |
| .25 | 1e-6 | 45° | 1183 | .29575 | .003418238, .062592177, .029775739 |

At .25 ms / 1e-6, peak rate differences are `[.0315746 m/s, .479236 rad/s,
.298670 rad/s]`. **Refinement:** at fixed dt, epsilon 1e-5→3e-6→1e-6 leaves
stop times unchanged; five-bar terminal theta changes shrink from about
4.4e-8 to 1.25e-8 rad; largest theta/rate spreads are 5.66e-8 rad / 1.13e-6 rad/s.
The reduced results are identical across epsilon. For 1→.5 ms, both endpoints
are .296 s: terminal theta changes ≤6.19e-10 rad and theta-rate changes
≤3.45e-9 rad/s across models/epsilons. For .5→.25 ms, the stop is .00025 s
earlier; terminal theta changes ~.00176/.00188 rad (five-bar/reduced) mix time
offset with integration error. Summaries contain no common-time trajectories;
no convergence order, new tolerance or equivalence PASS is inferred.

**Interpretation/limits:** snapshot closure 1.03e-16 m, largest hip-position error
2.78e-17 m and hip-map component error 7.24e-11 support fixed-length kinematic/
hip mapping agreement. Yet H(theta,theta)=.05653175 versus .05560000 kg m²;
wheel maps `[16.58375,-.83298,-.16702]` versus `[16.58375,-1,0]` (first component
1/m). Equal total leg mass does not match rod COMs/inertias to the rigid leg;
the assumed wheel stator reacts on a distal link, not the virtual leg. Persistent
differences are consistent with these ASSUMED mechanics; their individual
contributions were not isolated. These are ~.296 s open-loop falls, **not five
valid seconds or balance tests**. No full five-bar closed-loop control,
free-length/contact/jumping, hardware or policy-transfer validation.

**Recommendation:** retain the reduced baseline; establish measured/matched mass
and bearing provenance before any controller/policy transfer, and seek conductor
approval for a separate common-time trajectory/stop-event refinement study.
Documentation only: README pending claims updated; no full suites run locally.
PR is for conductor inspection/green-CI merge; no worker merge or Claude request.
