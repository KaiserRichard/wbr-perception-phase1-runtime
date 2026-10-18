.PHONY: test
SHELL := /bin/bash

test:
	mkdir -p tests
	set -euo pipefail; python3 -B -m unittest discover -s . -p 'test_*.py' -v 2>&1 | tee tests/last-run.log
