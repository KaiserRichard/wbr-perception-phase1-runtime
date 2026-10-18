#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
ROS_PREFIX="${WBR_ROS_PREFIX:-/opt/ros/jazzy}"
WORKSPACE="${WBR_COLCON_WORKSPACE:-$HOME/wbr-colcon-ws}"
OUTDIR="${WBR_COLCON_OUTDIR:-$WORKSPACE/wbr-colcon-evidence}"
ORB_ROOT="${WBR_ORB_SLAM3_ROOT:-$HOME/orbslam3/ORB_SLAM3}"
PLAN=0

usage() {
  cat >&2 <<'USAGE'
usage: build_on_pi.sh [--plan] [--ros-prefix PATH] [--workspace PATH]
                      [--outdir PATH] [--orb-root PATH]
USAGE
}
while (($#)); do
  case "$1" in
    --plan) PLAN=1; shift ;;
    --ros-prefix|--workspace|--outdir|--orb-root)
      (($# >= 2)) || { usage; exit 3; }
      case "$1" in
        --ros-prefix) ROS_PREFIX="$2" ;;
        --workspace) WORKSPACE="$2" ;;
        --outdir) OUTDIR="$2" ;;
        --orb-root) ORB_ROOT="$2" ;;
      esac
      shift 2 ;;
    -h|--help) usage >&1; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage; exit 3 ;;
  esac
done

ORB_LIB="$ORB_ROOT/lib/libORB_SLAM3.so"
ORB_MODE=OFF
ORB_REASON="ORB library absent at $ORB_LIB; building wbr_orb_node without ORB-SLAM3"
if [[ -f "$ORB_LIB" ]]; then
  ORB_MODE=ON
  ORB_REASON="ORB library present at $ORB_LIB; enabling native ORB-SLAM3"
fi

