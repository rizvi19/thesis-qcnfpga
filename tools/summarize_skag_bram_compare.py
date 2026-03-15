
#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from typing import Dict

CELL_RE = re.compile(r"\|\s*\d+\s*\|\s*([A-Za-z0-9_]+)\s*\|\s*([0-9]+)\s*\|")
BRAM_MAP_RE = re.compile(r"\|\s*([A-Za-z0-9_]+)\s*\|\s*([A-Za-z0-9_]+)\s*\|.*\|\s*([0-9]+)\s*\|\s*([0-9]+)\s*\|")
DIST_RE = re.compile(r"\|\s*([A-Za-z0-9_]+)\s*\|\s*([A-Za-z0-9_]+)\s*\|\s*([A-Za-z0-9_]+)\s*\|\s*([0-9Kk xX]+)\s*\|\s*([A-Za-z0-9_ xX]+)\s*\|")

def empty_metrics() -> Dict[str, int]:
    return {'BRAM18':0,'BRAM36':0,'BRAM_total_equiv18':0,'DSP':0,'LUT':0,'FF':0,'LUTRAM_prims':0}

def parse_utilization_report(path: Path) -> Dict[str, int]:
    metrics = empty_metrics()
    if not path.exists():
        return metrics
    for line in path.read_text(errors='ignore').splitlines():
        m = CELL_RE.search(line)
        if not m:
            continue
        cell, count = m.group(1), int(m.group(2))
        if cell in {'RAMB18E1','RAMB18'}:
            metrics['BRAM18'] += count
        elif cell in {'RAMB36E1','RAMB36'}:
            metrics['BRAM36'] += count
        elif cell == 'DSP48E1':
            metrics['DSP'] += count
        elif cell.startswith('LUT'):
            metrics['LUT'] += count
        elif cell.startswith('FD'):
            metrics['FF'] += count
        elif cell.startswith('RAM'):
            metrics['LUTRAM_prims'] += count
    metrics['BRAM_total_equiv18'] = metrics['BRAM18'] + 2*metrics['BRAM36']
    return metrics

def parse_vivado_log(path: Path) -> Dict[str, object]:
    metrics = empty_metrics()
    mapping = {'block': {}, 'distributed': {}}
    if not path.exists():
        return {'metrics': metrics, 'mapping': mapping}
    section = None
    for line in path.read_text(errors='ignore').splitlines():
        if 'Block RAM: Final Mapping Report' in line:
            section = 'block'; continue
        if 'Distributed RAM: Final Mapping Report' in line:
            section = 'distributed'; continue
        if line.startswith('---'):
            continue
        cm = CELL_RE.search(line)
        if cm:
            cell, count = cm.group(1), int(cm.group(2))
            if cell in {'RAMB18E1','RAMB18'}:
                metrics['BRAM18'] += count
            elif cell in {'RAMB36E1','RAMB36'}:
                metrics['BRAM36'] += count
            elif cell == 'DSP48E1':
                metrics['DSP'] += count
            elif cell.startswith('LUT'):
                metrics['LUT'] += count
            elif cell.startswith('FD'):
                metrics['FF'] += count
            elif cell.startswith('RAM'):
                metrics['LUTRAM_prims'] += count
        if section == 'block':
            bm = BRAM_MAP_RE.search(line)
            if bm:
                mapping['block'][bm.group(2)] = {'RAMB18': int(bm.group(3)), 'RAMB36': int(bm.group(4))}
        elif section == 'distributed':
            dm = DIST_RE.search(line)
            if dm:
                mapping['distributed'][dm.group(2)] = {'primitive': dm.group(5).strip()}
    metrics['BRAM_total_equiv18'] = metrics['BRAM18'] + 2*metrics['BRAM36']
    return {'metrics': metrics, 'mapping': mapping}

