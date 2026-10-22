# 2026-10-22 — one authorized v3 residual pilot

- Owner relayed Claude approval (implementation PR126 merged, review PR127) and
  authorized saved-v2 diagnostic plus exactly ONE residual pilot. No full run,
  direct arm, retries, reward/v2 changes or fixes after a run failure.
- Used isolated `chatgpt/20261022-v3-pilot-result` worktree from main14df6df;
  shared Mac/perception checkouts unchanged. Current account k verified Plus;
  strongest Astra/ultra worker prepared/recomputed the report, conductor ran CPU.
- Existing README venv was present. `"$PY" -m unittest
  sim.rl.tests.test_v3_pilot sim.rl.tests.test_v2 -v`:35PASS/20.545s, exit0.
  Docker ps empty; no other training or SLAM process found before launch.
- Diagnostic command used unchanged README archive/LQR-trace paths and new
  `~/wbr-evidence-archive/sim-v3-pilot-20261022-01/diagnostic`; exit0. Seeds0–2
  retained upright residuals at all four delays and residual series/statistics
  along the saved LQR trajectory, with frozen observation normalization.
- Exactly one `"$PY" -m sim.rl.v3_pilot run --out
  ~/wbr-evidence-archive/sim-v3-pilot-20261022-01/pilot`; external one-shot
  launcher recorded argv/source14df6df/seed42/attempt1 and preserved console.
  Started11:01:03UTC, finished11:16:02UTC; supervisor exit0,899.227s wall.
- First progress check137.549s after launch: snapshot0 had14/16 cases, no
  learning yet. Next check80k transitions/142.371active seconds projected
  33714.84transitions/minute (~2.966active minutes to100k). Continued unchanged.
- Snapshot0 strict16/16 passed; exact constructed/reloaded actor+LQR parity
  passed all4 delays. One pilot completed260000aggregate transitions,
  130updates/1300000plant ticks/256complete episodes; no early stop or retry.
- Stop:target_transitions_and_minimum_duration. Active training460.101s;
  budget603.463s (includes100k evaluation), all evaluations420.730s,
  internal wall890.684s, minimum overshoot3.463s,20min overrun0.
- Snapshot0/100k/final strict16/16/11 of16; survival16 each, leg-rate0 each;
  E0.2924332808274505/0.44729312198262994/0.8260700554275315. Pilot FAIL on final
  strict and both E screens; other five screens passed. This is a completed
  run with failed screens, not an infrastructure failure; no error.txt exists.
- First/last50k each48complete episodes: mean return583.6263439237264 /
  659.8651132665905; mean length1000/1000. Conductor independently recomputed
  every panel/window and matched recorded summaries; max raw return vs reward
  component reconstruction error1.93e-12. All episode/update logs retained.
- Full evidence including checkpoints, learning-curves.svg, diagnostic series,
  original logs, launch receipt and report helper stays in the external archive.
  Only result review/CURRENT/this session enter git; no DOCLOG/DECISIONS entry.
- After process exit, fast-forwarded report branch to e0b74b5 (merged PR127,
  review text only). Experiment source remains14df6df; no sim files changed.
- Handoff:`reviews/2026-10-22-v3-pilot-result.md`; result PR remains open for
  Claude after green CI. No rerun, full training, direct arm or hardware action.
