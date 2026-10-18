# Study guide checks

Status: **COMPLETE — document quality loop passed.** Hardware gates remain as stated in the guide. Final review date: 2026-10-18.

Guide: `WBR_STUDY_GUIDE.md`
Whitespace word count: **38,026** (includes headings, tables, math and printed commands).
Guide SHA-256: `163361123195a3b27e15a912f5602f37bef38b6104d2fd049bd72ebe6ddc0ddc`.

## What was checked

| Check | Final result |
|---|---|
| Scope and continuation | No existing guide/progress was present. Original BRIEF.md, run.sh and logs preserved. All created/edited files are inside study_guide/. |
| Required source/subject coverage | Sixteen theory chapters, every required topic, examples/mistakes/answered self-checks, both sessions and H0–H7; see qa/COVERAGE.md. |
| Original commands | **53/53 unchanged**, byte-for-byte against LAB_PLAN.md, steps.json and prior command-block SHA-256 records. |
| Supplemental command | One A-only finalization block preserves the actual ros-imu.yaml configuration. It replaces S/C finalization for A; source blocks retained. |
| Shell syntax | **54/54 PASS**, extracted to qa/command-*.bash and checked with `/bin/bash -n`; no command body executed. |
| Real interfaces | **26 implementation/interface groups** checked read-only, including fixed Foundation dependencies and the actual generic ORB C++ argument order. |
| Python command flags | Every long flag in **24 Python invocations** checked against source literals/generated argparse options without importing or running the target entry points. |
| Shell/C/ROS semantics | Positional shell guards, fixed roots, C long-option names, ROS argv in gate source, launch configurable_parameters and metadata publisher fields inspected. Target installation remains UNVERIFIED. |
| Configuration | All three copied YAMLs match source bytes. Flat launch keys checked against real rs_launch.py, with explicitly identified SDK-dynamic format/emitter keys. |
| Topics | Seventeen unique extended S/C topics; nine A selected topics; strict N3 ten-topic baseline distinguished. |
| Mermaid | **9/9 PASS** in a deliberately restricted flowchart grammar: quoted rectangular nodes, identifiers, simple arrows/chains and labels. All references defined; no exotic syntax. No renderer installed/run and no layout claim. |
| Markdown | Fences/details balanced; every theory chapter has pedagogical closure; **22 local links resolve**. External links are source-provided reading pointers, not freshly accessed verification. |
| Lab steps | **32/32** retain goal/setup/expected/criterion/recovery/files and add explicit criterion classification and home consumer. |
| Numeric/technical review | Independent arithmetic recomputation and manual causal/evidence review in qa/arithmetic.json and qa/COVERAGE.md. |
| Gate/evidence review | All WBR gates remain OPEN/not started. Dated later observations, measured summaries, assumptions, provisional OS defaults and missing data are distinct. |
| Provenance | **69 source files** hashed in qa/source-hashes.json. REVIEW_CODEX_K.md absent. |
| Theory depth | 18,530 theory words versus 15,228 lab words; introduction/reference separately counted. |

## Corrections made during the loop

- Source-correct link bench is **460800 baud**. The slide's 115200 label beside a 3.65 ms floor contradicts real script/firmware and framing arithmetic. Both inspected sources and the calculation agree; copied commands use the correct default.
- Extended topic count corrected to seventeen from the actual array.
- A-only finalization saves ros-imu.yaml; S/C retains ros-stereo.yaml. This avoids claiming an unused launch recipe was used.
- Explicitly expanded manual checkpoints and per-terminal bindings without altering audited command bytes.
- Retained 6×4 target precedence, native 192 B/sample budget, Phase-8 exclusion of historical RPE/paper numbers, and all conversion/firmware/clock gaps.
- First static checker attempt could not resolve generated trajectory argparse f-strings. Inspected the actual finite literal loop and corrected the checker; no guide flag changed to conceal the issue.

The loop was: source review → draft parts/progress → automated extraction/checks → manual coverage/evidence/arithmetic review → corrections → full final rerun. Results are in qa/final-checks.json, command-agreement.json, commands.json, source-interface-checks.json, python-cli-flags.json, mermaid.json, local-links.json and COVERAGE.md.

## Reproduce document checks

From the worktree root, run:

```bash
python3 study_guide/validate_guide.py
```

This writes only study_guide/qa/. It invokes Bash only with `-n` and never executes the printed hardware/lab commands. It requires the same read-only local sources to be available. `assemble_labs.py` is the original assembly helper and deliberately refuses a guide already containing Part II; do not rerun it to replace completed work.

## Remaining limits

No hardware, SSH, network mutation, GUI, firmware action, generated image, install, commit or branch change occurred. Static interface support is not installed-tool or real-hardware qualification. The required project gaps are summarized in guide R4: N3 card receipt/loaded sensor qualification, ROS analysis/native companion adapters, calibrated motion/reference data, full E7/v3 image/result producer, bounded HOLD-only fault and WBR N6/N7 evidence.
