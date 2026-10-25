# TerrainAdvisory firmware proposal — 2026-10-25

- Read the obstacle advisory/link specs, 24 Oct lab evaluation, F446 real-UART results, F446 build-size report, perception-health enum spec, and 25 Oct live-advisory summary.
- Drafted `docs/proposals/TERRAIN_ADVISORY_FIRMWARE_PROPOSAL.md` (about 150 lines) for STM32H7 firmware-owner review.
- Included receive-only boundary, type 4/5 framing and fields, MEASURED/CALCULATED/ASSUMED evidence labels, detector and saved-bag timing, UART fault/loss and timeout observations, F446 size reference, open decisions, and a proposed H7 bench plan.
- Left `Live LED tests 25 Oct` as an explicit TODO: the existing report says no physical LED test was performed.
- No firmware or hardware commands/tests run; no live Pi run, board flashing, motor action, commit, push, or branch switch.
