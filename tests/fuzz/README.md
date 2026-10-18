# Parser mutation fuzzing

This directory fuzzes the parser entry points named in T25 without changing the parsers. Python uses only the standard library except that `trajectory_eval` requires the repository's existing NumPy dependency. The fixed seed and workload are in `fuzz_config.json`; each Python input has a PROPOSED 0.25 s signal timeout. C mutation drivers use AddressSanitizer and UndefinedBehaviorSanitizer with no libFuzzer dependency. `ITERATIONS` and `SEED` can be overridden for a longer local run.

## Run

From the repository root on macOS or Linux:

```sh
make -C tests/fuzz test
```

This runs `test_fuzz.py` and 1,200 mutations per C codec, designed to finish in under 60 seconds. To run Python alone: `make -C tests/fuzz python`. To build/run the sanitizer drivers alone: `make -C tests/fuzz c`. `make -C tests/fuzz clean` removes generated binaries. The recorded run is `tests/last-run.log`.

The fixture `corpus/rosbag_real_header.cdr` is copied from the MEASURED saved-header fixture at `lab/rosbag_qual/tests/real_header_fixture.json`; its scope is parser behavior only. `corpus/link_proto_health_frozen.bin` is the project's frozen synthetic wire vector. These fixtures and passing fuzz runs are tooling evidence, not a system or hardware gate PASS.

## Coverage and limits

Coverage includes the perception-health Python stream parser and payload decoder, perception-health C frame decoder, link_proto Python COBS encoder inputs, link_proto C COBS/frame/stream decoder, `lab/rosbag_qual` CDR header reader, `tools/n4b_offline/db3_to_euroc.py` CDR header reader, and trajectory file reader. The Python tests include truncation, bit flips, arbitrary bytes, malformed/oversized lengths where represented by the format, reversed timestamps, NaN/inf values, and round-trip checks for accepted frames. The C drivers mutate generated valid health records with deterministic byte changes and truncation. This small corpus does not establish exhaustive safety or denial-of-service resistance.

`tools/run_all_tests.sh` currently does not discover files under `tests/`. Add this one line to its unittest discovery list when that runner is next updated:

```sh
python3 -m unittest discover -s tests/fuzz -p 'test_*.py' -v
```

The MCU-side `ph_rx` implementation was not present in this checkout (`rg --files` found no `ph_rx` source), so no driver could be built for it. This is a coverage limitation, not a parser finding. There are no identified crash, hang, or incorrect-accept findings from this bounded run.
