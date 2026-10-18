.PHONY: test
.SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

test:
	mkdir -p tests
	python3 -B -m unittest discover -s . -p 'test_*.py' -v 2>&1 | tee tests/last-run.log
