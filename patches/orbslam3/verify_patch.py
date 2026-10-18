#!/usr/bin/env python3
"""Offline patch/probe check. This does not run ORB-SLAM3 or pass N4B."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
PATCH = "0001-initialize-localmapping-startup-state.patch"
VERSION = "1.0"


def utc():
    return datetime.now(timezone.utc).isoformat()


def function(text, signature):
    """Extract an unchanged upstream function, including its balanced braces."""
    start = text.index(signature)
    opening = text.index("{", start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[start:end]


def probe(source):
    header = (source / "include/LocalMapping.h").read_text()
    declarations = []
    for kind, name in (("double", "mFirstTs"), ("KeyFrame*", "mpCurrentKeyFrame")):
        declarations.append(re.search(re.escape(kind) + r"\s+" + name + r"[^;]*;", header)[0])
    mapper = function((source / "src/LocalMapping.cc").read_text(),
                      "double LocalMapping::GetCurrKFTime()")
    system = function((source / "src/System.cc").read_text(),
                      "double System::GetTimeFromIMUInit()")
    # The exact pinned constructor initializes neither member. Only the two
    # real member declarations and two real method bodies are compiled here.
    return """#include <cassert>
#include <cstring>
#include <new>
struct KeyFrame { double mTimeStamp; };
struct LocalMapping {
    LocalMapping() {} // surrogate for the pinned constructor's omitted fields
    DECLARATIONS
    double GetCurrKFTime();
};
struct Atlas { bool initialized = false; bool isImuInitialized() { return initialized; } };
struct System {
    LocalMapping* mpLocalMapper;
    Atlas* mpAtlas;
    double GetTimeFromIMUInit();
};
MAPPER
SYSTEM
int main() {
    alignas(LocalMapping) unsigned char storage[sizeof(LocalMapping)];
    std::memset(storage, 0xa5, sizeof(storage));
    LocalMapping* mapping = new (storage) LocalMapping;
    assert(mapping->mpCurrentKeyFrame == nullptr);
    assert(mapping->mFirstTs == 0.0);
    assert(mapping->GetCurrKFTime() == 0.0);
    Atlas atlas;
    System system{mapping, &atlas};
    assert(system.GetTimeFromIMUInit() == 0.0);
    KeyFrame frame{11.0}; // synthetic seconds in one shared camera/IMU clock
    mapping->mpCurrentKeyFrame = &frame;
    mapping->mFirstTs = 10.0;
    assert(mapping->GetCurrKFTime() == 11.0);
    assert(system.GetTimeFromIMUInit() == 0.0);
    atlas.initialized = true;
    assert(system.GetTimeFromIMUInit() == 1.0);
    frame.mTimeStamp = 10.0;
    assert(system.GetTimeFromIMUInit() == 0.0);
    mapping->~LocalMapping();
}
""".replace("DECLARATIONS", "\n    ".join(declarations)).replace("MAPPER", mapper).replace("SYSTEM", system)


def check(source, outdir, compiler=None, analyze=False):
    started = utc()
    outdir.mkdir(parents=True, exist_ok=False)
    raw = outdir / "raw"
    raw.mkdir()
    manifest = json.loads((HERE / "source_manifest.json").read_text())
    criteria = []

    def criterion(name, description, status, measured, evidence, expectation):
        criteria.append(dict(id=name, description=description, status=status,
                             measured=measured, unit="semantic check", threshold=expectation,
                             evidence=evidence, threshold_source="SOURCE-SUPPORTED: source_manifest.json; pinned upstream behavior"))

    def command(name, args, cwd=None):
        (raw / (name + ".command.json")).write_text(json.dumps(args) + "\n")
        try:
            env = dict(os.environ)
            if cwd is not None:
                # Prevent git apply from discovering the enclosing worktree and
                # silently skipping paths outside its current subdirectory.
                env["GIT_CEILING_DIRECTORIES"] = str(Path(cwd).parent)
            result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, check=False)
        except FileNotFoundError:
            (raw / (name + ".stderr")).write_text("Executable unavailable: " + args[0] + "\n")
            return None
        (raw / (name + ".stdout")).write_bytes(result.stdout)
        (raw / (name + ".stderr")).write_bytes(result.stderr)
        (raw / (name + ".exit.txt")).write_text(str(result.returncode) + "\n")
        return result.returncode

    if analyze:
        inputs = source / "raw"
        revision = inputs / "revision.txt"
        patch = inputs / PATCH
    else:
        inputs = source
        revision = None
        patch = HERE / PATCH
    missing = []
    for relative in manifest["files"]:
        target = raw / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        original = inputs / relative
        if original.is_file():
            shutil.copyfile(original, target)
        else:
            missing.append(relative)
    if patch.is_file():
        shutil.copyfile(patch, raw / PATCH)
    else:
        missing.append(PATCH)
    if analyze:
        if revision.is_file():
            shutil.copyfile(revision, raw / "revision.txt")
        else:
            missing.append("revision.txt")
    elif source.is_dir():
        rc = command("revision", ["git", "-C", str(source.resolve()), "rev-parse", "HEAD"])
        if rc == 0:
            shutil.copyfile(raw / "revision.stdout", raw / "revision.txt")
        else:
            missing.append("verified git revision")
    else:
        missing.append("source directory")
    hashes = {p: hashlib.sha256((raw / p).read_bytes()).hexdigest()
              for p in manifest["files"] if (raw / p).is_file()}
    (raw / "source_identity.json").write_text(json.dumps(dict(hashes=hashes, missing=missing), indent=2) + "\n")
    matches = (not missing and hashes == manifest["files"] and
               (raw / "revision.txt").read_text().strip() == manifest["upstream_commit"])
    criterion("source_pin", "Exact pinned revision and source bytes", "BLOCKED" if missing else "PASS" if matches else "FAIL",
              dict(hashes=hashes, missing=missing), "raw/source_identity.json", "exact revision and SHA-256 equality")

    if matches:
        # Every mutation occurs in an automatically removed worktree-local tmp.
        tmp_root = HERE / "tmp"
        tmp_root.mkdir(exist_ok=True)
        try:
            with tempfile.TemporaryDirectory(dir=tmp_root) as temporary:
                scratch = Path(temporary)
                for relative in manifest["files"]:
                    target = scratch / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(raw / relative, target)
                patch_path = str((raw / PATCH).resolve())
                rc = command("apply-check", ["git", "apply", "--verbose", "--check", patch_path], cwd=scratch)
                if rc == 0:
                    rc = command("apply", ["git", "apply", "--verbose", patch_path], cwd=scratch)
                criterion("patch_applies", "Patch checks/applies to pinned source copy", "BLOCKED" if rc is None else "PASS" if rc == 0 else "FAIL",
                          rc, "raw/apply-check.stderr", "git apply --check and git apply succeed")
                if rc == 0:
                    (raw / "probe.cc").write_text(probe(scratch))
                    selected = compiler or shutil.which("clang++") or shutil.which("c++")
                    codes = []
                    if selected:
                        command("compiler-version", [selected, "--version"])
                        for standard in ("c++11", "c++17"):
                            executable = scratch / (standard + "-probe")
                            compiled = command(standard + "-compile", [selected, "-std=" + standard, "-Wall", "-Wextra", "-Werror", "-pedantic",
                                               str((raw / "probe.cc").resolve()), "-o", str(executable)])
                            codes.append(compiled)
                            if compiled == 0:
                                codes.append(command(standard + "-run", [str(executable)]))
                    status = "BLOCKED" if not codes or None in codes else "PASS" if all(c == 0 for c in codes) else "FAIL"
                    criterion("startup_probe", "Isolated real declarations/methods compile and satisfy startup/initialized invariants",
                              status, codes, "raw/probe.cc", "both C++11/C++17 compilation and assertions succeed")
        finally:
            tmp_root.rmdir()
    if not any(c["id"] == "patch_applies" for c in criteria):
        criterion("patch_applies", "Patch applicability", "BLOCKED", None, "raw/source_identity.json", "requires exact source pin")
    if not any(c["id"] == "startup_probe" for c in criteria):
        criterion("startup_probe", "Isolated startup regression", "BLOCKED", None, "raw/source_identity.json", "requires applicable patch and compiler")
    statuses = {c["status"] for c in criteria}
    status = "FAIL" if "FAIL" in statuses else "BLOCKED" if "BLOCKED" in statuses else "PASS"
    result = dict(check="orbslam3_n4b_startup_patch", tool_version=VERSION, status=status,
                  started_utc=started, ended_utc=utc(), host=dict(system=platform.system(), machine=platform.machine(), python=platform.python_version()),
                  criteria=criteria, raw_files=[dict(path=str(p.relative_to(outdir)), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                                                for p in sorted(raw.rglob("*")) if p.is_file()],
                  notes=["MEASURED offline software checks only. No Pi or N4B gate PASS.",
                         "SOURCE-SUPPORTED probe uses actual member declarations and method bodies, a surrogate constructor and stub KeyFrame/Atlas.",
                         "UNKNOWN: full translation-unit compilation, linked Pi behavior, concurrency/reset safety, physical sensor input."])
    (outdir / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print("criterion        status")
    for c in criteria:
        print(f"{c['id']:<16} {c['status']}")
    print("overall         ", status, "(offline software only)")
    return {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[status]


def main():
    class Parser(argparse.ArgumentParser):
        def error(self, message):
            self.print_usage(sys.stderr)
            self.exit(3, f"usage error: {message}\n")

    parser = Parser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source", type=Path)
    group.add_argument("--analyze-only", type=Path)
    parser.add_argument("--outdir", type=Path, required=True, help="fresh output directory")
    parser.add_argument("--compiler", help="explicit compiler executable, e.g. clang++")
    args = parser.parse_args()
    try:
        return check(args.source or args.analyze_only, args.outdir, args.compiler, args.analyze_only is not None)
    except (OSError, ValueError, IndexError, AttributeError) as error:
        print(f"usage/internal error: {error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
