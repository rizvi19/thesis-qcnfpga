#!/usr/bin/env python3
import argparse, json
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    plan = {
        'stage': 'Step 8B synthesis-prep',
        'goal': 'module-level out-of-context synthesis and report aggregation',
        'modules': [
            {'name': 'fdpe', 'top': 'fdpe'},
            {'name': 'skag_mem', 'top': 'skag_mem'},
            {'name': 'xorshift128plus', 'top': 'xorshift128plus'},
            {'name': 'pmo_ga_multigen', 'top': 'pmo_ga_multigen'},
        ],
        'expected_reports': [
            'utilization', 'timing_summary'
        ],
        'known_pre_synth_notes': [
            'Current lint summary is green at the stage level, but skag_mem still has two BLKSEQ warnings to review.',
            'This stage is OOC synthesis, not final integrated bitstream generation.'
        ]
    }
    Path(args.out).write_text(json.dumps(plan, indent=2))
    print(f'Wrote {args.out}')

if __name__ == '__main__':
    main()
