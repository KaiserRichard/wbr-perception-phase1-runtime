"""CLI for small saved JSON evidence only."""

import argparse
from pathlib import Path

from sim.rl.reporting.report import load_report, write_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v1-aggregate", type=Path)
    parser.add_argument("--v2-archive", type=Path)
    parser.add_argument("--out", type=Path, required=True, help="New directory outside git and evidence")
    args = parser.parse_args()
    try:
        report = load_report(args.v1_aggregate, args.v2_archive)
        protected = []
        if args.v1_aggregate:
            parent = args.v1_aggregate.resolve().parent
            protected.append(parent.parent if parent.name == "evaluation" else parent)
        if args.v2_archive:
            protected.append(args.v2_archive)
        write_report(report, args.out, protected)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"Saved-evidence report failed: {exc}\n")
    print(f"Wrote {args.out}: {len(report['rows'])} rows; {report['json_bytes_read']} JSON bytes; no replay")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
