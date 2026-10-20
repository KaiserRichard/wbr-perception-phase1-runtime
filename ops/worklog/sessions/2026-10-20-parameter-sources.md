# Parameter provenance audit — 2026-10-20

- Worker codex-b for conductor codex-f; bounded read-only source research and two
  documentation files. No other worker/account launched. No hardware action,
  simulation/training run or shared checkout/process access.
- Read root AGENTS, CURRENT, USER_PROFILE, RESEARCH_RULES, LQR_RL_GUIDE, both
  assumed configs, planar implementation, parity provenance/README, original
  source audit and existing nominal Claude/actuator/parity reviews.
- Initial `git status --short --branch`: clean detached HEAD at `6cae11d`;
  inspected log/remotes; `git fetch origin` succeeded; origin/main remained
  `6cae11df1ad4bfc756752adaf4aeeff72fe3e836`. Created fresh
  `chatgpt/20261020-parameter-sources` from origin/main in this isolated worktree.
- Documentation change: created `docs/learning/MODEL_PARAMETER_SOURCES.md`, one
  table covering current values, aggregate/axis definitions, primary evidence,
  applicability and UNKNOWNs. Created this session receipt. No shared worklog or
  DOCUMENTATION_LOG edit; conductor owns those updates.
- Remote research cache: `/private/tmp/wbr-parameter-sources-20261020/`.
  `upstream-tree.json` has 1,850 entries, not truncated. Twelve small DM-jump text
  files fetched at `6855ef8c6da20246251cfd473467c04112bf800f`; URLs, sizes and
  SHA-256 in `fetch-receipts.json`. VMC/chassisR hashes match vendored provenance.
- Followed manufacturer's official Gitee README to dmBots/dmBot; fetched tree
  and `.gitmodules` at `bcece81ce3ac898b9ced1436c2fe583408126e35`. Its pinned
  submodules supplied J4310 `2da08d236aa06743f85cde409811c005fbae0d5c`, H6215
  `c250cf84c27cb49c11a7be6c741599280352c717`, wheel-legged
  `a6613d4084d354aee9967d14f69156f0084ec8eb`.
- Inspected manufacturer tree metadata and small `get_k.m`, `get_k_length.m`,
  README text. Found explicit example body/rod/wheel constants and shape-derived
  inertias; no proof these define DM-jump's gain generator or owner's assemblies.
  No CAD, large BOM spreadsheet, dataset or video downloaded.
- Read manufacturer J4310 V1.1 manual v1.3 (2026-09-14), p.7, and H6215 manual
  v1.0 (cover 2024-05-21; filename 20240607), p.12. Exact supplier masses are
  approximately 306 g and 360 g per component in those revisions. These are not
  reduced-leg/body/wheel-pair mass estimates. Manual URLs/hashes/sizes retained
  in `manufacturer-fetch-receipts.json`; superseded reseller snippets unused.
- Read Bosch primary BMI088 datasheet rev.1.9 (history 2024-01-05), p.10. Raw
  gyro output noise is not fused body-pitch noise. PDF fetched with curl; native
  Swift PDFKit extracted all three manuals and rendered their specification
  pages; visually checked each table. PDFs/text/PNGs retained in the cache.
- Preserved failed attempts: browser DM tree/raw cache misses; Bosch PDF timeout;
  browser raw supplier PDFs rejected as octet-stream/cache miss. Python urllib
  hit `SSL: CERTIFICATE_VERIFY_FAILED`; system curl with normal TLS verification
  succeeded. One unquoted curl URL hit zsh glob parsing; quoted rerun succeeded.
  Local `rg --files docs/mechanical` returned missing-directory exit 2 because
  that path belongs to upstream, then inspected the pinned upstream text.
  `pdftotext`/Python PDF modules unavailable; used installed native PDFKit.
- Findings: current ASSUMED values retain their labels; radius is a firmware
  constant, not a measurement. No new owner mass/COM/inertia/lag/delay estimate
  established; source per-actuator clamps and supplier ratings are separated
  from aggregate input caps. CAD/BOM partition and five-bar equivalence remain
  unresolved. LQR gains/mass sweeps are not identification.
- Verification: 49 numerical source-text anchors found, zero missing; supplier
  page tables independently inspected. All 25 document reference definitions
  resolve locally. Receipt/cache manifest: `verification-receipt.json`.
- `git diff --cached --check`: PASS. Exactly the two authorized Markdown files
  staged. `git diff --exit-code 6cae11df1ad4bfc756752adaf4aeeff72fe3e836 -- sim`:
  exit 0, no changes. No runtime tests repeated for this documentation-only task.
- Unchanged config SHA-256: planar
  `f6310f9d7ac2c4f44186e43a632d2d75e9a0eecd0766464c28fdee0ab6ad6a99`;
  actuator/noise
  `1bd3c79add70cce74ba423382d557d7996e7a1d3db9f65c3d4bbcdc14840d90f`.
- Bosch PDF SHA-256 (URL is mutable; revision/date checked inside document):
  `53ab734dba49ac202fa6182fc2b545df6c6d7459c9fec6e851a1209e6bac417e`.
