#!/usr/bin/env python3
"""Read the Pi's apt cache without downloading or installing dependencies."""
import json
from datetime import datetime, timezone

import apt
import apt_pkg

apt_pkg.config.set("APT::Install-Recommends", "false")
apt_pkg.config.set("APT::Install-Suggests", "false")
packages = [
    "ros-jazzy-librealsense2",
    "ros-jazzy-realsense2-camera",
    "ros-jazzy-realsense2-description",
]
result = {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
          "install_recommends": False, "cases": {}}
for requested in [[p] for p in packages] + [packages[:2], packages]:
    cache = apt.Cache()
    for name in requested:
        cache[name].mark_install(auto_fix=True, auto_inst=True, from_user=True)
    changes = sorted(cache.get_changes(), key=lambda p: p.name)
    result["cases"][" + ".join(requested)] = {
        "requested": requested,
        "download_bytes": cache.required_download,
        "installed_size_delta_bytes": cache.required_space,
        "new_packages": sum(p.marked_install and not p.is_installed for p in changes),
        "upgrades": sum(p.is_installed and p.marked_upgrade for p in changes),
        "removals": sum(p.marked_delete for p in changes),
        "changes": [{"package": p.name,
                     "installed": p.installed.version if p.installed else None,
                     "candidate": p.candidate.version if p.candidate else None,
                     "download_bytes": p.candidate.size if p.candidate else None,
                     "installed_bytes": p.candidate.installed_size if p.candidate else None,
                     "remove": p.marked_delete} for p in changes],
    }
print(json.dumps(result, indent=2))
