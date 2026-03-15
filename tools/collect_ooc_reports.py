#!/usr/bin/env python3
import argparse, json, re
from pathlib import Path


def parse_util(path: Path):
    text = path.read_text(errors='ignore')
    out = {'file': str(path)}
    patterns = {
        'LUT': r'\|\s*CLB LUTs\*?\s*\|\s*(\d+)',
        'FF': r'\|\s*CLB Registers\s*\|\s*(\d+)',
        'BRAM': r'\|\s*Block RAM Tile\s*\|\s*([0-9.]+)',
        'DSP': r'\|\s*DSPs\s*\|\s*(\d+)',
    }
    for k, p in patterns.items():
        m = re.search(p, text)
        if m:
            out[k] = m.group(1)
    return out


def parse_timing(path: Path):
    text = path.read_text(errors='ignore')
    out = {'file': str(path)}
    m = re.search(r'WNS\s*\(ns\)\s*[:|]\s*([-0-9.]+)', text)
    if m:
        out['WNS_ns'] = float(m.group(1))
    m = re.search(r'TNS\s*\(ns\)\s*[:|]\s*([-0-9.]+)', text)
    if m:
        out['TNS_ns'] = float(m.group(1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reports-dir', required=True)
    ap.add_argument('--out-json', required=True)
    ap.add_argument('--out-md', required=True)
    args = ap.parse_args()

    rd = Path(args.reports_dir)
    mods = ['fdpe','skag_mem','xorshift128plus','pmo_ga_multigen']
    data = {'modules': {}}
    lines = ['# OOC Synthesis Report Summary', '']
    for mod in mods:
        util = rd / f'{mod}_utilization.rpt'
        tim = rd / f'{mod}_timing_summary.rpt'
        entry = {}
        if util.exists():
            entry['utilization'] = parse_util(util)
        if tim.exists():
            entry['timing'] = parse_timing(tim)
        data['modules'][mod] = entry
        lines.append(f'## {mod}')
        if not entry:
            lines.append('No reports found.')
        else:
            lines.append(f'```json\n{json.dumps(entry, indent=2)}\n```')
        lines.append('')
    Path(args.out_json).write_text(json.dumps(data, indent=2))
    Path(args.out_md).write_text('\n'.join(lines))
    print(f'Wrote {args.out_json}')
    print(f'Wrote {args.out_md}')

if __name__ == '__main__':
    main()
