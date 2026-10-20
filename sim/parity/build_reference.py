"""Build the unchanged pinned DM-jump functions with a small host ABI.

Python standard library only. Outputs are experiment artifacts, not source files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / "vendor" / "dm_jump"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_coefficients(source: str) -> str:
    """Return the exact upstream initializer, with no rewritten numeric literals."""
    match = re.search(r"float\s+Poly_Coefficient\s*\[12\]\[4\]\s*=\s*(\{.*?\});", source, re.S)
    if match is None:
        raise ValueError("Pinned 12x4 Poly_Coefficient initializer missing")
    initializer = match.group(1)
    rows = re.findall(r"\{([^{}]+)\}", initializer)
    if len(rows) != 12 or any(len(row.split(",")) != 4 for row in rows):
        raise ValueError("Unexpected coefficient table shape")
    return initializer


def build_reference(out_dir: Path, compiler: str | None = None) -> Path:
    """Build into an absent/empty directory and return the shared-library path."""
    out_dir = Path(out_dir).expanduser().resolve()
    if out_dir.exists() and (not out_dir.is_dir() or any(out_dir.iterdir())):
        raise FileExistsError(f"Refusing nonempty build output: {out_dir}")
    manifest = json.loads((VENDOR / "PROVENANCE.json").read_text())
    for name, expected in manifest["files"].items():
        if sha256(VENDOR / name) != expected:
            raise ValueError(f"Pinned source checksum mismatch: {name}")
    compiler_path = shutil.which(compiler or os.environ.get("CC", "clang"))
    if compiler_path is None and compiler is None:
        compiler_path = shutil.which("cc")
    if compiler_path is None:
        raise RuntimeError("C compiler unavailable; provide --compiler clang or cc")
    system = platform.system()
    if system not in ("Darwin", "Linux"):
        raise RuntimeError("Host reference currently supports macOS and Linux only")
    out_dir.mkdir(parents=True, exist_ok=True)
    initializer = extract_coefficients((VENDOR / "User/APP/chassisR_task.c").read_text())
    generated = out_dir / "gain_coefficients.h"
    generated.write_text("/* Exact initializer extracted from pinned chassisR_task.c. */\n"
                         "static float Poly_Coefficient[12][4] = " + initializer + ";\n")
    library = out_dir / ("libwbr_reference.dylib" if system == "Darwin" else "libwbr_reference.so")
    source = VENDOR / "User/Algorithm/VMC"
    wrapper = ROOT / "c_reference"
    command = [compiler_path, "-std=c11", "-O0", "-fno-fast-math", "-ffp-contract=off",
               "-fPIC", "-dynamiclib" if system == "Darwin" else "-shared",
               "-I", str(wrapper / "shims"), "-I", str(source), "-I", str(out_dir),
               str(source / "VMC_calc.c"), str(wrapper / "reference.c"), "-lm", "-o", str(library)]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    compiler_version = subprocess.run([compiler_path, "--version"], check=True,
                                      capture_output=True, text=True).stdout
    repository = ROOT.parents[1]
    def git(*args: str) -> str:
        result = subprocess.run(["git", "-C", str(repository), *args],
                                capture_output=True, text=True, check=False)
        return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"
    local_sources = [Path(__file__), *sorted(wrapper.rglob("*.c")),
                     *sorted(wrapper.rglob("*.h")), VENDOR / "PROVENANCE.json"]
    metadata = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_repository": manifest["repository"], "source_commit": manifest["commit"],
        "verified_vendor_sha256": manifest["files"],
        "harness_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in local_sources},
        "coefficient_initializer_sha256": hashlib.sha256(initializer.encode()).hexdigest(),
        "generated_header_sha256": sha256(generated),
        "library": library.name, "library_sha256": sha256(library),
        "compiler_command": command, "compiler_version": compiler_version,
        "compiler_stdout": completed.stdout, "compiler_stderr": completed.stderr,
        "host": platform.platform(), "python": sys.version,
        "repository_commit": git("rev-parse", "HEAD"),
        "repository_status": git("status", "--porcelain"),
        "numeric_contract": "float32 host libm sinf/cosf; no CMSIS-DSP bit-exact claim",
        "vmc_contract": "side 0 right, 1 left; stateless fixed pose; derivative history initialized; sequential calls only",
    }
    (out_dir / "build_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return library


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--compiler")
    args = parser.parse_args()
    print(build_reference(args.out_dir, args.compiler))


if __name__ == "__main__":
    main()
