date -u --iso-8601=seconds
printf 'HELPER AT PATH REFERENCED BY INSTALLED UDEV RULE (READ ONLY)\n'
ls -l /usr/local/libexec/wbr-d435i-iio-permissions
sha256sum /usr/local/libexec/wbr-d435i-iio-permissions
printf '\nNONINTERACTIVE SUDO AVAILABILITY (NO MUTATION)\n'
sudo -n true
printf 'sudo_noninteractive_exit=%s\n' "$?"
