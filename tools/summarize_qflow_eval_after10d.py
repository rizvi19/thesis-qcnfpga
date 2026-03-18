#!/usr/bin/env python3
"""
Step 11B: Package the post-10D evaluation story for thesis writing.

Reads:
- results/phase10c/qflow_baseline_eval_phase10c_stats.json
- results/phase10d/qflow_baseline_eval_phase10d_selection_sweep.json
- results/phase11a/qflow_thesis_packaging_summary.json (optional)

Writes:
- results/phase11b/qflow_eval_story_after10d.json
- results/phase11b/qflow_eval_story_after10d.csv
- results/phase11b/qflow_eval_story_after10d.md
"""

from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE10C = REPO_ROOT / "results" / "phase10c" / "qflow_baseline_eval_phase10c_stats.json"
PHASE10D = REPO_ROOT / "results" / "phase10d" / "qflow_baseline_eval_phase10d_selection_sweep.json"
PHASE11A = REPO_ROOT / "results" / "phase11a" / "qflow_thesis_packaging_summary.json"
OUT_DIR = REPO_ROOT / "results" / "phase11b"

def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def fmt(x: Any, nd: int = 6) -> str:
    if x is None:
        return "-"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)

def pick_baseline(stats: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
    for s in stats:
        if s.get("baseline") == name:
            return s
    return None

def compare_pair(ga: Dict[str, Any], key: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "latency_delta_ga_minus_keyaware": ga["mean_avg_latency"] - key["mean_avg_latency"],
        "fidelity_delta_ga_minus_keyaware": ga["mean_avg_bottleneck_fidelity"] - key["mean_avg_bottleneck_fidelity"],
        "load_balance_delta_ga_minus_keyaware": ga["mean_avg_load_balance"] - key["mean_avg_load_balance"],
        "runtime_ratio_ga_over_keyaware": (
            ga["mean_total_runtime_ms"] / key["mean_total_runtime_ms"]
            if key["mean_total_runtime_ms"] > 0 else None
        ),
    }

def best_variant_for_topology(top_summary: Dict[str, Any]) -> Dict[str, Any]:
    stats = top_summary["baseline_stats"]
    key = pick_baseline(stats, "dijkstra_keyaware")
    candidates = [
        s for s in stats
        if s["baseline"] in ("ga_tcheby_pick_default", "ga_tcheby_pick_fidelityheavy")
    ]
    scored = []
    for c in candidates:
        cmp = compare_pair(c, key)
        # heuristic score: reward fidelity and lower balance, penalize latency
        score = (
            1.5 * cmp["fidelity_delta_ga_minus_keyaware"]
            - 1.0 * cmp["latency_delta_ga_minus_keyaware"]
            - 0.5 * cmp["load_balance_delta_ga_minus_keyaware"]
        )
        scored.append((score, c, cmp))
    scored.sort(key=lambda t: t[0], reverse=True)
    score, chosen, cmp = scored[0]
    return {
        "chosen_variant": chosen["baseline"],
        "heuristic_tradeoff_score": score,
        **cmp,
        "chosen_stats": chosen,
        "keyaware_stats": key,
    }

def extract_phase10c_story(p10c: Dict[str, Any]) -> Dict[str, Any]:
    # Read only the headline that PMO-GA matched key-aware on the old suite.
    summaries = p10c.get("profile_topology_summaries", [])
    exact_match_profiles = []
    for s in summaries:
        topo = s.get("topology")
        comp_list = s.get("variant_comparisons_vs_keyaware", [])
        for comp in comp_list:
            if comp.get("variant") == "software_pmo_ga":
                exact_match_profiles.append({
                    "topology": topo,
                    "same_path_rate_vs_keyaware": comp.get("same_path_rate_vs_keyaware"),
                })
    return {
        "software_pmo_ga_old_suite_matches_keyaware": exact_match_profiles
    }

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    p10c = load_json(PHASE10C) if PHASE10C.exists() else {}
    p10d = load_json(PHASE10D)
    p11a = load_json(PHASE11A) if PHASE11A.exists() else {}

    profile_summaries = p10d["profile_topology_summaries"]
    rows: List[Dict[str, Any]] = []
    adopted_recommendations: List[Dict[str, Any]] = []

    for s in profile_summaries:
        profile = s["profile"]
        topo = s["topology"]
        best = best_variant_for_topology(s)
        adopted_recommendations.append({
            "profile": profile,
            "topology": topo,
            "recommended_ga_variant": best["chosen_variant"],
            "latency_delta_ga_minus_keyaware": best["latency_delta_ga_minus_keyaware"],
            "fidelity_delta_ga_minus_keyaware": best["fidelity_delta_ga_minus_keyaware"],
            "load_balance_delta_ga_minus_keyaware": best["load_balance_delta_ga_minus_keyaware"],
            "runtime_ratio_ga_over_keyaware": best["runtime_ratio_ga_over_keyaware"],
        })

        stats = s["baseline_stats"]
        key = pick_baseline(stats, "dijkstra_keyaware")
        for ga_name in ("ga_tcheby_pick_default", "ga_tcheby_pick_fidelityheavy"):
            ga = pick_baseline(stats, ga_name)
            comp = compare_pair(ga, key)
            rows.append({
                "profile": profile,
                "topology": topo,
                "ga_variant": ga_name,
                **comp,
                "keyaware_latency": key["mean_avg_latency"],
                "ga_latency": ga["mean_avg_latency"],
                "keyaware_fidelity": key["mean_avg_bottleneck_fidelity"],
                "ga_fidelity": ga["mean_avg_bottleneck_fidelity"],
                "keyaware_load_balance": key["mean_avg_load_balance"],
                "ga_load_balance": ga["mean_avg_load_balance"],
            })

    # Global recommendation: count wins by simple criteria
    variant_counts = {}
    for rec in adopted_recommendations:
        v = rec["recommended_ga_variant"]
        variant_counts[v] = variant_counts.get(v, 0) + 1
    global_recommended = max(variant_counts.items(), key=lambda kv: kv[1])[0]

    summary = {
        "phase10c_context": extract_phase10c_story(p10c),
        "phase10d_headline_findings": p10d.get("headline_findings", {}),
        "adopted_recommendations_by_profile_topology": adopted_recommendations,
        "global_recommended_software_ga_variant_for_thesis": global_recommended,
        "thesis_safe_interpretation": {
            "core_message": (
                "The earlier PMO-GA collapse was substantially influenced by latency-first final-answer selection. "
                "When the GA output is selected with weighted Tchebycheff scoring, it separates from key-aware shortest path "
                "on a meaningful subset of request instances, typically trading a small latency change for improved balance "
                "and occasionally improved fidelity."
            ),
            "do_say": [
                "Tchebycheff-picked PMO-GA provides a more faithful software reference to the intended multi-objective formulation.",
                "Selection policy materially affects whether PMO-GA appears distinct from the key-aware heuristic.",
                "The strongest observed GA advantage is usually lower load-balance (better spreading), not dominant wins on every metric."
            ],
            "do_not_say": [
                "PMO-GA universally dominates key-aware shortest path.",
                "Every tested scenario shows better fidelity and lower latency simultaneously.",
                "Hardware board deployment has already been demonstrated."
            ]
        },
        "phase11a_present": PHASE11A.exists(),
    }

    with (OUT_DIR / "qflow_eval_story_after10d.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    with (OUT_DIR / "qflow_eval_story_after10d.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # markdown
    md = []
    md.append("# QFlow Evaluation Story After Phase 10D\n")
    md.append("## Decision\n")
    md.append(
        f"- Recommended software PMO-GA thesis variant: **{global_recommended}**\n"
        "- Reason: it is the most thesis-faithful multi-objective selector across the current Phase 10D sweep.\n"
    )

    md.append("\n## Why this matters\n")
    md.append(
        "- Phase 10C showed the old software PMO-GA evaluation collapsing to the key-aware shortest-path baseline on the prior suite.\n"
        "- Phase 10D shows that this collapse was substantially influenced by **final-answer selection policy**.\n"
        "- Once the Pareto-front member is chosen with **weighted Tchebycheff selection**, PMO-GA separates from the key-aware baseline on a meaningful subset of cases.\n"
    )

    md.append("\n## Recommendation by profile/topology\n")
    md.append("| profile | topology | recommended_ga_variant | Δ latency (GA-keyaware) | Δ fidelity (GA-keyaware) | Δ load_balance (GA-keyaware) |\n")
    md.append("|---|---|---|---:|---:|---:|\n")
    for rec in adopted_recommendations:
        md.append(
            f"| {rec['profile']} | {rec['topology']} | {rec['recommended_ga_variant']} | "
            f"{rec['latency_delta_ga_minus_keyaware']:.6f} | "
            f"{rec['fidelity_delta_ga_minus_keyaware']:.6f} | "
            f"{rec['load_balance_delta_ga_minus_keyaware']:.6f} |\n"
        )

    md.append("\n## Detailed tradeoff table\n")
    md.append("| profile | topology | ga_variant | keyaware_latency | ga_latency | Δ latency | keyaware_fidelity | ga_fidelity | Δ fidelity | keyaware_load_balance | ga_load_balance | Δ load_balance |\n")
    md.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    for r in rows:
        md.append(
            f"| {r['profile']} | {r['topology']} | {r['ga_variant']} | "
            f"{r['keyaware_latency']:.6f} | {r['ga_latency']:.6f} | {r['latency_delta_ga_minus_keyaware']:.6f} | "
            f"{r['keyaware_fidelity']:.6f} | {r['ga_fidelity']:.6f} | {r['fidelity_delta_ga_minus_keyaware']:.6f} | "
            f"{r['keyaware_load_balance']:.6f} | {r['ga_load_balance']:.6f} | {r['load_balance_delta_ga_minus_keyaware']:.6f} |\n"
        )

    md.append("\n## Thesis-safe interpretation\n")
    md.append(
        "- The strongest observed PMO-GA benefit is usually **better load spreading / lower load-balance metric**, sometimes with a very small latency penalty.\n"
        "- Fidelity improvements exist in some current-like cases, but they are not universal.\n"
        "- Therefore the honest claim is **tradeoff-aware separation**, not universal domination.\n"
    )

    with (OUT_DIR / "qflow_eval_story_after10d.md").open("w", encoding="utf-8") as f:
        f.write("".join(md))

    print(f"Wrote {OUT_DIR / 'qflow_eval_story_after10d.json'}")
    print(f"Wrote {OUT_DIR / 'qflow_eval_story_after10d.csv'}")
    print(f"Wrote {OUT_DIR / 'qflow_eval_story_after10d.md'}")

if __name__ == "__main__":
    main()
