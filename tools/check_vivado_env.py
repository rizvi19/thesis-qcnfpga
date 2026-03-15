#!/usr/bin/env python3
import argparse, json, shutil, subprocess
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    vivado = shutil.which('vivado')
    info = {
        'vivado_available': bool(vivado),
        'vivado_path': vivado,
        'target_part': 'xc7a200tfbg484-1',
        'recommended_modules': ['fdpe', 'skag_mem', 'xorshift128plus', 'pmo_ga_multigen'],
    }
    if vivado:
        try:
            res = subprocess.run([vivado, '-version'], capture_output=True, text=True, timeout=20)
            info['vivado_version_text'] = (res.stdout or res.stderr).strip()
        except Exception as e:
            info['vivado_version_error'] = str(e)
    Path(args.out).write_text(json.dumps(info, indent=2))
    print(f'Wrote {args.out}')

if __name__ == '__main__':
    main()
