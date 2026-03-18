#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
for _p in (SCRIPT_DIR, REPO_ROOT, Path.cwd()):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

from evaluate_qflow_baselines_phase10b import (  # type: ignore
    REQUEST_SUITES,
    apply_path_consumption,
    build_topology,
    dijkstra_path,
    evaluate_path,
    finite_mean,
    simulate_key_dynamics,
)
from reference_model import MultiObjectiveGA

DEFAULT_ALPHAS = (1.0, 1.5, 0.5, 2.0)

STRESS_PROFILES: List[Dict[str, object]] = [
    {
        "name": "current_like",
        "sim_duration_s": 0.5,
        "tick_dt_s": 0.001,
        "f_min": 0.90,
        "request_multiplier": 1,
    },
    {
        "name": "depletion_plus_stricter_fidelity",
        "sim_duration_s": 1.0,
        "tick_dt_s": 0.001,
        "f_min": 0.92,
        "request_multiplier": 2,
    },
]

GA_VARIANTS: List[Dict[str, object]] = [
    {
        "baseline": "ga_latency_pick_default",
        "obj_weights": (0.4, 0.4, 0.2),
        "selection_mode": "latency",
    },
    {
        "baseline": "ga_tcheby_pick_default",
        "obj_weights": (0.4, 0.4, 0.2),
        "selection_mode": "tcheby",
    },
    {
        "baseline": "ga_tcheby_pick_fidelityheavy",
        "obj_weights": (0.25, 0.55, 0.20),
        "selection_mode": "tcheby",
    },
]

BASELINES = ["dijkstra_keyaware"] + [cfg["baseline"] for cfg in GA_VARIANTS]


def z95_halfwidth(values: Sequence[float]) -> float | None:
    vals = [float(v) for v in values if math.isfinite(float(v))]
    if len(vals) < 2:
        return None
    return 1.96 * statistics.stdev(vals) / math.sqrt(len(vals))


def fmt(x: object, digits: int = 6) -> str:
    if x is None:
        return "-"
    if isinstance(x, float):
        if math.isinf(x):
            return "inf"
        return f"{x:.{digits}f}"
    return str(x)


def expanded_requests(topo_name: str, multiplier: int) -> List[Tuple[int, int, int]]:
    base = REQUEST_SUITES[topo_name]
    reqs: List[Tuple[int, int, int]] = []
    for _ in range(multiplier):
        reqs.extend(base)
    return reqs


def choose_best_pareto_path(
    pareto: Sequence[object],
    ga: MultiObjectiveGA,
    selection_mode: str,
) -> Tuple[List[int], Dict[str, object]]:
    feasible = [c for c in pareto if getattr(c, "fitness", (float("inf"), 0.0, float("inf")))[0] < float("inf")]
    if not feasible:
        return [], {"pareto_front_size": len(pareto), "selection_mode": selection_mode, "best_tchebycheff": None}

    if selection_mode == "latency":
        best = min(
            feasible,
            key=lambda c: (
                float(c.fitness[0]),
                -float(c.fitness[1]),
                float(c.fitness[2]),
                len(c.path),
                tuple(c.path),
            ),
        )
        return list(best.path), {
            "pareto_front_size": len(feasible),
            "selection_mode": selection_mode,
            "best_tchebycheff": None,
        }

    if selection_mode != "tcheby":
        raise ValueError(f"Unsupported selection mode: {selection_mode}")

    z_ideal = (
        min(float(c.fitness[0]) for c in feasible),
        max(float(c.fitness[1]) for c in feasible),
        min(float(c.fitness[2]) for c in feasible),
    )
    score_rows = []
    for c in feasible:
        score = float(ga.tchebycheff_score(tuple(c.fitness), z_ideal))
        score_rows.append((score, float(c.fitness[0]), -float(c.fitness[1]), float(c.fitness[2]), len(c.path), tuple(c.path)))
    best_key = min(score_rows)
    best = min(
        feasible,
        key=lambda c: (
            float(ga.tchebycheff_score(tuple(c.fitness), z_ideal)),
            float(c.fitness[0]),
            -float(c.fitness[1]),
            float(c.fitness[2]),
            len(c.path),
            tuple(c.path),
        ),
    )
    return list(best.path), {
        "pareto_front_size": len(feasible),
        "selection_mode": selection_mode,
        "best_tchebycheff": best_key[0],
    }


