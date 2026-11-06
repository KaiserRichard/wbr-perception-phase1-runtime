# LIVE chain rehearsal without camera or Nucleo (30 Oct 2026, ~01:20)

**What it tests:** the exact LIVE software path on the Pi, i.e. `tools/link_bench/pi/advisory_link.py --ros`
from the lab checkout `~/wbr-demo-20261026`, which is byte-identical to main for advisory_link.py,
bench.c, sim.c, link_proto.c, decide.py and detect.py. The D435i is replaced by a recorded 24 Oct
RGB-D bag, and the Nucleo by `tools/link_bench/host/sim.c`: the firmware's `bench.c` behind a
pseudo-terminal. It **does not** test the real UART, the wiring, the LEDs, the camera driver or timing on the F446.

## Result (MEASURED, Pi 5, 20 s per bag, `--max-forward 3.0`)

| Bag (24 Oct) | Frames / dropped | Advisories | Confirmed median height | Median distance | Detection P50 / P95 | Receipt→send P50 / P95 | Echo rejects |
|---|---|---|---|---|---|---|---|
| B-H13 (13 cm box) | 220 / 72 | STOP 218, UNCERTAIN 2 | 0.131 m | 0.989 m | 69 / 76 ms | 100 / 130 ms | 0 |
| B-H05 (5 cm box) | 219 / 73 | JUMP 217, UNCERTAIN 2 | 0.044 m | 0.987 m | 69 / 80 ms | 100 / 132 ms | 0 |
| S1-empty (lamp pole) | 202 / 66 | STOP 200, UNCERTAIN 2 | 0.632 m | 1.439 m | 68 / 84 ms | 103 / 137 ms | 0 |

Simulated Nucleo final counters: accepted 641, rejected 0, wire errors 0, TX dropped 0, stale 1 (at the end of a run).
The 2 UNCERTAIN at the start of each bag are the 3-of-5 confirmation. The pseudo-terminal round-trip time (0.19 ms) says nothing about the real 460800-baud UART.
About one frame in three is dropped (detection ~70 ms at 15 Hz input); this is the same order as the 24 Oct live runs.
Raw outputs and plots: `~/wbr-evidence-archive/overnight-20261030-01/live-rehearsal/` (Mac).

## Re-run

```bash
ssh wbr-pi5 'bash -s' <<'EOF'
R=~/wbr-demo-20261026; T=/tmp/wbr-rehearsal; rm -rf $T; mkdir -p $T
cc -std=c99 -O2 -I$R/tools/link_bench/firmware -I$R/tools/link_proto $R/tools/link_bench/host/sim.c \
   $R/tools/link_bench/firmware/bench.c $R/tools/link_proto/link_proto.c -o $T/sim
source /opt/ros/jazzy/setup.bash; export ROS_DOMAIN_ID=78 ROS_LOCALHOST_ONLY=1
$T/sim $T/sim-final.txt > $T/sim.out 2>&1 & S=$!; sleep 1; PTY=$(head -1 $T/sim.out)
BAG=~/wbr-evidence/mobile-demo-20261024-01/B-H13/rgbd-bag
timeout 40 ros2 bag play $BAG --loop --topics /camera/camera/aligned_depth_to_color/image_raw \
  /camera/camera/aligned_depth_to_color/camera_info /camera/camera/color/camera_info >/dev/null 2>&1 &
sleep 2; (cd $R && python3 tools/link_bench/pi/advisory_link.py --port "$PTY" --out $T/B-H13 --ros --duration 20)
kill -TERM $S; cat $T/sim-final.txt
EOF
```

Summarize on the Mac: `summarize_live.py` imports matplotlib, which the Pi's system Python does not have.
Copy the run directory back with scp, then run
`~/Desktop/Research/wbr-venvs/perception/bin/python tools/link_bench/pi/summarize_live.py <dir>...`.
