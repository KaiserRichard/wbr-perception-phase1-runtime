# Lab-day Foxglove overlays and flicker replay

## Result

- Completed the requested offline artifacts on `claude2/20261025-lab-fixes`; no PR was opened and all changes remain uncommitted.
- Generated `foxglove-out/{2-books46,3-box13,4-approach,4-approach-r2,4-approach-r3}.mcap`, the unchanged source layout JSON, and `FLICKER_REPORT.md`.
- The report gives per-run advisory duration, all transition times for old/new/live sequences, and exact-frame old/live agreement. New defaults reduced transition counts on three of five takes; old replay/live agreement ranged from 50.7% to 99.8%.

## Commands and results

- `python tools/obstacle_decision/flicker_check.py <archive> ./foxglove-out/FLICKER_REPORT.md` — all five runs completed.
- `python tools/bag_tools/foxglove_demo.py <run>/camera-bag ./foxglove-out/<run>.mcap --max-forward 1.3 --range-hysteresis 0.10` — all five conversions completed.
- Layout copy matched `tools/bag_tools/foxglove_demo_layout.json` byte-for-byte. Output directory is 9.0 GB.

## Limitations

- The archived `4-approach-r3` MCAP lacks metadata and ends 1,535,989 bytes into a record. Replay and conversion used its complete record prefix plus a temporary footer; the archive was not changed. This yields 2,465 depth frames and is not a cleanly finalized source capture.
- Foxglove GUI rendering was not checked. No tests were added or run.

Claude: review the offline range-filter integration and MCAP recovery behavior in this worktree; changes remain uncommitted by request.
