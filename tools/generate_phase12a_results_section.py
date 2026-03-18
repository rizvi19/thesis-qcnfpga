#!/usr/bin/env python3
"""
Generate thesis-ready results section drafts from packaged phase11a and phase11b summaries.

Inputs:
- results/phase11a/qflow_thesis_packaging_summary.json
- results/phase11b/qflow_eval_story_after10d.json

Outputs:
- results/phase12a/qflow_thesis_results_section.md
- results/phase12a/qflow_thesis_results_section.tex
- results/phase12a/qflow_results_tables.csv
- results/phase12a/qflow_results_highlights.json
"""
from __future__ import annotations
import csv, json
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
PH11A = REPO_ROOT / 'results' / 'phase11a' / 'qflow_thesis_packaging_summary.json'
PH11B = REPO_ROOT / 'results' / 'phase11b' / 'qflow_eval_story_after10d.json'
OUT = REPO_ROOT / 'results' / 'phase12a'


def load_json(path: Path) -> Dict[str, Any]:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def fmt(x: Any, nd: int = 3) -> str:
    if x is None:
        return '-'
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def find_timing_table(p11a: Dict[str, Any]) -> List[Dict[str, Any]]:
    # tolerate multiple key names from previous summarizer styles
    for key in [
        'timing_progression', 'timing_closure_progression', 'timing_comparison_table',
        'timing_rows', 'timing_table', 'timing_summary_rows'
    ]:
        val = p11a.get(key)
        if isinstance(val, list) and val:
            return val
    # fallback from headline blocks
    rows = []
    for name in ['tc3', 'tc4', 'tc5', 'ooc_post_route']:
        block = p11a.get(name) or p11a.get('timing', {}).get(name)
        if isinstance(block, dict):
            row = {'version': name}
            row.update(block)
            rows.append(row)
    return rows


def normalize_timing_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for r in rows:
        out.append({
            'version': r.get('version') or r.get('label') or r.get('stage') or r.get('name'),
            'wns_ns': r.get('wns_ns', r.get('WNS_ns', r.get('wns'))),
            'tns_ns': r.get('tns_ns', r.get('TNS_ns', r.get('tns'))),
            'fmax_mhz': r.get('approx_fmax_mhz', r.get('fmax_mhz', r.get('approx_Fmax_MHz'))),
            'data_path_delay_ns': r.get('data_path_delay_ns', r.get('delay_ns', r.get('data_path_delay'))),
            'interpretation': r.get('interpretation', r.get('comment', '')),
        })
    # stable order if present
    order = {'tc3': 0, 'tc4': 1, 'tc5': 2, 'ooc_post_route': 3, 'ooc': 3}
    out.sort(key=lambda r: order.get(str(r['version']).lower(), 99))
    return out


def collect_eval_rows(p11b: Dict[str, Any]) -> List[Dict[str, Any]]:
    return p11b.get('adopted_recommendations_by_profile_topology', [])


def write_csv(timing_rows: List[Dict[str, Any]], eval_rows: List[Dict[str, Any]]) -> None:
    with (OUT / 'qflow_results_tables.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['SECTION', 'version/profile', 'topology', 'wns_ns', 'tns_ns', 'fmax_mhz', 'data_path_delay_ns',
                         'recommended_ga_variant', 'latency_delta_ga_minus_keyaware', 'fidelity_delta_ga_minus_keyaware',
                         'load_balance_delta_ga_minus_keyaware'])
        for r in timing_rows:
            writer.writerow(['timing', r['version'], '', r['wns_ns'], r['tns_ns'], r['fmax_mhz'], r['data_path_delay_ns'], '', '', '', ''])
        for r in eval_rows:
            writer.writerow(['evaluation', r['profile'], r['topology'], '', '', '', '', r['recommended_ga_variant'],
                             r['latency_delta_ga_minus_keyaware'], r['fidelity_delta_ga_minus_keyaware'], r['load_balance_delta_ga_minus_keyaware']])


