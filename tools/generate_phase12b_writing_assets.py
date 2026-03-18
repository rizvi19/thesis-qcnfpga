#!/usr/bin/env python3
"""
Phase 12B: Generate polished writing assets from packaged QFlow results.

Reads:
- results/phase11a/qflow_thesis_packaging_summary.json
- results/phase11b/qflow_eval_story_after10d.json
- results/phase12a/qflow_results_highlights.json

Writes:
- results/phase12b/qflow_thesis_results_polished.md
- results/phase12b/qflow_thesis_results_polished.tex
- results/phase12b/qflow_paper_results_condensed.md
- results/phase12b/qflow_paper_results_condensed.tex
- results/phase12b/qflow_defense_results_bullets.md
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "results" / "phase12b"

PH11A = REPO_ROOT / "results" / "phase11a" / "qflow_thesis_packaging_summary.json"
PH11B = REPO_ROOT / "results" / "phase11b" / "qflow_eval_story_after10d.json"
PH12A = REPO_ROOT / "results" / "phase12a" / "qflow_results_highlights.json"

def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def tex_escape(s: str) -> str:
    repl = {
        '\\': r'\textbackslash{}',
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
    }
    out = s
    for k, v in repl.items():
        out = out.replace(k, v)
    return out

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    p11a = load_json(PH11A)
    p11b = load_json(PH11B)
    p12a = load_json(PH12A)

    global_variant = p12a["global_recommended_variant"]
    best_latency = p12a["best_latency_case"]
    best_fidelity = p12a["best_fidelity_case"]
    best_balance = p12a["largest_balance_improvement_case"]
    eval_cases = p12a["evaluation_cases"]

    timing = p11a.get("timing_summary", {})
    versions = p11a.get("timing_versions", [])
    def row(name):
        for r in versions:
            if r.get("version") == name:
                return r
        return {}

    tc3 = row("tc3")
    tc4 = row("tc4")
    tc5 = row("tc5")
    ooc = row("tc5_ooc_impl")

    thesis_md = f"""# Polished Thesis Results Subsection

## Implementation and Timing-Closure Results

The integrated QFlow core was closed through a staged timing-closure process rather than a single monolithic optimization pass. In the early integrated baseline ({tc3.get('version','tc3')}), the dominant critical path was still concentrated in the SKAG update datapath, and the design missed the 10 ns requirement by a large margin. After restructuring and deepening the SKAG pipeline in {tc4.get('version','tc4')}, the worst path migrated from SKAG into FDPE. This shift was important because it showed that the original SKAG bottleneck had been reduced sufficiently for FDPE to become the next limiting stage. The final {tc5.get('version','tc5')} revision then re-pipelined FDPE and achieved positive setup slack at the 10 ns target, reaching approximately {tc5.get('approx_fmax_mhz', 0):.3f} MHz at post-synthesis. This result was subsequently corroborated by out-of-context post-route implementation, which also reported positive setup and hold slack and an approximate post-route frequency of {ooc.get('approx_fmax_mhz', 0):.3f} MHz.

Accordingly, the correct engineering narrative for the integrated core is: **SKAG bottleneck in tc3 → SKAG repair in tc4 → FDPE bottleneck exposed in tc4 → FDPE pipelining in tc5 → 100 MHz-class timing closure at post-synthesis and OOC post-route**. This is the thesis-safe interpretation of the closure history. It should also be emphasized that the implementation claim is an **OOC post-route validation of the core**, not a completed full board-level deployment.

## Baseline Evaluation Results

The baseline study shows that the strongest classical comparator is the **key-aware shortest-path heuristic**, not the random-path baseline. Earlier software evaluation suggested that the PMO-GA reference collapsed to the key-aware baseline; however, the follow-up selection-policy study showed that this behavior was substantially influenced by a latency-first final-answer rule. Once the final GA candidate was selected from the Pareto set using weighted Tchebycheff scoring, the software PMO-GA became distinct from the key-aware heuristic on a meaningful subset of the evaluated cases. Based on the current six-case evaluation sweep, the most appropriate software reference for the thesis is **{global_variant}**.

