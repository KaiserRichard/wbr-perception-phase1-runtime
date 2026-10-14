# Ticket L validation — 14 October 2026

Documentation checks only; hardware and estimator status remain OPEN.

- Both requested Markdown files have valid local links and balanced code fences.
- All seven Bash command cards pass `bash -n`; none was executed.
- The derived smoke helper changes exactly one analyzer-path reference and passes `bash -n`; it was not executed.
- The reading schedule totals 180 minutes and includes ten self-check questions.
- Course PDF text was extracted locally with macOS PDFKit: 91 pages, with the listed page/title mapping. No deck was edited or rebuilt. Titles remain the stable reference after another thread changes pagination.
- Git branch, status and recent history were inspected before writing. Existing output-folder ticket/logs were preserved. No network, SSH, installs, camera/ORB execution, branches, commits or stash were performed.

Source scope: the supplied session facts/addendum, N4A REPORT, N4B preparation README/plan/calibration notes, `docs/*.md`, both `main.tex` files, and the explicitly requested smoke/analyzer/plot/DEBUG_GUIDE helpers. The course PDF was inspected for the requested page mapping. External reading headings absent from these sources are marked unverified offline.

Manual bench validation: follow the runbook entry conditions; complete the patch-4 rebuild; inspect capture return/checksums/raw audits; review offline initialization, tracking and map IDs; plot retained outputs on the Mac; then review whether to proceed live. A full 100-second RAM take, repaired replay, current Wi-Fi connectivity, stable power and calibrated accuracy remain unverified.

Recheck command-card shell syntax from the Mac repository root, without executing them:

```bash
python3 - <<'PY'
from pathlib import Path
import re, subprocess
p = Path('experiments/2026-10-14-lab-prep/LAB_RUNBOOK_2026-10-15.md')
for block in re.findall(r'```bash\n(.*?)\n```', p.read_text(), re.S):
    subprocess.run(['bash', '-n'], input=block, text=True, check=True)
print('Shell syntax valid; no command card executed')
PY
```

Command adaptations are confined to this runbook: unique directories, checksummed copies in a separate runtime helper bundle, relocation of the analyzer call, preserved exit statuses and post-capture transfers. The 14 October facts supply the RAM workflow and `.db3` filename. No runtime utility, upstream build source, historical evidence or slide source was changed by this ticket.
