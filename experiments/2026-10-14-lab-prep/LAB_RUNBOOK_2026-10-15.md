# 15 October lab: record → replay → plot → live

**Diagnostic demo: OPEN.** Successful 100-second RAM capture and post-patch replay are **unverified**. Under-voltage remains unresolved; use the adequate supply if available. Calibration geometry is nominal, IMU noise assumed and camera–IMU time offset unknown.

## One-page checklist

- [ ] **Set up:** card in the **8 GB Pi**; camera directly in a **blue USB3 port**; Pi, power lead and connectors fixed, camera free to move with cable slack. Use “M625 Mechatronic Lab” Wi-Fi or secure the loose Ethernet cable with tape. Aim at a well-lit, textured, static scene.
- [ ] **Find the Pi:** Mac `ssh wbr-pi5-wifi`, or `ssh -o Hostname=192.168.50.2 wbr-pi5-wifi` with Ethernet. Wi-Fi on the 8 GB Pi is **unverified**. If the address changed, match the saved host key; the observed `192.168.0.127` host was another Pi. Do not replace a mismatched key.
- [ ] **Check the entry conditions:** owner says **`CAMERA AVAILABLE`** before any camera or ORB execution. Follow fresh-unit **N1 → N2 → N3**; the 100-second demo does not replace these gates. N1 requires USB **≥5000M**. N2 stays **IR1 Y8 640×480/15, gyro/200, accel/100**, staged **20 → 105 → 300 seconds**, with the mandatory soak and unchanged timing/health criteria in `n4b_plan.md`. Review N3 record/replay evidence. Gates remain OPEN until evidenced.
- [ ] **Rebuild:** resume patch 4 with `cmake --build build -j4` in `~/orbslam3/ORB_SLAM3`. Keep the build log; stop on failure. Check the installed example resolves the rebuilt library.
- [ ] **Record 100 seconds into RAM:** only the recorder owns the camera. Begin smooth translation in **1–2 seconds**; for **20–30 seconds**, move **10–30 cm** along all axes with gentle **±15–30°** roll/pitch/yaw. Continue a small loop, revisit the starting view, finish **5–10 seconds still**. Keep the Pi and connectors stationary. Emitter OFF; stereo **640×480 Y8/30**, gyro **200**, accel **100 Hz**.
- [ ] **Review → replay → plot:** confirm `rc=0`, checksum `OK`, both infrared (IR) streams, expected rates, ordered/common-domain stamps and no unexplained gaps. Audit beginning/end exclusions too. Run `--bag ... --no-viewer` in a fresh folder. Expect initialization, sustained tracking state **2**, one stable map and nonempty trajectories. Inspect resets and counters even if the plot looks plausible.
- [ ] **Live only after offline review:** same binary/settings, omit `--bag`, keep `--no-viewer`; use the motion recipe and retain power/kernel logs. Stop normally and check finalization. Copy evidence to the Mac immediately; card staging is not qualified dataset storage. A room plot has **no ground truth**, so accuracy remains **unverified**.

| If this fails | Do this next |
|---|---|
| `Not enough motion ... Reseting` | Inspect early keyframe spacing; repeat with gentle **translation**, varied speed and rotation. This warning can occur after initial IMU initialization. |
| Repeated `Creation of new map` | Inspect the event before each **new map ID**. One startup map is normal; two creation messages can describe one map. |
| `Fail to track local map!` | Inspect a retained stereo pair for blur, texture, pairing and row alignment; then check timing/calibration. Image quality is **unverified** if no pair was retained. |
| No IMU initialization / empty IMU queue | Audit gyro/accel counts, gaps, domains and bracketing; then geometry/noise and early motion. |
| Older/backward timestamp | Check order, clock domains and units. Preserve the records; do not sort them to conceal reversals. |

<details>
<summary><strong>Exact command cards — expand at the bench</strong></summary>

These are **future commands**, not executed for this ticket. Mac commands control/transfer; acquisition and processing run locally on the Pi. Stop on command failure. Existing binaries are in `~/wbr-runtime/n4b-20261013T080913Z/bin/`; never replace a checkout or historical take.

### Mac: connect and stage checksummed helpers

