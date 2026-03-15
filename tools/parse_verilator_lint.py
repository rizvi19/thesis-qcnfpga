#!/usr/bin/env python3
import argparse, json, re
from pathlib import Path

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--log', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    text = Path(args.log).read_text(errors='ignore') if Path(args.log).exists() else ''
    real_error_lines = re.findall(r'^%Error-[A-Z0-9_]+:.*$', text, re.M)
    warnings = len(re.findall(r'(^|\n)%Warning', text))
    modules = sorted(set(re.findall(r'(rtl/[A-Za-z0-9_]+\.v)', text)))
    result = {
        'tool': 'verilator',
        'overall_pass': len(real_error_lines) == 0,
        'error_count': len(real_error_lines),
        'warning_count': warnings,
        'modules_mentioned': modules,
        'notes': [
            'Warnings should be reviewed before synthesis even if lint passes.',
            'Multiple alternate top modules are expected at this milestone; review MULTITOP warnings in context.'
        ]
    }
    Path(args.out).write_text(json.dumps(result, indent=2))
    print(f'Wrote {args.out}')
if __name__ == '__main__':
    main()