The main quality advantage observed for the Tchebycheff-selected PMO-GA is **improved load spreading**, reflected by lower load-balance values than the key-aware baseline in the strongest cases. The largest observed balance gain appeared in the **{best_balance['profile']} / {best_balance['topology']}** scenario, where the recommended GA variant changed the load-balance metric by {best_balance['load_balance_delta_ga_minus_keyaware']:.6f} relative to key-aware routing, while also slightly improving latency by {best_balance['latency_delta_ga_minus_keyaware']:.6f}. The strongest current fidelity-oriented case appeared in **{best_fidelity['profile']} / {best_fidelity['topology']}**, where the recommended GA variant improved fidelity by {best_fidelity['fidelity_delta_ga_minus_keyaware']:.6f}, albeit with a small latency penalty of {best_fidelity['latency_delta_ga_minus_keyaware']:.6f}. These results indicate that the honest claim is **tradeoff-aware separation**, not universal domination over the key-aware heuristic on every metric.

## Final Thesis-Safe Takeaways

1. The hardware result is strong: the final integrated core met the 10 ns target at both post-synthesis and OOC post-route.
2. The strongest algorithmic comparator is the key-aware shortest-path baseline, which must be treated as the main non-trivial reference in the thesis.
3. The most faithful software representation of the proposed PMO-GA is **{global_variant}**.
4. The current evidence supports **multi-objective tradeoff benefits**, especially improved balance and route spreading, but it does not support a claim that PMO-GA universally dominates key-aware routing on all metrics.
5. Board-level deployment language must remain precise: the present claim is **post-synthesis and OOC post-route validation of the core**, not a completed physical board demonstration.
"""

    thesis_tex = rf"""\subsection{{Implementation and Timing-Closure Results}}

The integrated QFlow core was closed through a staged timing-closure process rather than a single monolithic optimization pass. In the early integrated baseline ({tex_escape(tc3.get('version','tc3'))}), the dominant critical path was still concentrated in the SKAG update datapath, and the design missed the 10~ns requirement by a large margin. After restructuring and deepening the SKAG pipeline in {tex_escape(tc4.get('version','tc4'))}, the worst path migrated from SKAG into FDPE. This shift was important because it showed that the original SKAG bottleneck had been reduced sufficiently for FDPE to become the next limiting stage. The final {tex_escape(tc5.get('version','tc5'))} revision then re-pipelined FDPE and achieved positive setup slack at the 10~ns target, reaching approximately {tc5.get('approx_fmax_mhz', 0):.3f}~MHz at post-synthesis. This result was subsequently corroborated by out-of-context post-route implementation, which also reported positive setup and hold slack and an approximate post-route frequency of {ooc.get('approx_fmax_mhz', 0):.3f}~MHz.

Accordingly, the correct engineering narrative for the integrated core is: \textbf{{SKAG bottleneck in tc3 $\rightarrow$ SKAG repair in tc4 $\rightarrow$ FDPE bottleneck exposed in tc4 $\rightarrow$ FDPE pipelining in tc5 $\rightarrow$ 100~MHz-class timing closure at post-synthesis and OOC post-route}}. This is the thesis-safe interpretation of the closure history. It should also be emphasized that the implementation claim is an \textbf{{OOC post-route validation of the core}}, not a completed full board-level deployment.

\subsection{{Baseline Evaluation Results}}

The baseline study shows that the strongest classical comparator is the \textbf{{key-aware shortest-path heuristic}}, not the random-path baseline. Earlier software evaluation suggested that the PMO-GA reference collapsed to the key-aware baseline; however, the follow-up selection-policy study showed that this behavior was substantially influenced by a latency-first final-answer rule. Once the final GA candidate was selected from the Pareto set using weighted Tchebycheff scoring, the software PMO-GA became distinct from the key-aware heuristic on a meaningful subset of the evaluated cases. Based on the current {eval_cases}-case evaluation sweep, the most appropriate software reference for the thesis is \textbf{{{tex_escape(global_variant)}}}.

