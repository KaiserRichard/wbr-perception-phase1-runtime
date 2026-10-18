# T25 report — parser robustness fuzzing

## Built

Added deterministic Python parser mutation tests and sanitizer-backed C mutation drivers under `tests/fuzz/`, with fixed inputs and thresholds in `fuzz_config.json`. The tests exercise perception-health stream parsing, available perception-health C decoding, link_proto COBS/frame/stream handling, both ROS CDR header readers, and trajectory file parsing. A MEASURED real rosbag header fixture is used alongside frozen/synthetic vectors. Parser implementations were not modified.

## Verification

`make -C tests/fuzz test` completed successfully on the development Mac with Python 3.11 and the available C compiler. Five Python unittest cases passed; both C programs completed 1,200 seeded mutations under AddressSanitizer and UndefinedBehaviorSanitizer. Full output is saved in `tests/last-run.log`. The run is bounded fixture/tooling evidence only, not a hardware gate PASS.

## Not verified and risks

No Pi, MCU hardware, or hardware transport was used. The MCU `ph_rx` source is absent from this worktree, so that requested decoder could not be compiled or exercised. Python timeouts use Unix `SIGALRM`, and tests require NumPy through the existing trajectory evaluator dependency. Short deterministic mutation runs can miss parser defects. See `FINDINGS.md`.

Proposed commit message: `Add bounded parser mutation fuzz coverage`
