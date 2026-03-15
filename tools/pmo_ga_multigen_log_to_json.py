#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def parse_value(v: str):
    v = v.strip()
    if v.lower() in ('true', 'false'):
        return v.lower() == 'true'
    try:
        if v.startswith('0x') or v.startswith('0X'):
            return int(v, 16)
        return int(v)
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return v

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--summary', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    data = {}
    for line in Path(args.summary).read_text().splitlines():
        line = line.strip()
        if '=' in line:
            k, v = line.split('=', 1)
            data[k.strip()] = parse_value(v)
    Path(args.out).write_text(json.dumps(data, indent=2))
    print(f'Wrote {args.out}')

if __name__ == '__main__':
    main()