Use a Mac Bash terminal. `WBR_ID` must be unique; keep the printed value for the Pi terminal. For Ethernet or a discovered address, set `WBR_SSH_OPTIONS=(-o Hostname=ADDRESS)` before connection/transfer; leave it empty when the alias works.

```bash
WBR_REPO="$HOME/Desktop/Research/wbr-perception-phase1-runtime"
WBR_HOST=wbr-pi5-wifi
WBR_SSH_OPTIONS=()  # Or: (-o Hostname=192.168.50.2) for Ethernet.
ssh "${WBR_SSH_OPTIONS[@]}" "$WBR_HOST"
# Exit the remote shell before the Mac staging commands below.
WBR_ID="lab-$(date -u +%Y%m%dT%H%M%SZ)"
WBR_STAGE="$WBR_REPO/experiments/2026-10-14-lab-prep/$WBR_ID"
mkdir "$WBR_STAGE"
cp "$WBR_REPO/experiments/2026-10-13-n4b-d435i-prep/"{smoke_ram.sh,analyze_take.py} "$WBR_STAGE/"
(cd "$WBR_STAGE" && shasum -a 256 smoke_ram.sh analyze_take.py > SHA256SUMS)
scp "${WBR_SSH_OPTIONS[@]}" -r "$WBR_STAGE" "$WBR_HOST:wbr-runtime/"
printf 'Pi terminal: export WBR_ID=%s\n' "$WBR_ID"
```

**Only if Wi-Fi discovery is needed:** confirm the Mac's current LAN first (`ifconfig`). The previously observed lab subnet was `192.168.0.*`; today's subnet is **unverified**. This scans SSH host keys without logging into candidates. It requires an existing saved Ed25519 key for alias `192.168.50.2`; if absent, identify the Pi locally instead. A scan is discovery, not a reason to accept a new key.

```bash
WBR_SUBNET=192.168.0   # Set to the verified current lab subnet.
WBR_KEYFILE="$WBR_REPO/experiments/2026-10-14-lab-prep/known-pi-key.txt"
ssh-keygen -F 192.168.50.2 | awk '$2=="ssh-ed25519" {print $2, $3}' > "$WBR_KEYFILE"
test -s "$WBR_KEYFILE" && for WBR_N in {1..254}; do
  WBR_IP="$WBR_SUBNET.$WBR_N"
  if ssh-keyscan -T 1 -t ed25519 "$WBR_IP" 2>/dev/null |
     awk '{print $2, $3}' | rg -F -x -q -f "$WBR_KEYFILE"; then
    printf 'Matching Pi: %s\n' "$WBR_IP"
  fi
done
# Substitute the matching address, preserving the alias's user/key settings:
# WBR_SSH_OPTIONS=(-o Hostname=MATCHING_ADDRESS -o HostKeyAlias=192.168.50.2)
# ssh "${WBR_SSH_OPTIONS[@]}" "$WBR_HOST"
# Keep those options for the subsequent scp commands.
```

### Pi: initialize this session and resume the library build

Use a local Pi Bash terminal, or SSH strictly as control. Paste the `export WBR_ID=...` line printed by the Mac first. Do not invent a different session name.

```bash
set -euo pipefail
: "${WBR_ID:?Paste the session ID from the Mac first}"
export WBR_HELPERS="$HOME/wbr-runtime/$WBR_ID"
WBR_BIN="$HOME/wbr-runtime/n4b-20261013T080913Z/bin"
WBR_ORB="$HOME/orbslam3/ORB_SLAM3"
WBR_YAML="$HOME/wbr-runtime/n4b-prep-20261013/D435i_317422076650_stereo_inertial.yaml"
WBR_SESSION="$HOME/wbr-evidence/$WBR_ID"
mkdir "$WBR_SESSION"
(cd "$WBR_HELPERS" && sha256sum -c SHA256SUMS)
cd "$WBR_ORB"
rg -n 'mpCurrentKeyFrame.*nullptr' include/LocalMapping.h
cmake --build build -j4 2>&1 | tee "$WBR_SESSION/rebuild.log"
export LD_LIBRARY_PATH="$WBR_ORB/lib:$WBR_ORB/Thirdparty/DBoW2/lib:$WBR_ORB/Thirdparty/g2o/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
ldd "$WBR_BIN/stereo_inertial_realsense_D435i" | tee "$WBR_SESSION/ldd.txt"
sha256sum "$WBR_ORB/lib/libORB_SLAM3.so" "$WBR_BIN/d435i_record" \
  "$WBR_BIN/stereo_inertial_realsense_D435i" "$WBR_YAML" \
  "$WBR_ORB/Vocabulary/ORBvoc.txt" > "$WBR_SESSION/runtime.sha256"
```

