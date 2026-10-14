# WBR process and learning deck — 13 October 2026

Open [main.pdf](main.pdf): 44 English pages (cover plus 43 content pages), six parts, matching the reference deck's theme, Avenir Next/Menlo fonts, palette and TikZ diagram style. [REVIEW_LOG.md](REVIEW_LOG.md) records the build/review loop. Existing builder logs and the brief were retained.

Build and render (from this folder):

```bash
latexmk -xelatex -interaction=nonstopmode main.tex
swift -module-cache-path qa/swift-cache \
  ~/Desktop/OS/OS-project/heterogeneous-edge-ai-os/slides/render.swift main.pdf preview
```

`main.tex` is the editable artifact. `build_deck.py` regenerates it from the page content and the reference preamble; edit the generator if regenerating. Requirements: local TeX installation with moloch, XeLaTeX, Avenir Next, Menlo, and macOS Swift/PDFKit. PNG previews are 1280×719; inspect each at native size. `qa/page-index.tsv` lists every page. `qa/build-revision1-final.log`, `qa/validation-revision1.txt`, `qa/deck-text.txt` and `qa/provenance.json` retain checks and provenance. Reference citations were rechecked against the current 91-page reference PDF; `qa/reference-text-revision1.txt` and `qa/reference-page-index-revision1.tsv` record that edition. Re-check citations if it changes. Revision 1 adds the cover, moves “Where we are” to page 2 and updates the reading route. The generator reproduces the reviewed source and explicit reference page numbers. The cover reuses `slides_course/images/P04.png`; no new illustration was generated.

Source key (paths relative to repository root):

- **[F]** `experiments/2026-10-13-SESSION_FACTS_FOR_SLIDES.md`: authoritative session summary, including Pi builds reported by another builder. This slide task did not independently inspect the Pi.
- **[A]** `experiments/2026-10-13-n4a-euroc-mh01/`: report, per-run trajectories/stdout, power log, `eval/ape_summary.txt`, reference and converted estimates.
- **[B]** `experiments/2026-10-13-n4b-d435i-prep/`: recorder/helpers, unapplied patch, candidate YAML, calibration notes, offline verification and plan. Older prose says `.bag`; current recorder source and facts specify `stereo_imu.db3`. Validate actual binary/output before use.
- **[G]** `experiments/2026-10-13-pi5-env-snapshot/bundles/wbr-runtime-20261013T044130Z/PHASE_A_RUNBOOK.md`: active-unit strict N1/N2/N3 instructions. Preserve the full runbook alongside abbreviated slide commands.
- Camera: `experiments/2026-10-13-pi5-env-snapshot/ADDENDUM_CAMERA_SWAP.md` and raw enumeration/calibration readback.
- Native build: `experiments/2026-10-13-orbslam3-pi-build/build_orbslam3.sh`; some underlying build logs remain on Pi, as identified by the session facts.
- Reference methods and gate criteria: `slides_course/main.tex`, inspected `slides_course/main.pdf`; historical context: `docs/PROJECT_STATE.md`, `docs/NEXT_GATE.md`. Neither historical draft supersedes the October facts.

Primary external verification: [Campos et al., accepted T-RO paper](https://arxiv.org/pdf/2007.11898), Table II, MH01 stereo-inertial **0.036 m**, median of ten trials, SE(3) alignment; our three-run mean is not the same statistic. [Kalibr camera–IMU documentation](https://github.com/ethz-asl/kalibr/wiki/camera-imu-calibration) supports the planned command and output artifacts. Links also appear in the deck.

All gates remain OPEN. Camera/ORB commands are future command shapes requiring `CAMERA AVAILABLE`, documented prerequisites and exact resolved paths. No camera process, ORB run, sensor capture, calibration/firmware change, SSH, installation or Git mutation occurred in this slide build. Large bags require separately qualified storage; cloning the OS onto a larger microSD does not provide that qualification. Kalibr/Allan tooling and conversion compatibility are PLANNED. Unknown accuracy/latency/calibration budgets stay OPEN.
