#!/usr/bin/env python3
import argparse
from pathlib import Path

TEXT = '''# Run this after Vivado is installed / loaded into PATH
vivado -mode batch -source tcl/run_ooc_synth.tcl

# Expected outputs:
# results/phase8b/*_utilization.rpt
# results/phase8b/*_timing_summary.rpt
# results/phase8b/ooc_report_summary.json
# results/phase8b/ooc_report_summary.md
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    Path(args.out).write_text(TEXT)
    print(f'Wrote {args.out}')

if __name__ == '__main__':
    main()