Check each result before continuing: initializer present, build exit zero, no missing libraries, `libORB_SLAM3.so` resolved from the intended native tree. Patch 4 was already applied to the Pi build copy; do not reapply it or rebuild/reset either canonical checkout.

### Pi: capture and review

The supplied `smoke_ram.sh` uses a fixed runtime path for its analyzer. Rebase **only that analyzer call** in a separate derived helper so the newly checksummed Mac copy is used; retain the original. Its historical evidence-directory prefix remains `2026-10-14-d435i-`; the unique session name carries the actual date.

```bash
sed 's|python3 $B/bin/analyze_take.py|python3 "$WBR_HELPERS/analyze_take.py"|' \
  "$WBR_HELPERS/smoke_ram.sh" > "$WBR_HELPERS/smoke_ram-local.sh"
sha256sum "$WBR_HELPERS/smoke_ram-local.sh" > "$WBR_SESSION/capture-helper.sha256"
df -h /dev/shm "$HOME/wbr-evidence"
free -h
lsusb -t
vcgencmd get_throttled
test ! -e "/dev/shm/wbr-take-$WBR_ID"
test ! -e "$HOME/wbr-evidence/2026-10-14-d435i-$WBR_ID"
bash "$WBR_HELPERS/smoke_ram-local.sh" "$WBR_ID" 100
WBR_CAPTURE="$HOME/wbr-evidence/2026-10-14-d435i-$WBR_ID"
WBR_TAKE="$WBR_CAPTURE/take"
cat "$WBR_CAPTURE/record.log" "$WBR_CAPTURE/analysis.json"
python3 "$WBR_HELPERS/analyze_take.py" "$WBR_TAKE/timestamps.csv"
(cd "$WBR_TAKE" && sha256sum -c ../ram-sha256.txt)
WBR_BAG="$WBR_TAKE/stereo_imu.db3"
test -s "$WBR_BAG"
```

Ensure RAM, available system memory and card free space can hold the take plus overhead before starting. The addendum reports about **1.7 GB** for 100 seconds and **3.9 GB** `/dev/shm` capacity on the 8 GB Pi; recheck today's state. This size is a budget, not a guarantee. Do not put a 300-second stereo soak into this RAM allocation. The helper copies after capture and removes the RAM take only after checksum success. `DONE` alone is not success: inspect recorder `rc`, all checksum results, `kernel.log` and `power-1hz.log`. The script does not enforce the gate health criteria.

If `stereo_imu.db3` is absent, inspect the retained take and recorder log; do not rename an unknown file. The old plan says `.bag`, but the later session facts identify `.db3` for this installed recorder.

### Pi: offline run, then live run after review

Run each block separately. Keep failures and start a fresh session/run directory for another attempt. Initialization should be visible in this patched example and its `*_tracking.csv`; sustained state 2 and one map are observations, not accuracy validation. The exporter can retain only the largest map.

```bash
WBR_OFFLINE="$WBR_SESSION/offline"
mkdir "$WBR_OFFLINE" && cd "$WBR_OFFLINE"
sha256sum "$WBR_BAG" "$WBR_YAML" > inputs.sha256
if /usr/bin/time -v "$WBR_BIN/stereo_inertial_realsense_D435i" \
  "$WBR_ORB/Vocabulary/ORBvoc.txt" "$WBR_YAML" n4b \
  --bag "$WBR_BAG" --no-viewer > run.log 2>&1; then
  WBR_RC=0
else WBR_RC=$?
fi
printf '%s\n' "$WBR_RC" > exit-status.txt
test "$WBR_RC" -eq 0
rg -n 'IMU initialized|maps in the atlas|Creation of new map|Not enough motion|LOST|lost|reset|Reseting|OPEN:' run.log
cp "$WBR_TAKE/timestamps.csv" "$WBR_CAPTURE/power-1hz.log" .
# Pause here: review input, tracking, map IDs, queues and the Mac plot.
```

