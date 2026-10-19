#!/usr/bin/env python3
"""Print a lab tool result.json as a short criterion table (read-only)."""
import json
import sys

if len(sys.argv) != 2:
    sys.exit("usage: show_result.py PATH/result.json")
result = json.load(open(sys.argv[1]))
print(f"check={result.get('check')} overall={result.get('status')}")


def short(value):
    text = value if isinstance(value, str) else json.dumps(value)
    return text if len(text) <= 80 else text[:77] + "..."


for c in result.get("criteria", []):
    print(f"{c.get('status', '?'):8} {c.get('id')}  measured={short(c.get('measured'))}"
          f"  threshold={short(c.get('threshold'))}")
