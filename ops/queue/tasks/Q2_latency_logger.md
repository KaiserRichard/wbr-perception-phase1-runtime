# Q2 — latency, queue and resource observer (component C7), dir: tools/runtime_observer/
Read queue/tasks/COMMON_QUEUE.md first. Build:
1. A tiny C++17 header-only event recorder (lock-free or mutex-bounded ring buffer, no allocation in the hot path) that
   stamps events with CLOCK_MONOTONIC ns (host_steady domain) plus optional source epoch with its domain: frame_received,
   queued, track_start, track_end, snapshot_published, dropped(reason), queue_depth. Binary or CSV dump at exit.
2. Python aggregator: per-stage durations and ages P50/P95/P99/max, queue depth stats/slope, drop counts by reason,
   throughput; cross-domain ages only if a clockmap (tools/clockmap) mapping is supplied, else UNAVAILABLE.
3. Python resource sampler for the Pi (psutil-free: /proc/stat, /proc/<pid>/status, /sys/class/thermal, cpufreq,
   `vcgencmd get_throttled` if present) writing 1 Hz CSV; on macOS it must degrade gracefully (fields UNAVAILABLE) and tests
   use fake /proc fixtures.
4. A parser for the timing lines that the existing patch (stereo_inertial_d435i_file.patch) prints, to reuse its numbers.
Tests with synthetic event streams (known delays, drops, backlog growth) and fake sysfs. Makefile or unittest.