Review gaps/order/domains in the acquisition audit; review actual IMU interpolation/bracketing separately in the driver audit. Recorder SDK stamps are milliseconds, ORB inputs seconds and EuRoC-format trajectory exports nanoseconds. Offline wall duration is not a live throughput measurement.

```bash
WBR_LIVE="$WBR_SESSION/live"
mkdir "$WBR_LIVE" && cd "$WBR_LIVE"
(while true; do
  printf '%s %s %s\n' "$(date -u +%FT%TZ)" "$(vcgencmd get_throttled)" "$(vcgencmd measure_temp)"
  sleep 1
done) > power-1hz.log & WBR_POWER_PID=$!
journalctl -k -f -n0 -o short-iso-precise > kernel.log 2>&1 & WBR_KERNEL_PID=$!
if timeout --signal=INT --kill-after=30s 90s \
  "$WBR_BIN/stereo_inertial_realsense_D435i" \
  "$WBR_ORB/Vocabulary/ORBvoc.txt" "$WBR_YAML" n4c \
  --no-viewer > run.log 2>&1; then
  WBR_RC=0
else WBR_RC=$?
fi
printf '%s\n' "$WBR_RC" > exit-status.txt
kill "$WBR_POWER_PID" "$WBR_KERNEL_PID"
rg -n 'IMU initialized|maps in the atlas|Creation of new map|Not enough motion|LOST|lost|reset|Reseting|OPEN:' run.log
```

Live timeout **124** is expected only with reviewed normal shutdown/finalized outputs. Forced kill or missing finalization is a failed attempt. Inspect live health and driver counters/backlog; preserve calibration warnings. Recorder and live SLAM must never run concurrently.

### Mac: copy, verify and plot before authorizing live progression

Run this after offline execution; repeat transfer into a **new** local destination after live execution. Plotting expects exactly one `f_*.txt` and its optional matching `kf_*.txt` in each run folder. Use already-installed dependencies; if missing, retain outputs and mark plotting unavailable.

```bash
WBR_LOCAL="$WBR_REPO/experiments/2026-10-14-lab-prep/evidence-$WBR_ID"
mkdir "$WBR_LOCAL"
scp "${WBR_SSH_OPTIONS[@]}" -r "$WBR_HOST:wbr-evidence/$WBR_ID" "$WBR_LOCAL/"
scp "${WBR_SSH_OPTIONS[@]}" -r "$WBR_HOST:wbr-evidence/2026-10-14-d435i-$WBR_ID" "$WBR_LOCAL/"
(cd "$WBR_LOCAL/2026-10-14-d435i-$WBR_ID/take" && shasum -a 256 -c ../ram-sha256.txt)
MPLCONFIGDIR="$WBR_LOCAL/.mplconfig" XDG_CACHE_HOME="$WBR_LOCAL/.cache" \
  python3 "$WBR_REPO/experiments/2026-10-14-d435i-demo/plot_run.py" \
  "$WBR_LOCAL/$WBR_ID/offline"
open "$WBR_LOCAL/$WBR_ID/offline/demo_plot.png"
```

Do not use `--gt` for the room take: no reference exists. `demo_stats.json` describes exported motion; its pose rate is not processing speed. For live results, use a new `WBR_LOCAL`, repeat the two transfers and checksum check, then substitute `/live` for `/offline` in the plot/open commands. Keep the Pi staging copy until the Mac copy is verified; this checklist performs no deletion.

</details>

Sources: [14 October addendum](../2026-10-14-SESSION_FACTS_ADDENDUM.md), [13 October facts](../2026-10-13-SESSION_FACTS_FOR_SLIDES.md), [n4b_plan](../2026-10-13-n4b-d435i-prep/n4b_plan.md), `smoke_ram.sh`, `analyze_take.py`, `plot_run.py` and [DEBUG_GUIDE](../2026-10-14-d435i-demo/DEBUG_GUIDE.md). Paths come from the ticket. Command cards adapt the existing procedures for unique directories, checksummed helper copies and the later `.db3`/RAM facts; only the analyzer path is rebased. Validation here is camera-free document/shell-syntax review, not Pi execution. No gate is promoted.
