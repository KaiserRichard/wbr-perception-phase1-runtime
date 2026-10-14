#!/bin/bash
# Diagnostic (OPEN) D435i recording into RAM (/dev/shm), copied to the card afterwards. Usage: smoke_ram.sh NAME SECONDS
B=$HOME/wbr-runtime/n4b-20261013T080913Z
R=$HOME/wbr-evidence/2026-10-14-d435i-$1; mkdir -p $R
S=/dev/shm/wbr-take-$1
(while true; do echo "$(date -u +%FT%TZ) $(vcgencmd get_throttled) $(vcgencmd pmic_read_adc EXT5V_V | awk '{print $2}') $(vcgencmd measure_temp) $(vcgencmd measure_clock arm)"; sleep 1; done) > $R/power-1hz.log & P=$!
journalctl -k -f -n0 -o short-iso-precise > $R/kernel.log 2>&1 & K=$!
sleep 1
$B/bin/d435i_record $S $2 > $R/record.log 2>&1; echo "rc=$?" >> $R/record.log
kill $P $K
python3 $B/bin/analyze_take.py $S/timestamps.csv > $R/analysis.json 2>&1
T0=$(date +%s); cp -a $S $R/take && sync; echo "copy_to_card_s=$(( $(date +%s)-T0 ))" >> $R/record.log
(cd $S && sha256sum *) > $R/ram-sha256.txt; (cd $R/take && sha256sum -c ../ram-sha256.txt) >> $R/record.log 2>&1 && rm -rf $S
du -B1 $R/take/* > $R/sizes.txt
echo DONE
