# T16 deployment report

## Built

- `make_bundle.sh` creates a commit-named tarball for Pi-owned runtime paths,
  excludes host simulation and firmware trees, and records build UTC plus
  per-file SHA-256 in `MANIFEST.json`. Dirty checkout refusal is default;
  `--allow-dirty` is explicit and recorded.
- `deploy.sh` supports remote `scp`/`ssh`, a command-printing dry run, local
  filesystem simulation, and rollback. It installs into a new release folder,
  validates contents before switching `current`, and keeps `previous` for
  rollback.
- `pi_smoke.sh` checks the manifest, Python/modules, CLI help, fixture analysis,
  and hardware-free unittest suites, then writes a PASS/FAIL/BLOCKED
  `result.json` and raw logs.

## Verification

The implementation tests are in `tests/test_deploy.py`; all **8 tests passed**
and output is saved to `tests/last-run.log`. They cover a temporary git bundle,
dirty-tree rejection, tamper detection, fake-host dry run, and local
install/rollback, status precedence across PASS/FAIL/BLOCKED, and checks that a
manifest contains the saved real power/USB evidence fixture. All three shell
scripts pass `bash -n`.

The smoke runner was also run against an extracted bundle on the Mac.
Manifest verification, CLI help, fixture analysis, tool availability, and all
bundled unit suites passed. Overall status was **BLOCKED** because this Mac has
Python 3.11.0rc2 and T16 requires Python 3.12 or newer on the Pi. The short
summary is saved in `tests/smoke-last-run.log`.

## Not verified and risks

- No SSH, SCP, Pi, camera, ROS graph, or serial device was accessed for this
  ticket. Remote shell/scp behavior and Python 3.12 execution remain UNKNOWN
  until the operator runs the documented commands on the intended Pi.
- `current` is switched atomically after extracted-file verification. The
  remote destination is commit-named and never overwritten. A failed extraction
  can leave an incomplete destination directory; remove it manually only after
  inspecting it before retrying.
- Existing tools vary in CLI shape. The smoke runner checks documented
  `--analyze-only` paths where they exist; tools without offline analyze modes
  are covered by their help output and fixture-backed unittest suites.
- Fixture PASS is not a hardware or project gate PASS.

Proposed commit message: `Add reproducible Pi deployment bundle and smoke test`
