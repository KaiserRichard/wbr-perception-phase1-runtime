---
name: wbr-storage-migrate
description: Move the Pi 5 system and data from the 32 GB microSD to the 128 GB microSD by cloning the whole card on the Mac, then growing the root partition. Use for any "move data from the 32 GB card to the 128 GB card" request.
---

# 32 GB to 128 GB microSD migration

Read `ops/lab-assistant/INSTRUCTIONS.md` first. This skill contains the most
dangerous commands of the lab day. Follow every confirmation step.

## Plan (decided default)
The Pi 5 has one microSD slot, so the 128 GB card must become the boot card.
We **clone the whole 32 GB card** onto the 128 GB card on the Mac, boot the Pi from
the 128 GB card, then grow its root partition. The **32 GB card is never written**
and stays as a full backup. Nothing is deleted.

If the user only wants to copy some folders, use `wbr-evidence-copy` instead.

Time: CALCULATED about 13 min per full 32 GB pass at an ASSUMED 40 MB/s card
reader (32e9 B / 40e6 B/s = 800 s). Four passes (read, verify, write, verify):
budget about 1 hour. It can be done before the lab if the Pi and Mac are at hand.

Not covered: the 128 GB card's write-speed qualification. Until that is done
under `docs/STORAGE_QUALIFICATION_DRAFT.md` with owner review, it is not a
qualified recording destination. Do not benchmark it here.

## Step 1 [PI] Record the "before" state, then shut down
```sh
df -h / ; lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT
du -sh ~/wbr-evidence ~/wbr-runtime ~/wbr-perception-phase1-runtime 2>/dev/null
sudo shutdown -h now
```
[PHYSICAL] Wait until the green activity LED stops, unplug power, remove the
32 GB card. Put a label on it: "WBR 32GB BACKUP".

## Step 2 [MAC] Space and card identity
```sh
df -h ~
diskutil list external physical
```
Need at least 35 GB free on the Mac. Insert the 32 GB card in the reader, run
`diskutil list external physical` again and find the **new** disk of about
31.9 to 32.0 GB with a small FAT32 `system-boot` partition plus a Linux partition.
Write down its identifier, e.g. `/dev/disk4`. Never use `disk0`, `disk1`, `disk2`
or `disk3` without checking: those are usually the Mac's own disks.

## Step 3 [MAC] Read the 32 GB card into an image (read-only for the card)
Replace `N` with the number found in step 2, and the date.
```sh
diskutil unmountDisk /dev/diskN
mkdir -p ~/wbr-backup && sudo dd if=/dev/rdiskN of=$HOME/wbr-backup/wbr-pi5-32gb-YYYYMMDD.img bs=4m
sudo cmp /dev/rdiskN $HOME/wbr-backup/wbr-pi5-32gb-YYYYMMDD.img && echo IMAGE_IDENTICAL
```
Press Ctrl-T in the terminal to see `dd` progress. `if=` is the card (input),
`of=` is the file (output): check this twice. `IMAGE_IDENTICAL` must appear.
Then save a checksum and eject:
```sh
shasum -a 256 $HOME/wbr-backup/wbr-pi5-32gb-YYYYMMDD.img | tee $HOME/wbr-backup/wbr-pi5-32gb-YYYYMMDD.img.sha256
diskutil eject /dev/diskN
```

## Step 4 [MAC] Identify the 128 GB card
Remove the 32 GB card. Insert the 128 GB card.
```sh
diskutil list external physical
```
Identifiers can change after re-inserting. Find the disk of about 127 to 128 GB.
The assistant must now repeat back: identifier, size, current partitions, and
"everything on this 128 GB card will be erased". The user must reply exactly
`CONFIRM WRITE /dev/rdiskM` (with the real number). Size not ~128 GB: stop.

## Step 5 [MAC] Write and verify (destructive for the 128 GB card only)
```sh
diskutil unmountDisk /dev/diskM
sudo dd if=$HOME/wbr-backup/wbr-pi5-32gb-YYYYMMDD.img of=/dev/rdiskM bs=4m && sync
sudo cmp $HOME/wbr-backup/wbr-pi5-32gb-YYYYMMDD.img /dev/rdiskM
```
Success is exactly `cmp: EOF on .../wbr-pi5-32gb-YYYYMMDD.img` (the card is larger
than the image, and every image byte matched). Any `differ: byte ...` line means
the copy failed: do not boot it; report it. If macOS shows "The disk you inserted
was not readable", click **Ignore**, never Initialize. Then:
```sh
diskutil eject /dev/diskM
```

## Step 6 [PHYSICAL] Boot from the 128 GB card
Only the 128 GB card in the Pi. Store the 32 GB backup card away from the Pi:
never insert both into the Pi at once (identical partition IDs confuse boot).
Power with the 27 W supply.

## Step 7 [PI] Grow the root partition
```sh
findmnt / ; lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT
```
Expect root on `/dev/mmcblk0p2` (label `writable`), disk `mmcblk0` about 119 GiB,
`mmcblk0p2` still about 29 GiB. Repeat that back; the user types
`CONFIRM GROW /dev/mmcblk0p2`. Then:
```sh
sudo growpart /dev/mmcblk0 2
sudo resize2fs /dev/mmcblk0p2
df -h /
```
Expect `/` size about 117 GiB.

## Step 8 [PI] Check nothing was lost
```sh
du -sh ~/wbr-evidence ~/wbr-runtime ~/wbr-perception-phase1-runtime 2>/dev/null
git -C ~/wbr-perception-phase1-runtime status -sb
vcgencmd get_throttled
```
Sizes must match step 1. Then continue with `wbr-orbslam3-bringup`.

## Report
Image path and SHA-256, both cmp results, 128 GB disk identifier used, before and
after `df -h /`, du comparison. Keep the image on the Mac and the 32 GB card as
backup until the owner decides otherwise.
