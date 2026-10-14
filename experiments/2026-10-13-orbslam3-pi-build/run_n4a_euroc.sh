#!/bin/bash
# N4A: upstream ORB-SLAM3 stereo-inertial on EuRoC MH01, headless (upstream example already passes viewer=false), 3 runs.
set -uo pipefail
O=$HOME/orbslam3/ORB_SLAM3; D=$HOME/datasets/euroc/MH01
EV=$HOME/wbr-evidence/2026-10-13-n4a-euroc-mh01; mkdir -p "$EV"
pgrep -f wbr-power-logger.sh >/dev/null || nohup $HOME/wbr-evidence/2026-10-13-orbslam3-build/wbr-power-logger.sh >> "$EV/power.log" 2>&1 < /dev/null &
{ uname -a; (cd $O && git log --oneline | head -3); sha256sum $O/lib/libORB_SLAM3.so $O/Examples/Stereo-Inertial/stereo_inertial_euroc $O/Examples/Stereo-Inertial/EuRoC.yaml $O/Examples/Stereo-Inertial/EuRoC_TimeStamps/MH01.txt; } > "$EV/provenance.txt" 2>&1
for r in 1 2 3; do
  R=$EV/run$r; mkdir -p $R; cd $R
  echo "run$r start $(date -u +%FT%TZ) $(vcgencmd get_throttled)" | tee -a "$EV/runs.log"
  /usr/bin/time -v $O/Examples/Stereo-Inertial/stereo_inertial_euroc $O/Vocabulary/ORBvoc.txt $O/Examples/Stereo-Inertial/EuRoC.yaml \
     $D $O/Examples/Stereo-Inertial/EuRoC_TimeStamps/MH01.txt mh01_stereoi > stdout.log 2> stderr.log
  echo "run$r end $(date -u +%FT%TZ) rc=$? $(vcgencmd get_throttled)" | tee -a "$EV/runs.log"
done
echo ALLDONE >> "$EV/runs.log"
