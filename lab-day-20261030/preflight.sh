#!/usr/bin/env bash
set -uo pipefail

failures=0

pass() {
    printf 'PASS %s\n' "$1"
}

warn() {
    printf 'WARN %s\n' "$1"
}

fail() {
    printf 'FAIL %s\n' "$1"
    failures=$((failures + 1))
}

check_file() {
    local path=$1
    local label=$2

    if [[ -f $path ]]; then
        pass "$label exists: $path"
    else
        fail "$label missing: $path"
    fi
}

check_dir() {
    local path=$1
    local label=$2

    if [[ -d $path ]]; then
        pass "$label exists: $path"
    else
        fail "$label missing: $path"
    fi
}

check_sha256() {
    local path=$1
    local expected=$2
    local label=$3
    local missing_hint=${4-}
    local hash_line
    local actual

    if [[ ! -f $path ]]; then
        if [[ -n $missing_hint ]]; then
            fail "$label missing: $path; stage it from the Mac with: $missing_hint"
        else
            fail "$label missing: $path"
        fi
        return
    fi

    hash_line=$(sha256sum -- "$path" 2>&1)
    if [[ $? -ne 0 ]]; then
        fail "$label could not be hashed: $hash_line"
        return
    fi

    actual=${hash_line%% *}
    if [[ $actual == "$expected" ]]; then
        pass "$label SHA-256 matches ($actual)"
    else
        fail "$label SHA-256 mismatch: expected $expected, got $actual"
    fi
}

# Camera enumeration is advisory because the camera may be connected later.
# rs-enumerate-devices ships with ROS Jazzy librealsense and is off PATH until ROS is sourced.
if ! command -v rs-enumerate-devices >/dev/null 2>&1 && [[ -x /opt/ros/jazzy/bin/rs-enumerate-devices ]]; then
    PATH="/opt/ros/jazzy/bin:$PATH"
fi
if ! command -v rs-enumerate-devices >/dev/null 2>&1; then
    warn 'D435/D435i not checked: rs-enumerate-devices is unavailable (camera may be plugged in later)'
else
    camera_output=$(rs-enumerate-devices -s 2>&1)
    camera_status=$?
    expected_serial_seen=0
    expected_usb3_seen=0
    serial_field_seen=0
    device_heading_seen=0
    device_has_expected_serial=0
    device_has_usb3=0

    while IFS= read -r camera_line; do
        if [[ $camera_line =~ ^[[:space:]]*Device[[:space:]]+info: ]]; then
            if (( device_heading_seen && device_has_expected_serial )); then
                expected_serial_seen=1
                if (( device_has_usb3 )); then
                    expected_usb3_seen=1
                fi
            fi
            device_heading_seen=1
            device_has_expected_serial=0
            device_has_usb3=0
        fi
        if [[ $camera_line =~ [Ss]erial[[:space:]_]*[Nn]umber ]]; then
            serial_field_seen=1
        fi
        if [[ $camera_line =~ (^|[^[:digit:]])317422076650([^[:digit:]]|$) ]]; then
            device_has_expected_serial=1
        fi
        if [[ $camera_line =~ [Uu][Ss][Bb].*(3([.][0-9]+)?|[0-9]+000[Mm]) ]]; then
            device_has_usb3=1
        fi
    done <<< "$camera_output"

    if (( device_heading_seen )); then
        if (( device_has_expected_serial )); then
            expected_serial_seen=1
            if (( device_has_usb3 )); then
                expected_usb3_seen=1
            fi
        fi
    else
        if [[ $camera_output =~ (^|[^[:digit:]])317422076650([^[:digit:]]|$) ]]; then
            expected_serial_seen=1
            if [[ $camera_output =~ [Uu][Ss][Bb].*(3([.][0-9]+)?|[0-9]+000[Mm]) ]]; then
                expected_usb3_seen=1
            fi
        fi
    fi

    if (( expected_serial_seen )); then
        if (( camera_status == 0 && expected_usb3_seen )); then
            pass 'D435/D435i serial 317422076650 enumerated on USB 3.x'
        elif (( camera_status != 0 )); then
            fail "D435/D435i serial 317422076650 found, but rs-enumerate-devices -s exited $camera_status"
        else
            fail 'D435/D435i serial 317422076650 found, but USB 3.x was not reported'
        fi
    elif (( serial_field_seen )); then
        fail 'A RealSense device is enumerated, but expected serial 317422076650 was not found'
    else
        warn 'D435/D435i not enumerated (camera may be plugged in later)'
    fi