def run_ga_variant(
    skag,
    src: int,
    dst: int,
    *,
    f_min: float,
    max_hops: int,
    seed: int,
    pop_size: int,
    max_generations: int,
    obj_weights: Tuple[float, float, float],
    selection_mode: str,
) -> Tuple[List[int], Dict[str, object]]:
    ga = MultiObjectiveGA(
        skag=skag,
        pop_size=pop_size,
        max_generations=max_generations,
        crossover_rate=0.8,
        mutation_rate=0.05,
        tournament_k=2,
        elite_count=4,
        max_hops=max_hops,
        f_min=f_min,
        stall_gens=10,
        stall_epsilon=1e-6,
        obj_weights=obj_weights,
        seed=seed,
    )
    pareto, convergence = ga.solve(src, dst, verbose=False)
    best_path, extra = choose_best_pareto_path(pareto, ga, selection_mode)
    extra.update(
        {
            "convergence_points": len(convergence),
            "obj_weights": list(obj_weights),
        }
    )
    return best_path, extra


def metric_mean(rows: Iterable[Dict[str, object]], key: str) -> float | None:
    vals = [float(r[key]) for r in rows if r.get("feasible") and r.get(key) is not None and math.isfinite(float(r[key]))]
    return finite_mean(vals)


def run_single_profile_topology(
    *,
    topo_name: str,
    profile: Dict[str, object],
    seed: int,
    ga_pop_size: int,
    ga_max_generations: int,
) -> Dict[str, object]:
    import copy

    sim_duration_s = float(profile["sim_duration_s"])
    tick_dt_s = float(profile["tick_dt_s"])
    f_min = float(profile["f_min"])
    request_multiplier = int(profile["request_multiplier"])

    base_skag = build_topology(topo_name, DEFAULT_ALPHAS)
    t_eval = simulate_key_dynamics(
        base_skag,
        sim_duration_s=sim_duration_s,
        tick_dt_s=tick_dt_s,
        f_min=f_min,
        seed=seed,
    )
    requests = expanded_requests(topo_name, request_multiplier)
    request_rows: List[Dict[str, object]] = []

    per_baseline_skag = {baseline: copy.deepcopy(base_skag) for baseline in BASELINES}

    for req_idx, (src, dst, max_hops) in enumerate(requests):
        for baseline_name in BASELINES:
            skag = per_baseline_skag[baseline_name]
            start = time.perf_counter()
            extra: Dict[str, object] = {}

            if baseline_name == "dijkstra_keyaware":
                path = dijkstra_path(
                    skag,
                    src,
                    dst,
                    edge_cost=lambda u, v: skag.edge_weight(u, v),
                    f_min=f_min,
                    require_feasible=True,
                )
            else:
                cfg = next(cfg for cfg in GA_VARIANTS if cfg["baseline"] == baseline_name)
                path, extra = run_ga_variant(
                    skag,
                    src,
                    dst,
                    f_min=f_min,
                    max_hops=max_hops,
                    seed=seed + 1009 * (req_idx + 1),
                    pop_size=ga_pop_size,
                    max_generations=ga_max_generations,
                    obj_weights=tuple(cfg["obj_weights"]),
                    selection_mode=str(cfg["selection_mode"]),
                )

            runtime_ms = (time.perf_counter() - start) * 1000.0
            metrics = evaluate_path(skag, path, f_min=f_min)
            row = {
                "profile": str(profile["name"]),
                "topology": topo_name,
                "seed": seed,
                "request_index": req_idx,
                "src": src,
                "dst": dst,
                "baseline": baseline_name,
                "runtime_ms": runtime_ms,
                **metrics,
                **extra,
            }
            request_rows.append(row)
            if metrics["feasible"]:
                apply_path_consumption(skag, path, t_now=t_eval)

    aggregate_rows: List[Dict[str, object]] = []
    for baseline_name in BASELINES:
        rows = [r for r in request_rows if r["baseline"] == baseline_name]
        feasible_rows = [r for r in rows if r["feasible"]]
        aggregate_rows.append(
            {
                "baseline": baseline_name,
                "request_count": len(rows),
                "feasible_count": len(feasible_rows),
                "avg_latency": metric_mean(feasible_rows, "latency"),
                "avg_bottleneck_fidelity": metric_mean(feasible_rows, "bottleneck_fidelity"),
                "avg_load_balance": metric_mean(feasible_rows, "load_balance"),
                "avg_distance_km": metric_mean(feasible_rows, "distance_km"),
                "avg_hops": metric_mean(feasible_rows, "hops"),
                "total_runtime_ms": finite_mean([sum(float(r["runtime_ms"]) for r in rows)]),
            }
        )

    return {
        "profile": str(profile["name"]),
        "topology": topo_name,
        "seed": seed,
        "config": {
            "sim_duration_s": sim_duration_s,
            "tick_dt_s": tick_dt_s,
            "f_min": f_min,
            "request_multiplier": request_multiplier,
        },
        "request_results": request_rows,
        "aggregate_baselines": aggregate_rows,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase 10D: bounded GA-selection-policy sweep for QFlow.")
    ap.add_argument("--topologies", nargs="+", default=["mesh9", "mesh16", "irregular12"], choices=["mesh9", "mesh16", "irregular12"])
    ap.add_argument("--seed-start", type=int, default=42)
    ap.add_argument("--repetitions", type=int, default=6)
    ap.add_argument("--ga-pop-size", type=int, default=64)
    ap.add_argument("--ga-max-generations", type=int, default=100)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-csv", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    all_request_rows: List[Dict[str, object]] = []
    all_aggregate_rows: List[Dict[str, object]] = []
    summary: Dict[str, object] = {
        "config": {
            "topologies": args.topologies,
            "seed_start": args.seed_start,
            "repetitions": args.repetitions,
            "ga_pop_size": args.ga_pop_size,
            "ga_max_generations": args.ga_max_generations,
            "profiles": STRESS_PROFILES,
            "ga_variants": GA_VARIANTS,
            "purpose": "Test whether PMO-GA collapses to key-aware shortest path because the final answer is selected by minimum latency instead of weighted Tchebycheff score.",
        },
        "profile_topology_summaries": [],
        "headline_findings": {},
    }

    for profile in STRESS_PROFILES:
        profile_name = str(profile["name"])
        for topo_name in args.topologies:
            run_summaries = []
            comparison_rows = []
            for rep in range(args.repetitions):
                seed = args.seed_start + rep
                run = run_single_profile_topology(
                    topo_name=topo_name,
                    profile=profile,
                    seed=seed,
                    ga_pop_size=args.ga_pop_size,
                    ga_max_generations=args.ga_max_generations,
                )
                run_summaries.append(run)
                all_request_rows.extend(run["request_results"])
                for agg in run["aggregate_baselines"]:
                    all_aggregate_rows.append({
                        "profile": profile_name,
                        "topology": topo_name,
                        "seed": seed,
                        **agg,
                    })

                # Compare each GA variant against key-aware request-by-request.
                by_req = {}
                for row in run["request_results"]:
                    by_req.setdefault(int(row["request_index"]), {})[str(row["baseline"])] = row
                for req_idx, bucket in sorted(by_req.items()):
                    key_row = bucket.get("dijkstra_keyaware")
                    if not key_row:
                        continue
                    for ga_variant in [cfg["baseline"] for cfg in GA_VARIANTS]:
                        ga_row = bucket.get(str(ga_variant))
                        if not ga_row:
                            continue
                        key_path = tuple(key_row.get("path", []))
                        ga_path = tuple(ga_row.get("path", []))
                        key_feasible = bool(key_row.get("feasible"))
                        ga_feasible = bool(ga_row.get("feasible"))
                        comparison_rows.append(
                            {
                                "profile": profile_name,
                                "topology": topo_name,
                                "seed": seed,
                                "request_index": req_idx,
                                "variant": ga_variant,
                                "ga_feasible": ga_feasible,
                                "key_feasible": key_feasible,
                                "same_path": bool(key_path == ga_path and ga_path),
                                "ga_lower_latency": bool(ga_feasible and key_feasible and float(ga_row["latency"]) < float(key_row["latency"]) - 1e-12),
                                "ga_higher_fidelity": bool(ga_feasible and key_feasible and float(ga_row["bottleneck_fidelity"]) > float(key_row["bottleneck_fidelity"]) + 1e-12),
                                "ga_lower_balance": bool(ga_feasible and key_feasible and float(ga_row["load_balance"]) < float(key_row["load_balance"]) - 1e-12),
                            }
                        )

            profile_topology_rows = [r for r in all_aggregate_rows if r["profile"] == profile_name and r["topology"] == topo_name]
            baseline_stats = []
            for baseline in BASELINES:
                rows = [r for r in profile_topology_rows if r["baseline"] == baseline]
                def vec(field: str) -> List[float]:
                    return [float(r[field]) for r in rows if r.get(field) is not None and math.isfinite(float(r[field]))]
                baseline_stats.append(
                    {
                        "baseline": baseline,
                        "runs": len(rows),
                        "mean_avg_latency": finite_mean(vec("avg_latency")),
                        "latency_ci95": z95_halfwidth(vec("avg_latency")),
                        "mean_avg_bottleneck_fidelity": finite_mean(vec("avg_bottleneck_fidelity")),
                        "fidelity_ci95": z95_halfwidth(vec("avg_bottleneck_fidelity")),
                        "mean_avg_load_balance": finite_mean(vec("avg_load_balance")),
                        "load_balance_ci95": z95_halfwidth(vec("avg_load_balance")),
                        "mean_total_runtime_ms": finite_mean(vec("total_runtime_ms")),
                        "runtime_ci95": z95_halfwidth(vec("total_runtime_ms")),
                    }
                )

            variant_comparisons = []
            for ga_variant in [cfg["baseline"] for cfg in GA_VARIANTS]:
                rows = [r for r in comparison_rows if r["variant"] == ga_variant]
                n = len(rows)
                same = sum(1 for r in rows if r["same_path"])
                lower_lat = sum(1 for r in rows if r["ga_lower_latency"])
                higher_fid = sum(1 for r in rows if r["ga_higher_fidelity"])
                lower_bal = sum(1 for r in rows if r["ga_lower_balance"])
                variant_comparisons.append(
                    {
                        "variant": ga_variant,
                        "request_instances": n,
                        "same_path_rate_vs_keyaware": (same / n) if n else None,
                        "ga_lower_latency_rate": (lower_lat / n) if n else None,
                        "ga_higher_fidelity_rate": (higher_fid / n) if n else None,
                        "ga_lower_balance_rate": (lower_bal / n) if n else None,
                    }
                )

            summary["profile_topology_summaries"].append(
                {
                    "profile": profile_name,
                    "topology": topo_name,
                    "baseline_stats": baseline_stats,
                    "variant_comparisons_vs_keyaware": variant_comparisons,
                }
            )

    # Headline: does any tcheby-picked variant separate from key-aware?
    tcheby_rows = [
        row
        for block in summary["profile_topology_summaries"]
        for row in block["variant_comparisons_vs_keyaware"]
        if "tcheby" in row["variant"]
    ]
    summary["headline_findings"] = {
        "max_tcheby_separation_rate": max(((1.0 - float(r["same_path_rate_vs_keyaware"])) for r in tcheby_rows if r["same_path_rate_vs_keyaware"] is not None), default=0.0),
        "best_tcheby_variant_by_fidelity_gain_rate": max(tcheby_rows, key=lambda r: float(r["ga_higher_fidelity_rate"] or 0.0), default=None),
        "best_tcheby_variant_by_balance_gain_rate": max(tcheby_rows, key=lambda r: float(r["ga_lower_balance_rate"] or 0.0), default=None),
        "interpretation": "If tcheby-picked GA separates from key-aware here, the collapse seen in Phase 10C was largely a final-answer selection-policy issue. If it still matches key-aware, then the current topology/request suite truly does not induce enough multi-objective conflict.",
    }

    out_json = Path(args.out_json)
    out_csv = Path(args.out_csv)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    with out_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Flat CSV from baseline stats plus comparison rows.
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "section",
            "profile",
            "topology",
            "baseline_or_variant",
            "runs_or_instances",
            "mean_avg_latency",
            "latency_ci95",
            "mean_avg_bottleneck_fidelity",
            "fidelity_ci95",
            "mean_avg_load_balance",
            "load_balance_ci95",
            "mean_total_runtime_ms",
            "runtime_ci95",
            "same_path_rate_vs_keyaware",
            "ga_lower_latency_rate",
            "ga_higher_fidelity_rate",
            "ga_lower_balance_rate",
        ])
        for block in summary["profile_topology_summaries"]:
            for row in block["baseline_stats"]:
                writer.writerow([
                    "baseline_stats",
                    block["profile"],
                    block["topology"],
                    row["baseline"],
                    row["runs"],
                    row["mean_avg_latency"],
                    row["latency_ci95"],
                    row["mean_avg_bottleneck_fidelity"],
                    row["fidelity_ci95"],
                    row["mean_avg_load_balance"],
                    row["load_balance_ci95"],
                    row["mean_total_runtime_ms"],
                    row["runtime_ci95"],
                    None,
                    None,
                    None,
                    None,
                ])
            for row in block["variant_comparisons_vs_keyaware"]:
                writer.writerow([
                    "comparison_vs_keyaware",
                    block["profile"],
                    block["topology"],
                    row["variant"],
                    row["request_instances"],
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    row["same_path_rate_vs_keyaware"],
                    row["ga_lower_latency_rate"],
                    row["ga_higher_fidelity_rate"],
                    row["ga_lower_balance_rate"],
                ])

    lines: List[str] = []
    lines.append("# Phase 10D GA Selection-Policy Sweep")
    lines.append("")
    lines.append("## Why this exists")
    lines.append("")
    lines.append("Phase 10C showed software PMO-GA matching key-aware shortest path on the current suites.")
    lines.append("This sweep tests whether the collapse comes from how the final GA answer is selected: minimum latency from the Pareto front versus weighted Tchebycheff selection.")
    lines.append("")
    lines.append("## Configuration")
    lines.append("")
    lines.append(f"- topologies: {args.topologies}")
    lines.append(f"- repetitions: {args.repetitions}")
    lines.append(f"- ga_pop_size: {args.ga_pop_size}")
    lines.append(f"- ga_max_generations: {args.ga_max_generations}")
    lines.append(f"- profiles: {[p['name'] for p in STRESS_PROFILES]}")
    lines.append("")

    for block in summary["profile_topology_summaries"]:
        lines.append(f"## {block['profile']} / {block['topology']}")
        lines.append("")
        lines.append("### Aggregate baseline stats")
        lines.append("")
        lines.append("| baseline | runs | mean_avg_latency | latency_ci95 | mean_avg_bottleneck_fidelity | fidelity_ci95 | mean_avg_load_balance | load_balance_ci95 | mean_total_runtime_ms |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for row in block["baseline_stats"]:
            lines.append(
                f"| {row['baseline']} | {row['runs']} | {fmt(row['mean_avg_latency'])} | {fmt(row['latency_ci95'])} | {fmt(row['mean_avg_bottleneck_fidelity'])} | {fmt(row['fidelity_ci95'])} | {fmt(row['mean_avg_load_balance'])} | {fmt(row['load_balance_ci95'])} | {fmt(row['mean_total_runtime_ms'])} |"
            )
        lines.append("")
        lines.append("### GA variants vs key-aware")
        lines.append("")
        lines.append("| variant | request_instances | same_path_rate_vs_keyaware | ga_lower_latency_rate | ga_higher_fidelity_rate | ga_lower_balance_rate |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for row in block["variant_comparisons_vs_keyaware"]:
            lines.append(
                f"| {row['variant']} | {row['request_instances']} | {fmt(row['same_path_rate_vs_keyaware'])} | {fmt(row['ga_lower_latency_rate'])} | {fmt(row['ga_higher_fidelity_rate'])} | {fmt(row['ga_lower_balance_rate'])} |"
            )
        lines.append("")

    hf = summary["headline_findings"]
    lines.append("## Headline findings")
    lines.append("")
    lines.append(f"- max_tcheby_separation_rate: {fmt(hf['max_tcheby_separation_rate'])}")
    lines.append(f"- best_tcheby_variant_by_fidelity_gain_rate: {hf['best_tcheby_variant_by_fidelity_gain_rate']}")
    lines.append(f"- best_tcheby_variant_by_balance_gain_rate: {hf['best_tcheby_variant_by_balance_gain_rate']}")
    lines.append(f"- interpretation: {hf['interpretation']}")
    lines.append("")

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
