# Evidence kept on the Mac only (not committed)

Commit of 2026-10-14 adds text, logs, configs, scripts, small trajectories and plots from
`experiments/2026-09-12-*`, `2026-09-13-*`, `2026-10-13-*`, `2026-10-14-*`. Rule: no recordings, raw images,
archives or files over 5 MB. These stay in the owner's Mac working tree (`~/Desktop/Research/wbr-perception-phase1-runtime/experiments/`):

| Folder | Excluded | Count | Size |
|---|---|---|---|
| 2026-09-13-d435i-post-reboot-20260913T023833Z | raw IR frames `.pgm` | 1976 | 607 MB |
| 2026-09-13-d435i-post-reboot-20260913T023833Z | files > 5 MB (`frames.jsonl` from stationary-600s and guided-60s, 5.5 MB `soak/frames.csv` copies) | 9 | 184 MB |
| 2026-09-13-d435i-post-reboot-20260913T023833Z | `.tar` evidence bundles, `.tar.gz` runtime bundles | 5 | 12 MB |
| 2026-09-13-d435i-camera-capture-20260913T015621Z | `.tar.gz` runtime bundle | 1 | 0.1 MB |
| 2026-09-13-* | `active-calibration-table.bin` (512-byte calibration table reads of the old unit) | 3 | 1.5 kB |
| 2026-10-13-n4a-euroc-mh01/eval | `gt_data.tum`, `gt_data.csv` (EuRoC MH01 ground truth; reproducible from the public dataset) | 2 | 14 MB |
| 2026-09-12-*, 2026-10-13-n4b-d435i-prep | `__pycache__/*.pyc` | 16 | 0.2 MB |
| 2026-10-14-d435i-demo | `.mplconfig/` matplotlib font cache (ignored by the folder's `.gitignore`) | 2 | small |

No `.db3` / `.bag` recordings exist in these Mac folders; D435i takes live on the Pi under `~/wbr-evidence/`.
SHA256SUMS files committed alongside some folders may list excluded files; their hashes remain checkable against the Mac copies.
