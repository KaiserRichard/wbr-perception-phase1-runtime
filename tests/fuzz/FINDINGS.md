# Fuzz findings

No crash, hang, or incorrect accept was identified in the bounded T25 run (1,200 C mutations per available C codec and deterministic Python mutation sets). Therefore there are no minimized bug reproducers or expected-failure tests.

**Coverage limitation:** the requested MCU-side `ph_rx` source is absent from this worktree; `rg --files` did not find it. The host `tools/perception_health/c` codec was fuzzed. The MCU decoder remains unverified until its source is available. This is not an identified bug.
