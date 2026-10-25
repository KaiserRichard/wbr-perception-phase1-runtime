# Live advisory summary

- Added `tools/link_bench/pi/summarize_live.py` to summarize one or more advisory output directories and write `advisory_summary.png` per run.
- Added `tools/link_bench/tests/test_summarize_live.py` with synthetic ROS-style packet rows covering advisory histograms, confirmed-only medians, latency percentiles, rejection/stale counts, and plot creation.
- First test attempt failed because the expected interpolated receipt-to-send P95 was 6.4 ms; corrected the fixture expectation to 6.7 ms.
- Pass: `MPLCONFIGDIR=/private/tmp/wbr-link-bench-mpl-cache python3 -m unittest tools.link_bench.tests.test_summarize_live` — 1 test, OK. Matplotlib emitted a non-fatal fontconfig cache warning in this restricted environment.
- No live Pi/ROS/bag run performed; validate on a fresh output directory when one is available.