declare -a PACKAGE_DIRS=() PACKAGE_NAMES=() TEST_NAMES=()
for package_dir in "$REPO_ROOT"/ros2/*; do
  [[ -d "$package_dir" && -f "$package_dir/package.xml" ]] || continue
  package_name="$(sed -n 's:^[[:space:]]*<name>\([^<]*\)</name>.*:\1:p' "$package_dir/package.xml" | head -n 1)"
  [[ -n "$package_name" ]] || { echo "package has no <name>: $package_dir" >&2; exit 3; }
  PACKAGE_DIRS+=("$package_dir")
  PACKAGE_NAMES+=("$package_name")
  if [[ -d "$package_dir/tests" ]] && find "$package_dir/tests" -type f -print -quit | grep -q .; then
    TEST_NAMES+=("$package_name")
  fi
done
if ((${#PACKAGE_NAMES[@]} == 0)); then
  echo "no ROS 2 package.xml files found below $REPO_ROOT/ros2" >&2
  exit 3
fi

print_cmd() { printf '%q ' "$@"; printf '\n'; }
if ((PLAN)); then
  echo "# WBR ROS 2 Jazzy colcon plan"
  echo "# ORB_MODE=$ORB_MODE ($ORB_REASON)"
  print_cmd mkdir -p "$WORKSPACE/src" "$OUTDIR"
  for package_dir in "${PACKAGE_DIRS[@]}"; do
    package_name="$(sed -n 's:^[[:space:]]*<name>\([^<]*\)</name>.*:\1:p' "$package_dir/package.xml" | head -n 1)"
    print_cmd ln -s "$package_dir" "$WORKSPACE/src/$package_name"
  done
  print_cmd source "$ROS_PREFIX/setup.bash"
  if [[ " ${PACKAGE_NAMES[*]} " == *" wbr_orb_node "* ]]; then
    build_orb=(colcon build --symlink-install --packages-select wbr_orb_node --cmake-args "-DWITH_ORB_SLAM3=$ORB_MODE")
    [[ "$ORB_MODE" == ON ]] && build_orb+=("-DORB_SLAM3_ROOT=$ORB_ROOT")
    print_cmd env MAKEFLAGS=-j2 "${build_orb[@]}"
    other_names=()
    for package_name in "${PACKAGE_NAMES[@]}"; do
      [[ "$package_name" == wbr_orb_node ]] || other_names+=("$package_name")
    done
    ((${#other_names[@]} == 0)) || print_cmd env MAKEFLAGS=-j2 colcon build --symlink-install --packages-select "${other_names[@]}"
  else
    print_cmd env MAKEFLAGS=-j2 colcon build --symlink-install --packages-select "${PACKAGE_NAMES[@]}"
  fi
  if ((${#TEST_NAMES[@]})); then
    print_cmd env MAKEFLAGS=-j2 colcon test --packages-select "${TEST_NAMES[@]}" --event-handlers console_direct+
    print_cmd colcon test-result --verbose
  else
    echo "# no package tests detected"
  fi
  exit 0
fi

mkdir -p "$OUTDIR"
STARTED_UTC="$(date -u +%FT%TZ)"
CRITERIA_FILE="$OUTDIR/criteria.tsv"; NOTES_FILE="$OUTDIR/notes.txt"; PROVENANCE_LOG="$OUTDIR/provenance.log"
: > "$CRITERIA_FILE"; : > "$NOTES_FILE"; : > "$PROVENANCE_LOG"
add_note() { printf '%s\n' "$*" >> "$NOTES_FILE"; }
add_criterion() { printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$@" >> "$CRITERIA_FILE"; }

write_result() {
  local status="$1" exit_code="$2" ended_utc
  ended_utc="$(date -u +%FT%TZ)"
  python3 - "$OUTDIR" "$status" "$exit_code" "$STARTED_UTC" "$ended_utc" "$REPO_ROOT" "$WORKSPACE" "$ROS_PREFIX" "$ORB_ROOT" "$ORB_MODE" <<'PY'
import hashlib, json, platform, sys
from pathlib import Path
outdir = Path(sys.argv[1])
status, exit_code, started, ended = sys.argv[2:6]
repo_root, workspace, ros_prefix, orb_root, orb_mode = sys.argv[6:]
criteria = []
for line in (outdir / "criteria.tsv").read_text(encoding="utf-8").splitlines():
    fields = line.split("\t")
    if len(fields) != 8: continue
    ident, description, measured, unit, threshold, cstatus, evidence, source = fields
    criteria.append({"id": ident, "description": description,
        "measured": None if measured == "null" else measured, "unit": unit,
        "threshold": threshold, "status": cstatus, "evidence": evidence,
        "threshold_source": source})
raw_files = []
for path in sorted(outdir.rglob("*")):
    if path.is_file() and path.name != "result.json":
        raw_files.append({"path": str(path.relative_to(outdir)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
notes = (outdir / "notes.txt").read_text(encoding="utf-8").splitlines()
result = {"check": "ros2_colcon_build", "tool_version": "build_on_pi/1.0",
    "status": status, "started_utc": started, "ended_utc": ended,
    "host": {"system": platform.system(), "release": platform.release(),
             "machine": platform.machine(), "python": platform.python_version()},
    "criteria": criteria, "raw_files": raw_files, "notes": notes,
    "provenance": {"repo_root": repo_root, "workspace": workspace,
        "ros_prefix": ros_prefix, "orb_root": orb_root, "orb_mode": orb_mode},
    "exit_code": int(exit_code)}
(outdir / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
PY
}

if [[ ! -f "$ROS_PREFIX/setup.bash" ]]; then
  echo "BLOCKED: ROS 2 Jazzy setup not found: $ROS_PREFIX/setup.bash" >&2
  add_criterion ros_setup "ROS 2 Jazzy setup exists" null path present BLOCKED notes.txt "Pi prerequisite: /opt/ros/jazzy/setup.bash"
  add_note "BLOCKED: source $ROS_PREFIX/setup.bash is absent; no workspace was changed."
  write_result BLOCKED 2
  exit 2
fi
missing_tools=()
for tool in python3 git colcon cmake gcc sha256sum; do
  command -v "$tool" >/dev/null 2>&1 || missing_tools+=("$tool")
done
if ((${#missing_tools[@]})); then
  echo "BLOCKED: missing required command(s): ${missing_tools[*]}" >&2
  add_criterion tools "Required Pi build commands are available" "${missing_tools[*]}" commands "all present" BLOCKED notes.txt "Pi build prerequisite"
  add_note "BLOCKED: missing command(s): ${missing_tools[*]}"
  write_result BLOCKED 2
  exit 2
fi
add_criterion ros_setup "ROS 2 Jazzy setup exists" present path present PASS provenance.log "Pi prerequisite: /opt/ros/jazzy/setup.bash"
# shellcheck disable=SC1090
source "$ROS_PREFIX/setup.bash"

set +e
{
  echo '$ git rev-parse HEAD'; git -C "$REPO_ROOT" rev-parse HEAD
  echo '$ colcon --version'; colcon --version
  echo '$ cmake --version'; cmake --version
  echo '$ gcc --version'; gcc --version
  echo "'$ sha256sum $ORB_LIB'"
  if [[ -f "$ORB_LIB" ]]; then sha256sum "$ORB_LIB"; else echo "ABSENT $ORB_LIB"; fi
} > "$PROVENANCE_LOG" 2>&1
provenance_rc=$?
set -e
if ((provenance_rc != 0)); then
  echo "BLOCKED: provenance command failed; see $PROVENANCE_LOG" >&2
  add_criterion provenance "Git, colcon, CMake, GCC and ORB provenance recorded" null entries present BLOCKED provenance.log "T30 provenance requirement"
  add_note "BLOCKED: one or more provenance commands failed with exit code $provenance_rc."
  write_result BLOCKED 2
  exit 2
fi
git_commit="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || true)"
colcon_version="$(colcon --version 2>&1 || true)"; colcon_version="${colcon_version%%$'\n'*}"
cmake_version="$(cmake --version 2>&1 || true)"; cmake_version="${cmake_version%%$'\n'*}"
gcc_version="$(gcc --version 2>&1 || true)"; gcc_version="${gcc_version%%$'\n'*}"
orb_sha=""
if [[ -f "$ORB_LIB" ]]; then orb_sha="$(sha256sum "$ORB_LIB" | awk '{print $1}')"; fi
python3 - "$OUTDIR/provenance.json" "$git_commit" "$colcon_version" "$cmake_version" "$gcc_version" "$ORB_LIB" "$orb_sha" <<'PY'
import json, sys
from pathlib import Path
out, commit, colcon, cmake, gcc, orb_lib, orb_sha = sys.argv[1:]
Path(out).write_text(json.dumps({"git_commit": commit or "UNKNOWN",
    "colcon_version": colcon or "UNKNOWN", "cmake_version": cmake or "UNKNOWN",
    "gcc_version": gcc or "UNKNOWN", "orb_library": orb_lib,
    "orb_library_sha256": orb_sha or None}, indent=2) + "\n")
PY
add_criterion provenance "Git, colcon, CMake, GCC and ORB provenance recorded" recorded entries present PASS provenance.json "T30 provenance requirement"
echo "ORB_MODE=$ORB_MODE: $ORB_REASON"
add_note "ORB mode: $ORB_MODE. $ORB_REASON."
add_note "MAKEFLAGS=-j2 is the bounded Pi build setting required by T30 and the measured Pi RAM/thermal constraints."

mkdir -p "$WORKSPACE/src"
for index in "${!PACKAGE_DIRS[@]}"; do
  package_dir="${PACKAGE_DIRS[$index]}"; package_name="${PACKAGE_NAMES[$index]}"
  link="$WORKSPACE/src/$package_name"
  if [[ -L "$link" ]]; then
    [[ "$(readlink "$link")" == "$package_dir" ]] || { echo "existing workspace link points elsewhere: $link" >&2; add_note "FAIL: workspace link points elsewhere: $link"; add_criterion workspace_links "ROS package symlinks point to this checkout" null links correct FAIL notes.txt "T30 workspace ownership"; write_result FAIL 1; exit 1; }
  elif [[ -e "$link" ]]; then
    echo "refusing to replace non-symlink workspace path: $link" >&2
    add_note "FAIL: refusing to replace non-symlink $link"
    add_criterion workspace_links "ROS package symlinks point to this checkout" null links correct FAIL notes.txt "T30 workspace ownership"
    write_result FAIL 1; exit 1
  else
    ln -s "$package_dir" "$link"
  fi
done
add_criterion workspace_links "ROS package symlinks point to this checkout" "${#PACKAGE_DIRS[@]}" packages "all direct ros2 packages" PASS provenance.json "T30 symlink workspace requirement"

build_failed=0; build_log="$OUTDIR/build.log"
build_orb=(colcon build --symlink-install --packages-select wbr_orb_node --cmake-args "-DWITH_ORB_SLAM3=$ORB_MODE")
[[ "$ORB_MODE" == ON ]] && build_orb+=("-DORB_SLAM3_ROOT=$ORB_ROOT")
{
  echo "# ${build_orb[*]}"
  if ! MAKEFLAGS=-j2 "${build_orb[@]}"; then build_failed=1; fi
  other_names=()
  for package_name in "${PACKAGE_NAMES[@]}"; do
    [[ "$package_name" == wbr_orb_node ]] || other_names+=("$package_name")
  done
  if ((${#other_names[@]})); then
    echo "# colcon build --symlink-install --packages-select ${other_names[*]}"
    if ! MAKEFLAGS=-j2 colcon build --symlink-install --packages-select "${other_names[@]}"; then build_failed=1; fi
  fi
} > "$build_log" 2>&1
if ((build_failed)); then
  echo "FAIL: colcon build failed; see $build_log" >&2
  add_criterion build "All discovered ROS 2 packages build" null packages pass FAIL build.log "T30 colcon build requirement"
  write_result FAIL 1; exit 1
fi
add_criterion build "All discovered ROS 2 packages build" "${#PACKAGE_NAMES[@]}" packages pass PASS build.log "T30 colcon build requirement"

if ((${#TEST_NAMES[@]})); then
  test_failed=0; test_log="$OUTDIR/test.log"
  {
    echo "# colcon test --packages-select ${TEST_NAMES[*]} --event-handlers console_direct+"
    if ! MAKEFLAGS=-j2 colcon test --packages-select "${TEST_NAMES[@]}" --event-handlers console_direct+; then test_failed=1; fi
    echo "# colcon test-result --verbose"
    if ! colcon test-result --verbose; then test_failed=1; fi
  } > "$test_log" 2>&1
  if ((test_failed)); then
    echo "FAIL: colcon test failed; see $test_log" >&2
    add_criterion tests "colcon tests for packages containing tests pass" null packages pass FAIL test.log "T30 test requirement"
    write_result FAIL 1; exit 1
  fi
  add_criterion tests "colcon tests for packages containing tests pass" "${#TEST_NAMES[@]}" packages pass PASS test.log "T30 test requirement"
else
  echo "No package tests detected; colcon test was not applicable."
  add_note "No package tests directory was found among discovered packages."
  add_criterion tests "colcon tests for packages containing tests pass" 0 packages "no tests discovered" PASS notes.txt "T30 test requirement"
fi
echo "PASS: colcon workspace build and applicable tests completed; evidence is $OUTDIR/result.json"
write_result PASS 0
