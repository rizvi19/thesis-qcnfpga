#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path

def parse_timing(text: str):
    out = {}
    m = re.search(r'\n\s*([\-\d\.]+)\s+([\-\d\.]+)\s+\d+\s+\d+\s+[\-\d\.]+\s+[\-\d\.]+', text)
    if m:
        out['WNS_ns'] = float(m.group(1)); out['TNS_ns'] = float(m.group(2))
    req = re.search(r'Requirement:\s+([\-\d\.]+)ns', text)
    dpd = re.search(r'Data Path Delay:\s+([\-\d\.]+)ns', text)
    src = re.search(r'Source:\s+(.+)', text)
    dst = re.search(r'Destination:\s+(.+)', text)
    if req: out['Requirement_ns'] = float(req.group(1))
    if dpd: out['Data_path_delay_ns'] = float(dpd.group(1))
    if src: out['Worst_source'] = src.group(1).strip()
    if dst: out['Worst_destination'] = dst.group(1).strip()
    if out.get('Data_path_delay_ns'):
        out['approx_Fmax_MHz'] = round(1000.0 / out['Data_path_delay_ns'], 3)
    return out

def parse_util(text: str):
    util = {}
    for cell in ['BUFG','DSP48E1','RAMB36E1','RAMB18E1','LUT6','FDRE','FDCE','FDPE']:
        m = re.search(rf'\|\d+\s*\|{cell}\s*\|\s*(\d+)\|', text)
        if m: util[cell] = int(m.group(1))
    return util

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--timing-rpt', required=True)
    ap.add_argument('--util-rpt', required=True)
    ap.add_argument('--out-json', required=True)
    ap.add_argument('--out-md', required=True)
    args = ap.parse_args()
    timing_text = Path(args.timing_rpt).read_text(errors='ignore')
    util_text = Path(args.util_rpt).read_text(errors='ignore')
    summary = {
        'top': 'qflow_top_tc',
        'utilization': parse_util(util_text),
        'timing': parse_timing(timing_text),
        'notes': [
            'Step 9C timing-closure build stores GA read weight in memory instead of recomputing it on the read path.',
            'Critical-path reduction is expected primarily inside u_skag ga-read weight generation.'
        ]
    }
    Path(args.out_json).write_text(json.dumps(summary, indent=2))
    md = ['# QFlow Top-Level Timing-Closure Summary', '', '## Utilization']
    for k,v in summary['utilization'].items():
        md.append(f'- {k}: {v}')
    md += ['', '## Timing']
    for k,v in summary['timing'].items():
        md.append(f'- {k}: {v}')
    md += ['', '## Notes'] + [f'- {n}' for n in summary['notes']]
    Path(args.out_md).write_text('\n'.join(md) + '\n')
    print(f'Wrote {args.out_json}')
    print(f'Wrote {args.out_md}')

if __name__ == '__main__':
    main()
