#!/bin/sh
set -eu
cd "$(dirname "$0")"
cc -std=c11 -Wall -Wextra -Werror -I../firmware test_logic.c -lm -o /tmp/agv_f446_test
/tmp/agv_f446_test
