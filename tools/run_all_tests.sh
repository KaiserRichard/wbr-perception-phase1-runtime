#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export PYTHONDONTWRITEBYTECODE=1

declare -a suite_names=()
declare -a suite_statuses=()
declare -a suite_details=()
failed=0

record_result() {
  suite_names+=("$1")
  suite_statuses+=("$2")
  suite_details+=("$3")
  if [[ "$2" == "FAIL" ]]; then
    failed=1
  fi
}

run_python_suite() {
  local suite_dir="$1"
  local suite_name="python:${suite_dir}"
  if PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "$suite_dir" -p 'test*.py' -v; then
    record_result "$suite_name" "PASS" "unittest discovery"
  else
    local status=$?
    record_result "$suite_name" "FAIL" "unittest exited ${status}"
  fi
}

has_dependency_marker() {
  local makefile="$1"
  local marker
  for marker in ROS ORB_SLAM3 arm-none-eabi hardware; do
    if rg -qi "$marker" "$makefile"; then
      printf '%s' "$marker"
      return 0
    fi
  done
  return 1
}

run_make_suite() {
  local suite_dir="$1"
  local makefile="${suite_dir}/Makefile"
  local dependency=""
  if [[ ! -f "$makefile" ]]; then
    record_result "make:${suite_dir}:test" "SKIPPED" "Makefile is absent"
    return
  fi

  # These five targets were reviewed: each test target exercises host-only C/C++
  # and/or Python code. The ROS bridge target builds only its ROS-free core probe;
  # VIO's default test uses the fake engine and does not enable its optional ORB binding.
  if dependency="$(has_dependency_marker "$makefile")"; then
    case "$suite_dir:$dependency" in
      tools/vio_adapter:ORB_SLAM3|tools/ros2_bridge:ROS) ;;
      *)
        record_result "make:${suite_dir}:test" "SKIPPED" "Makefile references ${dependency}; target requires an unavailable dependency"
        return
        ;;
    esac
  fi

  if [[ "$suite_dir" == "tools/vio_adapter" ]]; then
    if make -C "$suite_dir" CXX="${CXX:-c++}" test; then
      record_result "make:${suite_dir}:test" "PASS" "host fake-engine target"
    else
      local status=$?
      record_result "make:${suite_dir}:test" "FAIL" "make exited ${status}"
    fi
  else
    if make -C "$suite_dir" test; then
      record_result "make:${suite_dir}:test" "PASS" "host target"
    else
      local status=$?
      record_result "make:${suite_dir}:test" "FAIL" "make exited ${status}"
    fi
  fi
}

declare -a python_dirs=()
add_python_dir() {
  local suite_dir="$1"
  local existing
  [[ -d "$suite_dir" ]] || return 0
  for existing in "${python_dirs[@]-}"; do
    [[ "$existing" == "$suite_dir" ]] && return 0
  done
  python_dirs+=("$suite_dir")
}

for suite_dir in tools/*/tests; do
  [[ -d "$suite_dir" ]] && add_python_dir "$suite_dir"
done
add_python_dir tools/trajectory_eval
for suite_dir in calibration/*/tests lab/*/tests tools/eval_pipeline/tests tools/eval_pipeline/*/tests tools/perception_health/tests; do
  [[ -d "$suite_dir" ]] && add_python_dir "$suite_dir"
done

for suite_dir in tools/link_proto tools/link_bench tools/runtime_observer tools/vio_adapter tools/ros2_bridge; do
  run_make_suite "$suite_dir"
done

for suite_dir in "${python_dirs[@]}"; do
  run_python_suite "$suite_dir"
done

printf '\n%-48s %-8s %s\n' "SUITE" "STATUS" "DETAIL"
printf '%-48s %-8s %s\n' "------------------------------------------------" "--------" "------------------------------"
for i in "${!suite_names[@]}"; do
  printf '%-48s %-8s %s\n' "${suite_names[$i]}" "${suite_statuses[$i]}" "${suite_details[$i]}"
done

if (( failed )); then
  exit 1
fi