The main quality advantage observed for the Tchebycheff-selected PMO-GA is \textbf{{improved load spreading}}, reflected by lower load-balance values than the key-aware baseline in the strongest cases. The largest observed balance gain appeared in the \textbf{{{tex_escape(best_balance['profile'])} / {tex_escape(best_balance['topology'])}}} scenario, where the recommended GA variant changed the load-balance metric by {best_balance['load_balance_delta_ga_minus_keyaware']:.6f} relative to key-aware routing, while also slightly improving latency by {best_balance['latency_delta_ga_minus_keyaware']:.6f}. The strongest current fidelity-oriented case appeared in \textbf{{{tex_escape(best_fidelity['profile'])} / {tex_escape(best_fidelity['topology'])}}}, where the recommended GA variant improved fidelity by {best_fidelity['fidelity_delta_ga_minus_keyaware']:.6f}, albeit with a small latency penalty of {best_fidelity['latency_delta_ga_minus_keyaware']:.6f}. These results indicate that the honest claim is \textbf{{tradeoff-aware separation}}, not universal domination over the key-aware heuristic on every metric.

\subsection{{Final Thesis-Safe Takeaways}}

\begin{{enumerate}}
\item The hardware result is strong: the final integrated core met the 10~ns target at both post-synthesis and OOC post-route.
\item The strongest algorithmic comparator is the key-aware shortest-path baseline, which must be treated as the main non-trivial reference in the thesis.
\item The most faithful software representation of the proposed PMO-GA is \textbf{{{tex_escape(global_variant)}}}.
\item The current evidence supports \textbf{{multi-objective tradeoff benefits}}, especially improved balance and route spreading, but it does not support a claim that PMO-GA universally dominates key-aware routing on all metrics.
\item Board-level deployment language must remain precise: the present claim is \textbf{{post-synthesis and OOC post-route validation of the core}}, not a completed physical board demonstration.
\end{{enumerate}}
"""

    paper_md = f"""# Condensed Results for Paper Use

The final integrated QFlow core achieved timing closure at a 10 ns target after a staged optimization sequence in which the dominant bottleneck first resided in SKAG, then shifted to FDPE after SKAG repair, and was finally resolved by FDPE re-pipelining. The resulting tc5 design achieved approximately {tc5.get('approx_fmax_mhz', 0):.3f} MHz at post-synthesis, while OOC post-route implementation preserved positive setup and hold slack with an approximate frequency of {ooc.get('approx_fmax_mhz', 0):.3f} MHz.

For routing evaluation, the strongest non-trivial classical baseline was the key-aware shortest-path heuristic. A focused selection-policy study showed that an earlier collapse of the software PMO-GA reference to the key-aware heuristic was largely caused by latency-first final-answer selection. When the final candidate was instead chosen using weighted Tchebycheff scoring, PMO-GA became distinct from the key-aware baseline on a meaningful subset of the {eval_cases} evaluated cases. The recommended software PMO-GA variant is therefore **{global_variant}**.

The dominant PMO-GA advantage in the current study is improved balance and load spreading rather than universal wins on every metric. The strongest balance gain appeared in **{best_balance['profile']} / {best_balance['topology']}**, with a load-balance change of {best_balance['load_balance_delta_ga_minus_keyaware']:.6f} relative to the key-aware baseline. The strongest fidelity-oriented case appeared in **{best_fidelity['profile']} / {best_fidelity['topology']}**, where fidelity improved by {best_fidelity['fidelity_delta_ga_minus_keyaware']:.6f}. Accordingly, the honest claim is that QFlow supports **multi-objective tradeoff-aware routing with 100 MHz-class validated hardware closure**, rather than universal dominance over a strong key-aware heuristic.
"""

    paper_tex = rf"""The final integrated QFlow core achieved timing closure at a 10~ns target after a staged optimization sequence in which the dominant bottleneck first resided in SKAG, then shifted to FDPE after SKAG repair, and was finally resolved by FDPE re-pipelining. The resulting tc5 design achieved approximately {tc5.get('approx_fmax_mhz', 0):.3f}~MHz at post-synthesis, while OOC post-route implementation preserved positive setup and hold slack with an approximate frequency of {ooc.get('approx_fmax_mhz', 0):.3f}~MHz.

