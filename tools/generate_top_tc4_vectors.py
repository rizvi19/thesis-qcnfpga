#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json
from pathlib import Path

POP=8
GEN=3
MASK=0x0005
SEED0=1
SEED1=2
FDPE_X_Q4_13=8192
FDPE_F_INIT=63569
INIT_EDGE_FIELDS = dict(qber=100, arrival_rate=2000, fidelity=63569, key_count=300)
DATA = [
    [
        dict(id=0, lat=360000, fid=56000, util=17000, gene=0x1101),
        dict(id=1, lat=350000, fid=56500, util=16600, gene=0x1122),
        dict(id=2, lat=345000, fid=58000, util=16000, gene=0x1144),
        dict(id=3, lat=334000, fid=59500, util=15100, gene=0x1166),
        dict(id=4, lat=327680, fid=60948, util=14418, gene=0x1188),
        dict(id=5, lat=336000, fid=60000, util=14750, gene=0x11AA),
        dict(id=6, lat=342000, fid=59200, util=15150, gene=0x11CC),
        dict(id=7, lat=348000, fid=58500, util=15600, gene=0x11EE),
    ],
    [
        dict(id=16, lat=352000, fid=56600, util=16800, gene=0x1201),
        dict(id=17, lat=346000, fid=57400, util=16200, gene=0x1222),
        dict(id=18, lat=341000, fid=58400, util=15850, gene=0x1244),
        dict(id=19, lat=333000, fid=59800, util=15080, gene=0x1266),
        dict(id=20, lat=329000, fid=60600, util=14500, gene=0x1288),
        dict(id=21, lat=335000, fid=60050, util=14820, gene=0x12AA),
        dict(id=22, lat=340000, fid=59350, util=15250, gene=0x12CC),
        dict(id=23, lat=347000, fid=58600, util=15650, gene=0x12EE),
    ],
    [
        dict(id=32, lat=340000, fid=58200, util=15800, gene=0x2001),
        dict(id=33, lat=334000, fid=59000, util=15100, gene=0x3456),
        dict(id=34, lat=329500, fid=60000, util=14600, gene=0x2078),
        dict(id=35, lat=325500, fid=60800, util=14450, gene=0x209A),
        dict(id=36, lat=321000, fid=61200, util=14350, gene=0x20BC),
        dict(id=37, lat=319500, fid=61300, util=14320, gene=0x20DE),
        dict(id=38, lat=318000, fid=61550, util=14200, gene=0x20F0),
        dict(id=39, lat=323000, fid=61100, util=14400, gene=0x20FF),
    ]
]

def dominates(a, b):
    a_no_worse = a['lat'] <= b['lat'] and a['fid'] >= b['fid'] and a['util'] <= b['util']
    b_no_worse = b['lat'] <= a['lat'] and b['fid'] >= a['fid'] and b['util'] <= a['util']
    a_strict = a['lat'] < b['lat'] or a['fid'] > b['fid'] or a['util'] < b['util']
    b_strict = b['lat'] < a['lat'] or b['fid'] > a['fid'] or b['util'] < a['util']
    return a_no_worse and a_strict, b_no_worse and b_strict

def prefer(a, b):
    a_dom, b_dom = dominates(a, b)
    if a_dom:
        return a
    if b_dom:
        return b
    if a['lat'] != b['lat']:
        return a if a['lat'] < b['lat'] else b
    if a['fid'] != b['fid']:
        return a if a['fid'] > b['fid'] else b
    if a['util'] != b['util']:
        return a if a['util'] < b['util'] else b
    return a

def pack(row):
    return f"{row['id'] & 0xFFFF:04x}{row['lat'] & 0xFFFFFFFF:08x}{row['fid'] & 0xFFFF:04x}{row['util'] & 0xFFFF:04x}{row['gene'] & 0xFFFF:04x}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--tb-dir', required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    tb_dir = Path(args.tb_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tb_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / 'qflow_top_tc4_candidates.csv'
    memh_path = tb_dir / 'qflow_top_tc4_candidates.memh'
    expected_path = out_dir / 'qflow_top_tc4_expected.json'

    rows = []
    global_best = None
    per_gen_best = []
    for g, gen_rows in enumerate(DATA):
        best = None
        for i, row in enumerate(gen_rows):
            row2 = dict(gen=g, index=i, **row)
            rows.append(row2)
            best = row if best is None else prefer(best, row)
            global_best = row if global_best is None else prefer(global_best, row)
        per_gen_best.append(best)

    last_gen = DATA[-1]
    child = ((last_gen[0]['gene'] & 0xFF00) | (last_gen[1]['gene'] & 0x00FF)) & 0xFFFF
    mutated = child ^ MASK

    with csv_path.open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['gen','index','id','latency_q16_16','fidelity_q0_16','util_q0_16','gene16'])
        for r in rows:
            w.writerow([r['gen'], r['index'], r['id'], r['lat'], r['fid'], r['util'], f"0x{r['gene']:04X}"])

    with memh_path.open('w') as f:
        for r in rows:
            f.write(pack(r) + "\n")

    expected = {
        'integration_stage': 'step9e_top_tc4_smoke',
        'seeds': {'seed0': SEED0, 'seed1': SEED1},
        'fdpe_case': {
            'x_q4_13': FDPE_X_Q4_13,
            'f_init_q0_16': FDPE_F_INIT,
            'expected_nominal_result_q0_16': 23385,
            'allowed_abs_diff_lsb': 2
        },
        'skag_init_edge': INIT_EDGE_FIELDS,
        'expected_best_id': global_best['id'],
        'expected_best_latency_q16_16': global_best['lat'],
        'expected_best_fidelity_q0_16': global_best['fid'],
        'expected_best_util_q0_16': global_best['util'],
        'expected_child_gene16': child,
        'expected_mutated_gene16': mutated,
        'per_generation_best_ids': [r['id'] for r in per_gen_best],
        'notes': [
            'Step 9F smoke test validates the timing-closure-4 top using the iterative-divider SKAG FDPE update pipeline.',
            'Candidate stream remains deterministic for controlled integration checking.'
        ]
    }
    expected_path.write_text(json.dumps(expected, indent=2) + "\n")

    print(f'Wrote {len(rows)} top-level timing-closure-4 candidates to {memh_path}')
    print(f' - {csv_path}')
    print(f' - {expected_path}')

if __name__ == '__main__':
    main()
