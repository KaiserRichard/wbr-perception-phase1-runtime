# Rules for every queued Codex task (no Claude session is supervising you)

You run unattended in your own git worktree (the current directory), branched from
claude/project-thread-ui22me of KaiserRichard/wbr-perception-phase1-runtime. Read first:
research/sw-foundation/PROPOSAL.md, research/sw-foundation/J1_components.md, research/sw-foundation/J2_architecture.md,
and the READMEs of tools/take_tools, tools/calib_tools, tools/link_proto, tools/frames, tools/clockmap, tools/trajectory_eval
(if present). Read-only reference checkout (NEVER write there): /Users/quockaiser/Desktop/Research/wbr-perception-phase1-runtime
(experiments/2026-10-13-n4b-d435i-prep/ holds d435i_input.h, d435i_rs.h, stereo_inertial_d435i_file.patch,
D435i_317422076650_stereo_inertial.yaml; slides_roadmap/research/R1_algorithms.md and R2_integration.md hold design).
Real data (read-only, never copy into the repo): /Users/quockaiser/Desktop/Research/wbr-data/2026-10-14-d435i-ramtest15s/
(take/stereo_imu.db3, take/timestamps.csv, euroc/ = EuRoC export with times_ns.txt).

Hard limits: no ssh, no Raspberry Pi or camera access, no installs, no network package downloads, no git commands
(the runner commits for you), no edits outside your assigned directory unless the task says so. ORB-SLAM3 is NOT built
on this Mac: anything needing it must compile/test without it (fake engine, optional build flag) and say so.
Environment: Python 3.11 + numpy + PyYAML (no pytest), Apple clang (C++17), make. Tests: stdlib unittest or a
Makefile `test` target; they must pass. Rules: frames and timestamps are first class (named transforms T_A_B maps B into A,
clock domain on every stamp, no cross-domain arithmetic), never fabricate results, label claims SOURCE-SUPPORTED / MEASURED /
INFERRED / UNKNOWN, cite upstream source (URL + lines) for any API you depend on, small readable code, English only.
Nothing here is a gate PASS. When done, write <your dir>/REPORT.md: what was built, exact test command and result,
what is verified vs NOT verified, open issues. If you cannot finish, still write REPORT.md starting with "BLOCKED:" or
"FAILED:" and the reason.