fi

throttle_output=$(vcgencmd get_throttled 2>&1)
throttle_status=$?
throttle_output=${throttle_output//$'\r'/}
if (( throttle_status == 0 )) && [[ $throttle_output == 'throttled=0x0' ]]; then
    pass 'vcgencmd get_throttled reports throttled=0x0'
else
    fail "vcgencmd get_throttled expected throttled=0x0; got: $throttle_output"
fi

df_output=$(df -Pk "$HOME" 2>&1)
df_status=$?
if (( df_status != 0 )); then
    fail "could not read free space for $HOME: $df_output"
else
    df_last_line=${df_output##*$'\n'}
    read -r _ _ _ df_available _ <<< "$df_last_line"
    if [[ ${df_available-} =~ ^[0-9]+$ ]]; then
        if (( df_available < 10485760 )); then
            fail "free space in $HOME is below 10 GiB ($df_available KiB available)"
        elif (( df_available < 20971520 )); then
            warn "free space in $HOME is below 20 GiB ($df_available KiB available)"
        else
            pass "free space in $HOME is at least 20 GiB ($df_available KiB available)"
        fi
    else
        fail "could not parse df output for $HOME: $df_output"
    fi
fi

check_file /opt/ros/jazzy/setup.bash 'ROS 2 Jazzy setup'
check_file /home/richard/wbr-camera-ros-build-20261021-04/install/setup.bash 'camera ROS install setup'
check_file /home/richard/wbr-demo-ws-20261025/install/setup.bash 'planner workspace setup'
check_dir /home/richard/wbr-demo-ws-20261025/install/wbr_planner_node 'planner install package directory'
check_file /home/richard/orbslam3/ORB_SLAM3/Vocabulary/ORBvoc.txt 'ORB-SLAM3 vocabulary'
check_file /home/richard/wbr-evidence/mobile-demo-20261024-01/setup/rgbd-ros-15fps.yaml 'RGB-D 15 FPS settings'
check_file /home/richard/wbr-evidence/camera-day-20261021-01/mcap-marked-loop-01/capture_loop.py 'camera capture runner'
check_file /home/richard/wbr-pi-camera-day-20261021/scripts/camera_day/record.sh 'camera bag recorder'
check_file "$HOME/wbr-demo-20261026/lab-day-20261026/live_chain.sh" 'LIVE chain runner'
check_file "$HOME/wbr-demo-20261026/lab-day-20261025/path_live.sh" 'P1 path runner'
check_file "$HOME/imu-can-bench/flash.sh" 'flash script'
check_file "$HOME/imu-can-bench/flash_safe.py" 'read-only flash script'
check_file "$HOME/imu-can-bench/stm32boot.py" 'STM32 bootloader utility'
check_file "$HOME/imu-can-bench/restore_canfix01.sh" 'canfix01 restore script'

check_sha256 \
    "$HOME/imu-can-bench/link_bench_f446.bin" \
    bf5721b44c0d9eafa4b5b53fb75f1ceec8c6e3c72a0c81d5a6bfd7635fe003ed \
    'link-bench firmware image' \
    'scp tools/link_bench/firmware/prebuilt/link_bench_f446.bin wbr-pi5:~/imu-can-bench/link_bench_f446.bin'
check_sha256 \
    "$HOME/course-stage/fw/wbr-agv_f446_home_canfix01.bin" \
    f614cde00541a15f80873a72981618dfc65e3f923a1d9309e1fb732831ecf296 \
    'canfix01 firmware image'

uart_device=/dev/ttyAMA0
if [[ ! -e $uart_device ]]; then
    fail "$uart_device does not exist"
elif [[ ! -c $uart_device ]]; then
    fail "$uart_device exists but is not a character device"
elif command -v fuser >/dev/null 2>&1; then
    uart_pids=$(fuser "$uart_device" 2>/dev/null)
    if [[ -n $uart_pids ]]; then
        uart_holders=''
        for uart_pid in $uart_pids; do
            uart_name=$(ps -p "$uart_pid" -o comm= 2>/dev/null || true)
            if [[ -z $uart_name ]]; then
                uart_name='name unavailable'
            fi
            uart_holders="${uart_holders}${uart_holders:+, }${uart_name} (pid $uart_pid)"
        done
        warn "$uart_device is held by: $uart_holders"
    else
        pass "$uart_device exists and fuser reports no process holding it"
    fi
elif command -v lsof >/dev/null 2>&1; then
    uart_pids=$(lsof -t "$uart_device" 2>/dev/null)
    if [[ -n $uart_pids ]]; then
        uart_holders=''
        for uart_pid in $uart_pids; do
            uart_name=$(ps -p "$uart_pid" -o comm= 2>/dev/null || true)
            if [[ -z $uart_name ]]; then
                uart_name='name unavailable'
            fi
            uart_holders="${uart_holders}${uart_holders:+, }${uart_name} (pid $uart_pid)"
        done
        warn "$uart_device is held by: $uart_holders"
    else
        pass "$uart_device exists and lsof reports no process holding it"
    fi
else
    warn "$uart_device exists, but neither fuser nor lsof is available to check holders"
fi

if command -v pgrep >/dev/null 2>&1; then
    matching_processes=$(pgrep -afi 'ros2|realsense|orb[_-]?slam' 2>/dev/null | grep -v 'ros2cli.daemon' || true)
    if [[ -z $matching_processes ]]; then
        pass 'no ros2, RealSense, or ORB-SLAM processes are running'
    else
        process_holders=''
        while IFS= read -r process_line; do
            process_pid=${process_line%% *}
            process_comm=$(ps -p "$process_pid" -o comm= 2>/dev/null || true)
            if [[ -z $process_comm ]]; then
                process_comm='process name unavailable'
            fi
            process_holders="${process_holders}${process_holders:+, }${process_comm} (pid $process_pid)"
        done <<< "$matching_processes"
        warn "ros2, RealSense, or ORB-SLAM processes found: $process_holders"
    fi
else
    warn 'could not check for leftover ros2, RealSense, or ORB-SLAM processes (pgrep unavailable)'
fi

evidence_dir="$HOME/wbr-evidence/lab-day-20261030"
existing_runs=()
for run_path in \
    "$evidence_dir/M1-lab-map" \
    "$evidence_dir/L1-3m-line" \
    "$evidence_dir/A1-approach" \
    "$evidence_dir"/LIVE-chain-* \
    "$evidence_dir/P1-path-test"; do
    if [[ -d $run_path ]]; then
        existing_runs+=("${run_path##*/}")
    fi
done

if (( ${#existing_runs[@]} == 0 )); then
    pass 'no existing lab-day-20261030 run directories use the runbook names'
else
    existing_run_list=''
    for existing_run in "${existing_runs[@]}"; do
        existing_run_list="${existing_run_list}${existing_run_list:+, }$existing_run"
    done
    warn "existing lab-day-20261030 run directories may collide with runbook names: $existing_run_list"
fi

if (( failures > 0 )); then
    printf 'RESULT: FAIL (%d failed check(s))\n' "$failures"
    exit 1
fi

printf 'RESULT: PASS (no failed checks; review WARN lines)\n'
