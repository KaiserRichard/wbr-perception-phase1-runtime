"""Run one unittest suite, refusing successful but incomplete discovery."""

from pathlib import Path
import sys
import unittest


def cases(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from cases(item)
        else:
            yield item


def main():
    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"BLOCKED: required suite directory is absent: {root}", flush=True)
        return 2
    # Preserve the repository import context of `python3 -m unittest`.
    sys.path.insert(0, str(Path.cwd()))
    loader = unittest.TestLoader()
    suite = loader.discover(str(root), pattern="test*.py")
    tests = list(cases(suite))
    covered = set()
    for test in tests:
        module = sys.modules.get(type(test).__module__)
        filename = getattr(module, "__file__", None)
        if filename:
            covered.add(Path(filename).resolve())
    expected = {p.resolve() for p in root.rglob("test*.py") if p.is_file()}
    missing = sorted(expected - covered)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    if not tests or missing or result.testsRun == len(result.skipped):
        print("BLOCKED: no executed tests or incomplete unittest discovery", flush=True)
        for path in missing:
            print(f"BLOCKED: no tests discovered from {path.relative_to(root)}", flush=True)
        return 2
    print(f"DISCOVERED: {len(expected)} test files, {result.testsRun} tests, "
          f"{len(result.skipped)} skipped", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
