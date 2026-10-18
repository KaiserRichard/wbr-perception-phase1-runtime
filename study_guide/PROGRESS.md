# Study guide progress

Status: COMPLETE. No pre-existing WBR_STUDY_GUIDE.md or PROGRESS.md was present. Existing BRIEF.md, run.sh and logs are preserved.

## Scope

Write only inside study_guide/. No hardware, SSH, GUI, generated images, installs, commits or branch changes. Commands in the guide are future operator instructions.

## Source review

Read the audited LAB_PLAN.md, COMMAND_AUDIT.md, steps.json / command-blocks.json structure, lab-config YAML, both base lectures and study-deck teaching text/notes; calibration plan, project state/next gate and canonical architecture/decisions/evidence index. Canonical counterparts are used only where worktree documents are absent. Read lab-day/link sources, CN hardware/E6/E7/synergy/hybrid sources, original OS protocol v1 and newer OS-wt-cn supervisor/v3 integration. REVIEW_CODEX_K.md is absent.

Controlling conflicts: Phase-8 facts override the older 91-page lecture; later still-replay report is dated separately; 6x4 target files override stale 6x6 prose; 192 B/sample native Allan budget overrides 160; original OS v1 does not define newer v3 NET_STATUS behavior; card exception is not accepted by archived N3 runner. No WBR gate is PASS.

## Parts

- Part 0: complete; evidence vocabulary, controlling snapshot and dated later-source limitations.
- Part I theory: complete, Chapters 1–16; prose, derivations, examples, mistakes, answered self-checks, gate tables and simple diagrams. Source correction: link-bench baud is 460800 in source, not 115200 as one slide says. Final quality review complete.
- Part II labs: complete. All 53 audited shell blocks preserved byte for byte; added per-step criterion labels/home consumers/manual checkpoints, actual seventeen-topic count, source-correct bench baud and A-only finalization supplement. Copied all three lab-config YAML files unchanged. Two sessions stay ≤150 min, long Allan at home, conversion/firmware blockers explicit.
- Part III reference: complete; glossary, command lookup, file/representation map, open-gap closure evidence and source precedence/links. Added printable Session-1→2 and home checklists.
- Quality loop: COMPLETE. Final guide 38,026 whitespace words; 16 theory chapters; all 32 steps; 53/53 original blocks unchanged, 54/54 bash -n PASS; 26 static interface groups and all flags for 24 Python invocations checked; 9/9 restricted Mermaid grammar PASS; 22 local links; 69 source hashes. Manual coverage/evidence/arithmetic review and corrected final rerun complete. See CHECKS.md and qa/COVERAGE.md. No hardware qualification is claimed.

## Final deliverables and open project gaps

WBR_STUDY_GUIDE.md, CHECKS.md, PROGRESS.md, unchanged lab-config copies, reproducible validator and qa evidence. The single guide contains introduction/current state, Part I theory, Part II practical sessions/home work and Part III reference.

Open project dependencies are documented in guide R4, not hidden as unfinished document work. No WBR gate PASS, no fabricated receipt, no missing executable invented. The real F446RE bench baud correction and A finalization supplement are documented in CHECKS.md.

To resume a later revision, read this progress file and CHECKS.md, edit the existing guide, and rerun validate_guide.py. Do not restart or reassemble completed parts.