def best_eval_takeaways(eval_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    default_count = sum(1 for r in eval_rows if r['recommended_ga_variant'] == 'ga_tcheby_pick_default')
    all_count = len(eval_rows)
    biggest_balance = min(eval_rows, key=lambda r: r['load_balance_delta_ga_minus_keyaware']) if eval_rows else None
    best_latency = min(eval_rows, key=lambda r: r['latency_delta_ga_minus_keyaware']) if eval_rows else None
    best_fidelity = max(eval_rows, key=lambda r: r['fidelity_delta_ga_minus_keyaware']) if eval_rows else None
    return {
        'default_variant_recommended_count': default_count,
        'evaluation_cases': all_count,
        'global_recommended_variant': 'ga_tcheby_pick_default' if default_count >= max(1, all_count-1) else 'mixed',
        'largest_balance_improvement_case': biggest_balance,
        'best_latency_case': best_latency,
        'best_fidelity_case': best_fidelity,
    }


def build_markdown(timing_rows: List[Dict[str, Any]], eval_rows: List[Dict[str, Any]], takeaways: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append('# QFlow Thesis Results Section Draft\n\n')
    lines.append('## 1. Implementation and Timing-Closure Results\n\n')
    lines.append(
        'The integrated QFlow core was refined through successive timing-closure iterations. '
        'In the tc3 baseline, the dominant bottleneck remained inside SKAG and the design failed the 10 ns target by a large margin. '
        'After restructuring the SKAG datapath in tc4, the worst path shifted into FDPE, indicating that the primary SKAG bottleneck had been sufficiently reduced. '
        'The final tc5 revision re-pipelined FDPE and achieved positive setup slack at the 10 ns target. '
        'This timing result was then corroborated by out-of-context (OOC) post-route implementation, which also reported positive setup and hold slack.\n\n'
    )
    lines.append('| version | WNS (ns) | TNS (ns) | approx. Fmax (MHz) | data path delay (ns) | interpretation |\n')
    lines.append('|---|---:|---:|---:|---:|---|\n')
    for r in timing_rows:
        lines.append(f"| {r['version']} | {fmt(r['wns_ns'],3)} | {fmt(r['tns_ns'],3)} | {fmt(r['fmax_mhz'],3)} | {fmt(r['data_path_delay_ns'],3)} | {r['interpretation'] or '-'} |\n")
    lines.append('\n')
    lines.append(
        'The most important engineering narrative is therefore: **SKAG bottleneck in tc3 → SKAG repair in tc4 → FDPE bottleneck exposed in tc4 → FDPE pipelining in tc5 → timing closure at 100 MHz class**. '
        'This is the correct interpretation of the closure history and should be used consistently in the thesis.\n\n'
    )
    lines.append('## 2. Evaluation and Baseline Comparison\n\n')
    lines.append(
        'The baseline evaluation progressed in two stages. First, the earlier software PMO-GA evaluation appeared to collapse to the key-aware shortest-path baseline. '
        'A focused follow-up study then showed that this collapse was substantially influenced by the **final-answer selection policy**. '
        'When the Pareto-front candidate was selected using weighted Tchebycheff scoring rather than a latency-first rule, PMO-GA began to separate from the key-aware heuristic on a meaningful subset of cases.\n\n'
    )
    lines.append('| profile | topology | recommended GA variant | Δ latency (GA - key-aware) | Δ fidelity (GA - key-aware) | Δ load-balance (GA - key-aware) |\n')
    lines.append('|---|---|---|---:|---:|---:|\n')
    for r in eval_rows:
        lines.append(
            f"| {r['profile']} | {r['topology']} | {r['recommended_ga_variant']} | {fmt(r['latency_delta_ga_minus_keyaware'],6)} | {fmt(r['fidelity_delta_ga_minus_keyaware'],6)} | {fmt(r['load_balance_delta_ga_minus_keyaware'],6)} |\n"
        )
    lines.append('\n')
    lines.append(
        'Across the current sweep, **ga_tcheby_pick_default** is the best overall software reference for the proposed PMO-GA. '
        'Its strongest observed benefit is generally improved load spreading, reflected by lower load-balance values than the key-aware baseline. '
        'In some current-like scenarios it also yields small fidelity improvements, although these gains are not universal. '
        'Accordingly, the honest claim is **tradeoff-aware separation**, not universal domination over the key-aware shortest-path heuristic.\n\n'
    )
    lines.append('## 3. Thesis-Safe Takeaways\n\n')
    lines.append('- The hardware timing result is strong: tc5 met the 10 ns target at post-synthesis and OOC post-route.\n')
    lines.append('- The strongest classical comparator is the key-aware shortest-path baseline, not the random-path baseline.\n')
    lines.append('- PMO-GA should be represented in software using **ga_tcheby_pick_default** for the thesis narrative.\n')
    lines.append('- The current evaluation supports **multi-objective tradeoff benefits**, especially better balance, but does not support a claim of universal superiority on every metric.\n')
    lines.append('- Hardware deployment should still be described as **post-synthesis and OOC post-route validated**, not as a completed full board demonstration.\n')
    return ''.join(lines)


def build_tex(timing_rows: List[Dict[str, Any]], eval_rows: List[Dict[str, Any]]) -> str:
    def esc(s: str) -> str:
        return s.replace('_', '\\_')
    lines: List[str] = []
    lines.append('% QFlow thesis-ready results section draft\n')
    lines.append('\\subsection{Implementation and Timing-Closure Results}\n')
    lines.append(
        'The integrated QFlow core was refined through successive timing-closure iterations. '
        'In the tc3 baseline, the dominant bottleneck remained inside SKAG and the design failed the 10~ns target by a large margin. '
        'After restructuring the SKAG datapath in tc4, the worst path shifted into FDPE, indicating that the primary SKAG bottleneck had been sufficiently reduced. '
        'The final tc5 revision re-pipelined FDPE and achieved positive setup slack at the 10~ns target. '
        'This result was corroborated by out-of-context (OOC) post-route implementation, which also reported positive setup and hold slack.\n\n'
    )
    lines.append('\\begin{table}[t]\n\\centering\n\\caption{QFlow timing-closure progression.}\n')
    lines.append('\\begin{tabular}{lrrrrl}\n\\hline\n')
    lines.append('Version & WNS (ns) & TNS (ns) & Fmax (MHz) & Delay (ns) & Interpretation \\\\ \n\\hline\n')
    for r in timing_rows:
        lines.append(f"{esc(str(r['version']))} & {fmt(r['wns_ns'],3)} & {fmt(r['tns_ns'],3)} & {fmt(r['fmax_mhz'],3)} & {fmt(r['data_path_delay_ns'],3)} & {esc(str(r['interpretation'] or '-'))} \\\\ \n")
    lines.append('\\hline\n\\end{tabular}\n\\end{table}\n\n')
    lines.append('\\subsection{Evaluation and Baseline Comparison}\n')
    lines.append(
        'The earlier software PMO-GA evaluation appeared to collapse to the key-aware shortest-path baseline. '
        'A focused follow-up study showed that this collapse was substantially influenced by the final-answer selection policy. '
        'When the Pareto-front member was selected using weighted Tchebycheff scoring rather than a latency-first rule, PMO-GA separated from the key-aware heuristic on a meaningful subset of cases. '
        'The most thesis-faithful software reference is therefore \\texttt{ga\\_tcheby\\_pick\\_default}.\n\n'
    )
    lines.append('\\begin{table}[t]\n\\centering\n\\caption{Recommended PMO-GA variant and tradeoff against the key-aware baseline.}\n')
    lines.append('\\begin{tabular}{llrrr}\n\\hline\n')
    lines.append('Profile/Topology & Variant & $\\Delta$Lat. & $\\Delta$Fid. & $\\Delta$Bal. \\\\ \n\\hline\n')
    for r in eval_rows:
        prof_top = esc(f"{r['profile']}/{r['topology']}")
        lines.append(f"{prof_top} & {esc(r['recommended_ga_variant'])} & {fmt(r['latency_delta_ga_minus_keyaware'],6)} & {fmt(r['fidelity_delta_ga_minus_keyaware'],6)} & {fmt(r['load_balance_delta_ga_minus_keyaware'],6)} \\\\ \n")
    lines.append('\\hline\n\\end{tabular}\n\\end{table}\n\n')
    lines.append(
        'The strongest observed PMO-GA benefit is generally lower load-balance, i.e., better load spreading, sometimes with only a very small latency penalty and occasionally with a small fidelity gain. '
        'Accordingly, the correct claim is tradeoff-aware separation rather than universal domination over the key-aware shortest-path heuristic.\n'
    )
    return ''.join(lines)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    p11a = load_json(PH11A)
    p11b = load_json(PH11B)

    timing_rows = normalize_timing_rows(find_timing_table(p11a))
    eval_rows = collect_eval_rows(p11b)
    takeaways = best_eval_takeaways(eval_rows)

    md = build_markdown(timing_rows, eval_rows, takeaways)
    tex = build_tex(timing_rows, eval_rows)

    (OUT / 'qflow_thesis_results_section.md').write_text(md, encoding='utf-8')
    (OUT / 'qflow_thesis_results_section.tex').write_text(tex, encoding='utf-8')
    write_csv(timing_rows, eval_rows)
    with (OUT / 'qflow_results_highlights.json').open('w', encoding='utf-8') as f:
        json.dump(takeaways, f, indent=2)

    print(f'Wrote {OUT / "qflow_thesis_results_section.md"}')
    print(f'Wrote {OUT / "qflow_thesis_results_section.tex"}')
    print(f'Wrote {OUT / "qflow_results_tables.csv"}')
    print(f'Wrote {OUT / "qflow_results_highlights.json"}')


if __name__ == '__main__':
    main()