def load_baseline(summary_path: Path) -> Dict[str, int]:
    if not summary_path.exists():
        return {'BRAM_total_equiv18':0,'DSP':0}
    payload = json.loads(summary_path.read_text())
    skag = payload.get('modules', {}).get('skag_mem', {})
    util = skag.get('utilization', {})
    out = {'BRAM_total_equiv18': int(util.get('BRAM','0')), 'DSP': int(util.get('DSP','0'))}
    rpt = util.get('file')
    if rpt:
        parsed = parse_utilization_report(Path(rpt))
        if any(parsed.values()):
            out.update(parsed)
    return out

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline-summary', type=Path, default=Path('results/phase8b/ooc_report_summary.json'))
    ap.add_argument('--optimized-util', type=Path, default=Path('results/phase9a/skag_mem_bram_utilization.rpt'))
    ap.add_argument('--vivado-log', type=Path, default=Path('results/phase9a/vivado_skag_bram_ooc.log'))
    ap.add_argument('--out-json', type=Path, default=Path('results/phase9a/skag_bram_compare.json'))
    ap.add_argument('--out-md', type=Path, default=Path('results/phase9a/skag_bram_compare.md'))
    args = ap.parse_args()
    baseline = load_baseline(args.baseline_summary)
    optimized = parse_utilization_report(args.optimized_util)
    log_payload = parse_vivado_log(args.vivado_log)
    if log_payload['metrics']['BRAM_total_equiv18'] or log_payload['metrics']['LUTRAM_prims'] or log_payload['metrics']['DSP']:
        for k, v in log_payload['metrics'].items():
            optimized[k] = max(int(optimized.get(k, 0)), int(v))
    block_keys = set(log_payload['mapping']['block'].keys())
    dist_keys = set(log_payload['mapping']['distributed'].keys())
    required_raw_banks = {'qber_mem_reg', 'arrival_mem_reg', 'fidelity_mem_reg', 'key_mem_reg'}
    full_bram = required_raw_banks.issubset(block_keys) and required_raw_banks.isdisjoint(dist_keys)
    comparison = {
        'baseline_skag_mem': baseline,
        'optimized_skag_mem_bram': optimized,
        'memory_mapping': log_payload['mapping'],
        'delta': {
            'BRAM_total_equiv18': optimized.get('BRAM_total_equiv18',0)-baseline.get('BRAM_total_equiv18',0),
            'DSP': optimized.get('DSP',0)-baseline.get('DSP',0),
            'LUT': optimized.get('LUT',0)-baseline.get('LUT',0),
            'FF': optimized.get('FF',0)-baseline.get('FF',0),
            'LUTRAM_prims': optimized.get('LUTRAM_prims',0)-baseline.get('LUTRAM_prims',0),
        },
        'bram_inference_improved': optimized.get('BRAM_total_equiv18',0) > baseline.get('BRAM_total_equiv18',0),
        'edge_memory_full_bram': full_bram,
        'notes': [
            'Baseline values come from Step 8B OOC summary/report for skag_mem.',
            'Optimized values come from Step 9A OOC synthesis of skag_mem_bram.',
            'This revision removes the stored weight RAM and recomputes GA-read weight from raw field banks.',
            'Full success requires qber, arrival, fidelity, and key banks to infer BRAM with no raw-field bank left in LUTRAM.'
        ]
    }
    args.out_json.write_text(json.dumps(comparison, indent=2))
    md = [
        '# SKAG BRAM Optimization Comparison','',
        '## Baseline `skag_mem`',
        f"- BRAM (18K equivalent): {baseline.get('BRAM_total_equiv18',0)}",
        f"- DSP: {baseline.get('DSP',0)}",
        f"- LUT: {baseline.get('LUT','n/a')}",
        f"- FF: {baseline.get('FF','n/a')}",'',
        '## Optimized `skag_mem_bram`',
        f"- BRAM (18K equivalent): {optimized.get('BRAM_total_equiv18',0)}",
        f"- DSP: {optimized.get('DSP',0)}",
        f"- LUT: {optimized.get('LUT',0)}",
        f"- FF: {optimized.get('FF',0)}",
        f"- LUTRAM primitives: {optimized.get('LUTRAM_prims',0)}",'',
        '## Memory mapping',
        f"- Block RAM mapped objects: {', '.join(sorted(block_keys)) or 'none'}",
        f"- Distributed RAM mapped objects: {', '.join(sorted(log_payload['mapping']['distributed'].keys())) or 'none'}",'',
        '## Delta (optimized - baseline)',
        f"- BRAM (18K equivalent): {comparison['delta']['BRAM_total_equiv18']}",
        f"- DSP: {comparison['delta']['DSP']}",
        f"- LUT: {comparison['delta']['LUT']}",
        f"- FF: {comparison['delta']['FF']}",
        f"- LUTRAM primitives: {comparison['delta']['LUTRAM_prims']}",'',
        f"**BRAM inference improved:** `{comparison['bram_inference_improved']}`",
        f"**Edge memory fully in BRAM:** `{comparison['edge_memory_full_bram']}`",
    ]
    args.out_md.write_text('\n'.join(md) + '\n')
    print(f'Wrote {args.out_json}')
    print(f'Wrote {args.out_md}')

if __name__ == '__main__':
    main()
