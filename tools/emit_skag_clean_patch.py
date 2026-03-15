#!/usr/bin/env python3
import argparse
from pathlib import Path

PATCH_TEXT = '''`timescale 1ns/1ps

// Optional lint-clean variant of skag_mem reset loops.
// Replace only if you want to eliminate the remaining BLKSEQ warnings before synthesis.
// Apply manually to your current rtl/skag_mem.v reset loop:
//     edge_mem[i]   <= 64'd0;
//     weight_mem[i] <= INF_WEIGHT;
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    Path(args.out).write_text(PATCH_TEXT)
    print(f'Wrote {args.out}')

if __name__ == '__main__':
    main()
