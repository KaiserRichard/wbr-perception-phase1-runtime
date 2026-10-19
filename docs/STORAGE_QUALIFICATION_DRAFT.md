# DRAFT: 128 GB card recording-destination qualification

**DRAFT — requires owner review before execution. UNTESTED ON HARDWARE.**
This is a procedure proposal, not an executable benchmark tool or a qualification
result. The owner must review the exact benchmark implementation, destination,
duration, size, reserve and fsync cadence before execution.

Source: [D435I_CALIBRATION_PLAN.md](D435I_CALIBRATION_PLAN.md), prerequisites/storage
(line 160), and [session addendum](../experiments/2026-10-14-SESSION_FACTS_ADDENDUM.md)
item 3. The 18.4 MB/s decimal stream budget exceeds the historical 16.6 MB/s
achieved rate. Target **at least 27.6 MB/s** sustained including fsync, calculated
as 1.5 x 18.4. Payload, serialization and OS contention still need take audits.

1. Identify the actual 128 GB card's mounted recording filesystem and dedicated
   data directory, separate from OS/build paths. Record card identity, mount,
   filesystem/options, power/cooling, free bytes and intended largest take size
   and duration. Never use a raw device, format a filesystem, overwrite any
   existing file, or place the benchmark on a different volume.
2. Select a fresh dedicated benchmark directory on that filesystem and a new
   regular file, created exclusively (fail if it exists; refuse symlinks). Keep
   existing data untouched. Confirm no camera or recorder owns the destination.
3. Precheck free space: at least the entire planned benchmark size **plus an
   explicitly reviewed OS reserve**, and retain the plan's free-space requirement
   of at least twice the largest planned take plus that reserve. Plan enough
   benchmark space for both size and duration constraints at plausible write
   speeds; if capacity cannot cover them, stop for review. No disk-fill tests.
4. Write sequential, non-sparse, non-compressible blocks into that file. Use a
   monotonic timer starting before the first write. Perform fsync periodically
   (PROPOSED: after each 1 MiB block) and a final fsync before stopping the timer;
   record actual bytes, elapsed time, fsync cadence, errors and interval rates.
   Buffered or cached writes without fsync are insufficient. Do not claim fsync
   proves power-loss durability of the card controller.
5. Continue until **both** written bytes exceed the largest planned take
   (including estimated metadata overhead) **and** elapsed time is at least its
   duration. For a 120 s / 3.0 GB reserved take, that means >3.0 GB and >=120 s;
   at 27.6 MB/s the duration alone writes >=3.312 GB. Longer planned takes require
   correspondingly longer/larger tests. Monitor remaining space against the OS
   reserve; stop on low space, write/fsync error, power or thermal problem and
   label the run incomplete/failed, never qualified.
6. Review total bytes / elapsed seconds and interval rates including all fsync
   time. PROPOSED acceptance: overall and every complete 10 s interval >=27,600,000
   B/s, both size/duration constraints met, no errors or interrupted execution.
   Retain raw logs and environment observations, including failures. A pass
   applies only to this destination and observed conditions; subsequent bag
   audits must still establish delivery without drops.
7. After review, use the destination's measured sustained rate (conservatively
   the lowest accepted interval rate) in a separate reviewed destination-specific
   bag config's `storage.max_write_rate_bps`. The proposed profile deliberately
   retains 16,600,000 until that evidence exists; do not silently promote it.
8. Close the test file, preserve benchmark logs outside the payload file, verify
   the exact test pathname belongs to this new dedicated directory, then remove
   only that new benchmark file and empty benchmark directory. Never use a
   wildcard or recursive cleanup of a shared data directory. Record restored
   free space. Preserve existing takes; copy and verify take checksums before
   any separately authorized take deletion.

Owner review and real destination measurements are pending. Full-rate recording
remains gated on qualification; this draft does not authorize its execution.
