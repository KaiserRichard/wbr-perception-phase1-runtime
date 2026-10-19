---
name: wbr-evidence-copy
description: Copy a lab evidence folder from the Pi to the Mac (or between disks) with a SHA-256 manifest and verification. Use after every lab run and before anything is deleted.
---

# Evidence copy with checksums

Read `ops/lab-assistant/INSTRUCTIONS.md` first. Copy whole run folders, including
failed runs. The source is kept; deleting it is a separate decision.

## Step 1 [PI] Make a manifest next to the run folder
Replace `RUN` with the folder name under `~/wbr-evidence/`. The manifest is written
beside the folder, so the run folder itself is not modified.
```sh
cd ~/wbr-evidence && ls -d RUN && test ! -e RUN.sha256
find RUN -type f -print0 | sort -z | xargs -0 sha256sum > RUN.sha256 && wc -l RUN.sha256
```
If `RUN.sha256` already exists, stop: use a new name like `RUN.sha256-02`.

## Step 2 [MAC] Copy (read-only for the Pi)
```sh
mkdir -p ~/wbr-evidence-archive
rsync -av wbr-pi5:wbr-evidence/RUN wbr-pi5:wbr-evidence/RUN.sha256 ~/wbr-evidence-archive/
```
Evidence goes in `~/wbr-evidence-archive/`, never inside the git repository folder.

## Step 3 [MAC] Verify
```sh
cd ~/wbr-evidence-archive && shasum -a 256 -c RUN.sha256 | grep -v ': OK$'; echo "lines_not_ok_above"
```
Nothing printed above `lines_not_ok_above` means every file matched. Any
`FAILED` line: copy again into a new folder name; never edit files to match.

## Deleting the source (rare)
Only if the user asks, only after step 3 is clean, and only with
`CONFIRM DELETE ~/wbr-evidence/RUN`. Default on lab day: keep it.

## Report
Run folder, number of files in the manifest, verification result, archive path.
