#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json
from pathlib import Path

def parse_int(v: str) -> int:
    v=v.strip()
    if v.lower().startswith('0x'):
        return int(v,16)
    return int(v)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--csv', required=True)
    ap.add_argument('--out', required=True)
    args=ap.parse_args()

    rows=list(csv.DictReader(Path(args.csv).open()))
    if not rows:
        raise SystemExit('No rows found in CSV log.')
    r=rows[-1]
    result={
        'prng_last': parse_int(r['prng_last']),
        'fdpe_result': parse_int(r['fdpe_result']),
        'skag_edge': parse_int(r['skag_edge']),
        'skag_weight': parse_int(r['skag_weight']),
        'best_id': parse_int(r['best_id']),
        'best_latency': parse_int(r['best_latency']),
        'best_fidelity': parse_int(r['best_fidelity']),
        'best_util': parse_int(r['best_util']),
        'child_gene': parse_int(r['child_gene']),
        'mutated_gene': parse_int(r['mutated_gene']),
        'overall_pass': r['pass'].strip().lower() in {'1','true','yes'}
    }
    Path(args.out).write_text(json.dumps(result, indent=2))
    print(f'Wrote {args.out}')

if __name__ == '__main__':
    main()