For routing evaluation, the strongest non-trivial classical baseline was the key-aware shortest-path heuristic. A focused selection-policy study showed that an earlier collapse of the software PMO-GA reference to the key-aware heuristic was largely caused by latency-first final-answer selection. When the final candidate was instead chosen using weighted Tchebycheff scoring, PMO-GA became distinct from the key-aware baseline on a meaningful subset of the {eval_cases} evaluated cases. The recommended software PMO-GA variant is therefore \textbf{{{tex_escape(global_variant)}}}.

The dominant PMO-GA advantage in the current study is improved balance and load spreading rather than universal wins on every metric. The strongest balance gain appeared in \textbf{{{tex_escape(best_balance['profile'])} / {tex_escape(best_balance['topology'])}}}, with a load-balance change of {best_balance['load_balance_delta_ga_minus_keyaware']:.6f} relative to the key-aware baseline. The strongest fidelity-oriented case appeared in \textbf{{{tex_escape(best_fidelity['profile'])} / {tex_escape(best_fidelity['topology'])}}}, where fidelity improved by {best_fidelity['fidelity_delta_ga_minus_keyaware']:.6f}. Accordingly, the honest claim is that QFlow supports \textbf{{multi-objective tradeoff-aware routing with 100~MHz-class validated hardware closure}}, rather than universal dominance over a strong key-aware heuristic.
"""

    defense_md = f"""# Defense Results Bullets

## Slide: Hardware Closure
- Integrated core closed through staged bottleneck migration: SKAG first, then FDPE.
- tc5 achieved approximately {tc5.get('approx_fmax_mhz', 0):.3f} MHz at post-synthesis.
- OOC post-route preserved timing closure at approximately {ooc.get('approx_fmax_mhz', 0):.3f} MHz.
- Claim carefully limited to **post-synthesis + OOC post-route validated core**, not full board demo.

## Slide: Evaluation Headline
- Strongest classical baseline: **key-aware shortest path**.
- Random valid path is only a weak sanity-check baseline.
- Recommended software PMO-GA thesis variant: **{global_variant}**.

## Slide: What Changed After Selection-Policy Study
- Earlier PMO-GA collapse was strongly influenced by latency-first final selection.
- Weighted Tchebycheff selection made PMO-GA separate from key-aware on a meaningful subset of cases.
- Honest win: **better tradeoff handling**, especially balance / load spreading.

## Slide: Best Current Quantitative Cases
- Best balance case: {best_balance['profile']} / {best_balance['topology']}, load-balance delta = {best_balance['load_balance_delta_ga_minus_keyaware']:.6f}.
- Best fidelity case: {best_fidelity['profile']} / {best_fidelity['topology']}, fidelity delta = {best_fidelity['fidelity_delta_ga_minus_keyaware']:.6f}.
- Best latency-improvement case: {best_latency['profile']} / {best_latency['topology']}, latency delta = {best_latency['latency_delta_ga_minus_keyaware']:.6f}.

## Slide: Honest Takeaway
- QFlow hardware result is strong and thesis-worthy.
- Current evidence supports **multi-objective tradeoff benefits**, not universal dominance on every metric.
- Best paper-safe claim: **100 MHz-class validated QFlow core with tradeoff-aware routing benefits over simpler baselines**.
"""

    (OUT_DIR / "qflow_thesis_results_polished.md").write_text(thesis_md, encoding="utf-8")
    (OUT_DIR / "qflow_thesis_results_polished.tex").write_text(thesis_tex, encoding="utf-8")
    (OUT_DIR / "qflow_paper_results_condensed.md").write_text(paper_md, encoding="utf-8")
    (OUT_DIR / "qflow_paper_results_condensed.tex").write_text(paper_tex, encoding="utf-8")
    (OUT_DIR / "qflow_defense_results_bullets.md").write_text(defense_md, encoding="utf-8")

    print(f"Wrote {OUT_DIR / 'qflow_thesis_results_polished.md'}")
    print(f"Wrote {OUT_DIR / 'qflow_thesis_results_polished.tex'}")
    print(f"Wrote {OUT_DIR / 'qflow_paper_results_condensed.md'}")
    print(f"Wrote {OUT_DIR / 'qflow_paper_results_condensed.tex'}")
    print(f"Wrote {OUT_DIR / 'qflow_defense_results_bullets.md'}")

if __name__ == "__main__":
    main()
