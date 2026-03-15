#!/usr/bin/env python3
import argparse, json, re
from pathlib import Path

def load_json(path: str):
    return json.loads(Path(path).read_text())

def read_text(path: str):
    return Path(path).read_text(errors='ignore')

def extract_phase0_pass(text: str) -> bool:
    upper = text.upper()
    return ('PASS' in upper) and ('FAIL' not in upper.splitlines()[:30])

def extract_skag_pass(text: str):
    m = re.search(r'overall_pass\s*=\s*(true|false)', text, re.I)
    if m:
        return m.group(1).lower() == 'true'
    m = re.search(r'fail_count\s*=\s*(\d+)', text, re.I)
    return (int(m.group(1)) == 0) if m else None

def get_overall_pass(obj):
    if isinstance(obj, dict):
        if 'overall_pass' in obj:
            return bool(obj['overall_pass'])
        if 'sanity_gates' in obj and isinstance(obj['sanity_gates'], dict) and 'overall_pass' in obj['sanity_gates']:
            return bool(obj['sanity_gates']['overall_pass'])
        if 'fail_count' in obj:
            return int(obj['fail_count']) == 0
    return False

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase0', required=True)
    ap.add_argument('--fdpe', required=True)
    ap.add_argument('--skag', required=True)
    ap.add_argument('--prng', required=True)
    ap.add_argument('--pmo_reduced', required=True)
    ap.add_argument('--pmo_family', required=True)
    ap.add_argument('--pmo_multigen', required=True)
    ap.add_argument('--top_smoke', required=True)
    ap.add_argument('--out-json', required=True)
    ap.add_argument('--out-md', required=True)
    args = ap.parse_args()

    checks = {
        'phase0_freeze': extract_phase0_pass(read_text(args.phase0)),
        'fdpe_rtl': get_overall_pass(load_json(args.fdpe)),
        'skag_rtl': bool(extract_skag_pass(read_text(args.skag))),
        'prng_randomness': get_overall_pass(load_json(args.prng)),
        'pmo_ga_reduced': get_overall_pass(load_json(args.pmo_reduced)),
        'pmo_ga_family': get_overall_pass(load_json(args.pmo_family)),
        'pmo_ga_multigen': get_overall_pass(load_json(args.pmo_multigen)),
        'top_smoke': get_overall_pass(load_json(args.top_smoke)),
    }
    top_smoke = load_json(args.top_smoke)
    overall = all(checks.values())
    result = {
        'overall_pass': overall,
        'checks': checks,
        'top_smoke_best_id': top_smoke.get('best_id'),
        'top_smoke_fdpe_result': top_smoke.get('fdpe_result'),
        'top_smoke_skag_weight': top_smoke.get('skag_weight'),
        'next_stage_recommendation': 'Proceed to synthesis-prep and lint cleanup' if overall else 'Resolve lint errors before synthesis',
    }
    Path(args.out_json).write_text(json.dumps(result, indent=2))
    md = ['# QFlow Verification Status Summary','',f"Overall pass: **{overall}**",'','| Check | Status |','|---|---|']
    for k, v in checks.items():
        md.append(f'| {k} | {"PASS" if v else "FAIL"} |')
    md += ['',f"Top smoke best_id: `{top_smoke.get('best_id')}`",f"Top smoke FDPE result: `{top_smoke.get('fdpe_result')}`",f"Top smoke SKAG weight: `{top_smoke.get('skag_weight')}`",'',f"Next: {result['next_stage_recommendation']}"]
    Path(args.out_md).write_text('\n'.join(md) + '\n')
    print(f'Wrote {args.out_json}')
    print(f'Wrote {args.out_md}')
if __name__ == '__main__':
    main()
