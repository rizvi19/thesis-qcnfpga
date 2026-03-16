#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path


def parse_timing(text: str):
    out = {}
    # Summary row: WNS TNS WHS THS PWNS PTNS
    m = re.search(r'\n\s*([\-\d\.]+)\s+([\-\d\.]+)\s+([\-\d\.]+)\s+([\-\d\.]+)\s+([\-\d\.]+)\s+([\-\d\.]+)', text)
    if m:
        out['WNS_ns'] = float(m.group(1))
        out['TNS_ns'] = float(m.group(2))
        out['WHS_ns'] = float(m.group(3))
        out['THS_ns'] = float(m.group(4))
        out['PWNS_ns'] = float(m.group(5))
        out['PTNS_ns'] = float(m.group(6))
    req = re.search(r'Requirement:\s+([\-\d\.]+)ns', text)
    dpd = re.search(r'Data Path Delay:\s+([\-\d\.]+)ns', text)
    src = re.search(r'Source:\s+(.+)', text)
    dst = re.search(r'Destination:\s+(.+)', text)
    if req:
        out['Requirement_ns'] = float(req.group(1))
    if dpd:
        out['Data_path_delay_ns'] = float(dpd.group(1))
    if src:
        out['Worst_source'] = src.group(1).strip()
    if dst:
        out['Worst_destination'] = dst.group(1).strip()
    if out.get('Data_path_delay_ns'):
        out['approx_Fmax_MHz'] = round(1000.0 / out['Data_path_delay_ns'], 3)
    if 'WNS_ns' in out:
        out['meets_setup_timing'] = out['WNS_ns'] >= 0.0
    if 'WHS_ns' in out:
        out['meets_hold_timing'] = out['WHS_ns'] >= 0.0
    return out


def parse_util(text: str):
    util = {}
    for cell in ['BUFG', 'DSP48E1', 'RAMB36E1', 'RAMB18E1', 'LUT6', 'FDRE', 'FDCE', 'FDPE']:
        m = re.search(rf'\|\s*\d+\s*\|\s*{cell}\s*\|\s*(\d+)\s*\|', text)
        if m:
            util[cell] = int(m.group(1))
    return util


def parse_route_status(text: str):
    out = {}
    for pat, key in [
        (r'# of logical nets\s*:\s*(\d+)', 'logical_nets'),
        (r'# of nets not needing routing\s*:\s*(\d+)', 'nets_not_needing_routing'),
        (r'# of internally routed nets\s*:\s*(\d+)', 'internally_routed_nets'),
        (r'# of routable nets\s*:\s*(\d+)', 'routable_nets'),
        (r'# of unrouted nets\s*:\s*(\d+)', 'unrouted_nets'),
        (r'# of fully routed nets\s*:\s*(\d+)', 'fully_routed_nets'),
        (r'# of nets with routing errors\s*:\s*(\d+)', 'nets_with_routing_errors'),
    ]:
        m = re.search(pat, text)
        if m:
            out[key] = int(m.group(1))
    if 'unrouted_nets' in out and 'nets_with_routing_errors' in out:
        out['routing_clean'] = (out['unrouted_nets'] == 0 and out['nets_with_routing_errors'] == 0)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--timing-rpt', required=True)
    ap.add_argument('--util-rpt', required=True)
    ap.add_argument('--route-status-rpt', required=True)
    ap.add_argument('--out-json', required=True)
    ap.add_argument('--out-md', required=True)
    args = ap.parse_args()

    timing_text = Path(args.timing_rpt).read_text(errors='ignore')
    util_text = Path(args.util_rpt).read_text(errors='ignore')
    route_text = Path(args.route_status_rpt).read_text(errors='ignore')

    summary = {
        'top': 'qflow_top_tc5',
        'stage': 'Step 9H post-route implementation',
        'utilization': parse_util(util_text),
        'timing': parse_timing(timing_text),
        'route_status': parse_route_status(route_text),
        'notes': [
            'This stage uses the tc5 timing-closure RTL baseline and checks final implementation timing after opt/place/route/phys_opt.',
            'The pass condition is non-negative setup slack at 10 ns and a clean routed design.'
        ]
    }
    Path(args.out_json).write_text(json.dumps(summary, indent=2) + "\n")

    md = ['# QFlow Top-Level Post-Route Implementation Summary', '', '## Utilization']
    for k, v in summary['utilization'].items():
        md.append(f'- {k}: {v}')
    md += ['', '## Timing']
    for k, v in summary['timing'].items():
        md.append(f'- {k}: {v}')
    md += ['', '## Route Status']
    for k, v in summary['route_status'].items():
        md.append(f'- {k}: {v}')
    md += ['', '## Notes'] + [f'- {n}' for n in summary['notes']]
    Path(args.out_md).write_text('\n'.join(md) + '\n')
    print(f'Wrote {args.out_json}')
    print(f'Wrote {args.out_md}')

if __name__ == '__main__':
    main()
