date --iso-8601=seconds
printf '\nCURRENT USB ENUMERATION\n'
lsusb
lsusb -t
printf '\nD435I SYSFS FIELDS\n'
for d in /sys/bus/usb/devices/*; do
    [ -f "$d/idVendor" ] || continue
    [ "$(cat "$d/idVendor")" = 8086 ] || continue
    [ "$(cat "$d/idProduct")" = 0b3a ] || continue
    printf 'SYSFS_PATH=%s\nREAL_PATH=%s\n' "$d" "$(readlink -f "$d")"
    for f in busnum devnum devpath idVendor idProduct product serial speed bcdDevice; do
        printf '%s=' "$f"
        cat "$d/$f"
    done
done
printf '\nSTORAGE\n'
lsblk -o NAME,MODEL,SIZE,FSTYPE,LABEL,MOUNTPOINTS,TRAN
findmnt /mnt/wbr-data
findmnt -T /mnt/wbr-data -o TARGET,SOURCE,FSTYPE,UUID,OPTIONS
df -hT /mnt/wbr-data
printf '\nUTC END\n'
date -u --iso-8601=seconds
