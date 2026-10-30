# 31 Oct plan: tickets for the AI team (prepared by Claude 1 on 30 Oct)

Start of day (whoever is conductor): `zsh ops/tickets/2026-10-31/launch.sh wave1`, then `launch.sh status` every so often.
Quota at the end of 30 Oct: codex-k (Plus) 22 % of the week used, resets 4 Nov, so it gets the heavy report work. codex-e (Plus) is about 70 %+ used and resets 1 Nov 08:53, so it only gets the Vietnamese translation. Free accounts: c, b and a are freshest; d, g and h are 74–85 % used. agy has Gemini only (its Claude models return around 6 Nov). codex-b was busy with another session: check before use.

## Wave 1 (parallel, about 1–2 h)
| ID | Worker | What | Output | Done when |
|---|---|---|---|---|
| A1 | codex-k | Owner's PDF comments: bigger diagrams, no evidence appendix, Drive links, remove page-1 photo | report/WBR_Phase1_Report.pdf/.docx | conductor checks pages 1, 7 and the last page |
| A2 | codex-c | Professor-style critique (read-only) | review_next/REVIEW_FOR_OWNER.md | prioritised list + 5 likely questions |
| A4 | codex-a | MuJoCo model generator from a YAML manifest (ready for CAD data) | ~/.worktrees/wbr-c1-model, sim/wbr_model | headless 1000-step test passes; conductor commits + PR |
| A5 | codex-j | YOLO 320 px / INT8 variants, Mac benchmark + Pi script | p1-run/VARIANTS.md | table + pi_bench_variants.sh |
| A6 | codex-h | Staged sim/compute plan (Mac, brother's laptop, Chợ Mơ, lab, cloud) | ~/.worktrees/wbr-c1-simplan/research/compute/SIM_COMPUTE_PLAN.md | stage x machine table + 10-min benchmarks; conductor commits + PR |

## Wave 2 (in sequence, same files)
| B1 | codex-k | Apply A2's high/medium items to the English report | report + review_next/APPLIED.md | after A1 and A2 |
| B2 | codex-e | Vietnamese version | report_vi/BaoCao_WBR_GiaiDoan1.pdf/.docx | after B1 |

## Owner (needs your hands or your decision)
1. Read the English report after B1 and send it to your supervisor (check the cover line and Drive sharing).
2. OS midterm: read ~/.worktrees/OS-wt-report/report_vi/BaoCao_HDH_Nhom3Stars_GiuaKy.docx, fill any "đang cập nhật" items, submit. Conductor commits it to the OS repo afterwards.
3. Close PR #155. Pick roadmap program (a) or (b).
4. Pi on: run `pi_bench_variants.sh` (from A5) to get real Pi FPS for the YOLO variants (about 10 min).
5. Lab day (if any): FINAL_LAB_RUNBOOK. The Nucleo runs T3 now, so flash the LED image first (BOOT0 + RESET).
6. Brother's CAD/mass data: put it in a folder; then a codex-k ticket fills the manifest and rebuilds the model with A4's generator.

## Conductor (Claude)
- Verify each output (open the file, spot-check numbers), commit and push the A4/A6 branches, open PRs, merge when green.
- End of day: write FACTS_DAY.md, then agy runs C1-session-log-agy.txt (`~/.local/bin/agy --model gemini-3.8-flash-high -p "$(cat C1-session-log-agy.txt)"` from that folder) and copies it to Obsidian.
- Do not leave jobs running overnight: the owner closes the Mac.
