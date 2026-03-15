#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def parse_summary(path: Path) -> dict:
    out = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if '=' in line:
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip()
            try:
                out[k] = int(v)
            except ValueError:
                out[k] = v
    return out

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--summary', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    data = parse_summary(Path(args.summary))
    data['overall_pass'] = int(data.get('fail_count', 1)) == 0
    Path(args.out).write_text(json.dumps(data, indent=2))
    print(f"Wrote {args.out}")

if __name__ == '__main__':
    main()
