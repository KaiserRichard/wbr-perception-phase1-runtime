date -u --iso-8601=seconds
id
source /opt/ros/jazzy/setup.bash
timeout --signal=INT --kill-after=5s 30s /opt/ros/jazzy/bin/rs-enumerate-devices
rc=$?
printf '\nENUMERATION_RETURN_CODE=%s\n' "$rc"
date -u --iso-8601=seconds
exit "$rc"
