#!/bin/bash
# Diagnostic (OPEN) D435i recording with 1 Hz power log and kernel log. Usage: smoke.sh NAME SECONDS
B=$HOME/wbr-runtime/n4b-20261013T080913Z
R=$HOME/wbr-evidence/2026-10-14-d435i-$1; mkdir -p $R
(while true; do echo "$(date -u +%FT%TZ) $(vcgencmd get_throttled) $(vcgencmd pmic_read_adc EXT5V_V | awk '{print $2}') $(vcgencmd measure_temp) $(vcgencmd measure_clock arm)"; sleep 1; done) > $R/power-1hz.log & P=$!
journalctl -k -f -n0 -o short-iso-precise > $R/kernel.log 2>&1 & K=$!
sleep 2
$B/bin/d435i_record $R/take $2 > $R/record.log 2>&1; echo "rc=$?" >> $R/record.log
sleep 2; kill $P $K
python3 $B/bin/analyze_take.py $R/take/timestamps.csv > $R/analysis.json 2>&1
du -B1 $R/take/* > $R/sizes.txt
echo DONE
