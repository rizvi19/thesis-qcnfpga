#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
for _p in (SCRIPT_DIR, REPO_ROOT, Path.cwd()):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

# Reuse the already validated phase10b helpers.
from evaluate_qflow_baselines_phase10b import (  # type: ignore
    DEFAULT_ALPHAS,
    REQUEST_SUITES,
    apply_path_consumption,
    build_topology,
    count_wins,
    dijkstra_path,
    evaluate_path,
    finite_mean,
    random_valid_path,
    run_software_ga,
    simulate_key_dynamics,
)


BASELINES = [
    "dijkstra_distance",
    "dijkstra_keyaware",
    "random_valid_path",
    "software_pmo_ga",
]


def z95_halfwidth(values: List[float]) -> float | None:
    if len(values) < 2:
        return None
    stdev = statistics.stdev(values)
    return 1.96 * stdev / math.sqrt(len(values))


def run_single_eval(
    *,
    topo_name: str,
    seed: int,
    sim_duration_s: float,
    tick_dt_s: float,
    f_min: float,
    ga_pop_size: int,
    ga_max_generations: int,
) -> Dict[str, object]:
    import copy
    import time

    base_skag = build_topology(topo_name, DEFAULT_ALPHAS)
    t_eval = simulate_key_dynamics(
        base_skag,
        sim_duration_s=sim_duration_s,
        tick_dt_s=tick_dt_s,
        f_min=f_min,
        seed=seed,
    )
    requests = REQUEST_SUITES[topo_name]
    request_rows: List[Dict[str, object]] = []

    for baseline_name in BASELINES:
        skag = copy.deepcopy(base_skag)
        for req_idx, (src, dst, max_hops) in enumerate(requests):
            start = time.perf_counter()
            extra: Dict[str, object] = {}

            if baseline_name == "dijkstra_distance":
                path = dijkstra_path(
                    skag,
                    src,
                    dst,
                    edge_cost=lambda u, v: skag.link_params[(u, v)].distance_km,
                    f_min=f_min,
                    require_feasible=True,
                )
            elif baseline_name == "dijkstra_keyaware":
                path = dijkstra_path(
                    skag,
                    src,
                    dst,
                    edge_cost=lambda u, v: skag.edge_weight(u, v),
                    f_min=f_min,
                    require_feasible=True,
                )
            elif baseline_name == "random_valid_path":
                path = random_valid_path(
                    skag,
                    src,
                    dst,
                    f_min=f_min,
                    max_hops=max_hops,
                    seed=seed + 101 * (req_idx + 1),
                )
            elif baseline_name == "software_pmo_ga":
                path, extra = run_software_ga(
                    skag,
                    src,
                    dst,
                    f_min=f_min,
                    max_hops=max_hops,
                    seed=seed + 1009 * (req_idx + 1),
                    pop_size=ga_pop_size,
                    max_generations=ga_max_generations,
                )
            else:
                raise AssertionError(baseline_name)

            runtime_ms = (time.perf_counter() - start) * 1000.0
            metrics = evaluate_path(skag, path, f_min=f_min)
            row = {
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

    latency_wins = count_wins(request_rows, "latency", higher_is_better=False)
    fidelity_wins = count_wins(request_rows, "bottleneck_fidelity", higher_is_better=True)

    aggregate_baselines: List[Dict[str, object]] = []
    for baseline_name in BASELINES:
        rows = [r for r in request_rows if r["baseline"] == baseline_name]
        feasible_rows = [r for r in rows if r["feasible"]]
        aggregate_baselines.append(
            {
                "baseline": baseline_name,
                "request_count": len(rows),
                "feasible_count": len(feasible_rows),
                "avg_hops": finite_mean(float(r["hops"]) for r in feasible_rows),
                "avg_distance_km": finite_mean(float(r["distance_km"]) for r in feasible_rows),
                "avg_latency": finite_mean(float(r["latency"]) for r in feasible_rows),
                "avg_bottleneck_fidelity": finite_mean(float(r["bottleneck_fidelity"]) for r in feasible_rows),
                "avg_load_balance": finite_mean(float(r["load_balance"]) for r in feasible_rows),
                "total_runtime_ms": float(sum(float(r["runtime_ms"]) for r in rows)),
                "latency_wins": latency_wins.get(baseline_name, 0),
                "fidelity_wins": fidelity_wins.get(baseline_name, 0),
            }
        )

    return {
        "topology": topo_name,
        "seed": seed,
        "requests": [{"src": s, "dst": d, "max_hops": h} for (s, d, h) in requests],
        "aggregate_baselines": aggregate_baselines,
        "request_results": request_rows,
    }


def fmt(x: object, digits: int = 6) -> str:
    if x is None:
        return "-"
    if isinstance(x, float):
        if math.isinf(x):
            return "inf"
        return f"{x:.{digits}f}"
    return str(x)


def main() -> None:
    ap = argparse.ArgumentParser(description="Run repeated-seed statistical baseline evaluation for QFlow.")
    ap.add_argument("--topologies", nargs="+", default=["mesh9", "mesh16", "irregular12"], choices=["ring6", "mesh9", "mesh16", "irregular12"])
    ap.add_argument("--seed-start", type=int, default=42)
    ap.add_argument("--repetitions", type=int, default=30)
    ap.add_argument("--sim-duration-s", type=float, default=0.5)
    ap.add_argument("--tick-dt-s", type=float, default=0.001)
    ap.add_argument("--f-min", type=float, default=0.9)
    ap.add_argument("--ga-pop-size", type=int, default=64)
    ap.add_argument("--ga-max-generations", type=int, default=100)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-csv", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    all_run_rows: List[Dict[str, object]] = []
    summary: Dict[str, object] = {
        "config": {
            "topologies": args.topologies,
            "seed_start": args.seed_start,
            "repetitions": args.repetitions,
            "sim_duration_s": args.sim_duration_s,
            "tick_dt_s": args.tick_dt_s,
            "f_min": args.f_min,
            "ga_pop_size": args.ga_pop_size,
            "ga_max_generations": args.ga_max_generations,
            "request_mode": "sequential_multi_request_with_key_consumption",
            "alphas": list(DEFAULT_ALPHAS),
        },
        "topologies": [],
    }

    for topo_name in args.topologies:
        run_summaries = []
        req_match_rows = []
        for rep in range(args.repetitions):
            seed = args.seed_start + rep
            run_summary = run_single_eval(
                topo_name=topo_name,
                seed=seed,
                sim_duration_s=args.sim_duration_s,
                tick_dt_s=args.tick_dt_s,
                f_min=args.f_min,
                ga_pop_size=args.ga_pop_size,
                ga_max_generations=args.ga_max_generations,
            )
            run_summaries.append(run_summary)
            for agg in run_summary["aggregate_baselines"]:
                all_run_rows.append({
                    "topology": topo_name,
                    "seed": seed,
                    **agg,
                })
            # Track GA-vs-keyaware path matching per request.
            by_req: Dict[int, Dict[str, Tuple[int, ...]]] = {}
            for row in run_summary["request_results"]:
                by_req.setdefault(int(row["request_index"]), {})[str(row["baseline"])] = tuple(row["path"])
            for req_idx, vals in sorted(by_req.items()):
                key_path = vals.get("dijkstra_keyaware", tuple())
                ga_path = vals.get("software_pmo_ga", tuple())
                req_match_rows.append({
                    "request_index": req_idx,
                    "match": bool(key_path == ga_path and key_path),
                    "keyaware_path": list(key_path),
                    "ga_path": list(ga_path),
                })

        # Aggregate repeated-run stats.
        baseline_stats = []
        for baseline in BASELINES:
            rows = [r for r in all_run_rows if r["topology"] == topo_name and r["baseline"] == baseline]
            def vec(field: str) -> List[float]:
                return [float(r[field]) for r in rows if r.get(field) is not None and math.isfinite(float(r[field]))]

            lat = vec("avg_latency")
            fid = vec("avg_bottleneck_fidelity")
            bal = vec("avg_load_balance")
            rt = vec("total_runtime_ms")
            hops = vec("avg_hops")
            dist = vec("avg_distance_km")
            baseline_stats.append({
                "baseline": baseline,
                "runs": len(rows),
                "mean_avg_hops": finite_mean(hops),
                "mean_avg_distance_km": finite_mean(dist),
                "mean_avg_latency": finite_mean(lat),
                "latency_ci95": z95_halfwidth(lat),
                "mean_avg_bottleneck_fidelity": finite_mean(fid),
                "fidelity_ci95": z95_halfwidth(fid),
                "mean_avg_load_balance": finite_mean(bal),
                "load_balance_ci95": z95_halfwidth(bal),
                "mean_total_runtime_ms": finite_mean(rt),
                "runtime_ci95": z95_halfwidth(rt),
                "mean_latency_wins": finite_mean(vec("latency_wins")),
                "mean_fidelity_wins": finite_mean(vec("fidelity_wins")),
            })

        request_match_summary = []
        requests = REQUEST_SUITES[topo_name]
        for req_idx, (src, dst, max_hops) in enumerate(requests):
            rows = [r for r in req_match_rows if r["request_index"] == req_idx]
            match_count = sum(1 for r in rows if r["match"])
            unique_keyaware = sorted({tuple(r["keyaware_path"]) for r in rows if r["keyaware_path"]})
            unique_ga = sorted({tuple(r["ga_path"]) for r in rows if r["ga_path"]})
            request_match_summary.append({
                "request_index": req_idx,
                "src": src,
                "dst": dst,
                "max_hops": max_hops,
                "ga_matches_keyaware_count": match_count,
                "ga_matches_keyaware_rate": match_count / len(rows) if rows else None,
                "distinct_keyaware_paths": [list(p) for p in unique_keyaware],
                "distinct_ga_paths": [list(p) for p in unique_ga],
            })

        summary["topologies"].append({
            "name": topo_name,
            "requests": [{"src": s, "dst": d, "max_hops": h} for (s, d, h) in requests],
            "repeated_baseline_stats": baseline_stats,
            "ga_vs_keyaware_request_match": request_match_summary,
        })

    out_json = Path(args.out_json)
    out_csv = Path(args.out_csv)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2) + "\n")

    fieldnames = [
        "topology", "seed", "baseline", "request_count", "feasible_count", "avg_hops",
        "avg_distance_km", "avg_latency", "avg_bottleneck_fidelity", "avg_load_balance",
        "total_runtime_ms", "latency_wins", "fidelity_wins",
    ]
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_run_rows:
            writer.writerow({k: row.get(k) for k in fieldnames})

    md_lines: List[str] = []
    md_lines.append("# Phase 10C Repeated-Seed Statistical Baseline Evaluation")
    md_lines.append("")
    md_lines.append("## Configuration")
    for k, v in summary["config"].items():
        md_lines.append(f"- {k}: {v}")
    md_lines.append("")
    for topo in summary["topologies"]:
        md_lines.append(f"## {topo['name']}")
        md_lines.append("")
        md_lines.append("### Repeated-run aggregate baseline stats")
        md_lines.append("")
        md_lines.append("| baseline | runs | mean_avg_hops | mean_avg_distance_km | mean_avg_latency | latency_ci95 | mean_avg_bottleneck_fidelity | fidelity_ci95 | mean_avg_load_balance | load_balance_ci95 | mean_total_runtime_ms | runtime_ci95 | mean_latency_wins | mean_fidelity_wins |")
        md_lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for row in topo["repeated_baseline_stats"]:
            md_lines.append(
                "| {baseline} | {runs} | {mean_avg_hops} | {mean_avg_distance_km} | {mean_avg_latency} | {latency_ci95} | {mean_avg_bottleneck_fidelity} | {fidelity_ci95} | {mean_avg_load_balance} | {load_balance_ci95} | {mean_total_runtime_ms} | {runtime_ci95} | {mean_latency_wins} | {mean_fidelity_wins} |".format(
                    baseline=row["baseline"],
                    runs=row["runs"],
                    mean_avg_hops=fmt(row["mean_avg_hops"]),
                    mean_avg_distance_km=fmt(row["mean_avg_distance_km"]),
                    mean_avg_latency=fmt(row["mean_avg_latency"]),
                    latency_ci95=fmt(row["latency_ci95"]),
                    mean_avg_bottleneck_fidelity=fmt(row["mean_avg_bottleneck_fidelity"]),
                    fidelity_ci95=fmt(row["fidelity_ci95"]),
                    mean_avg_load_balance=fmt(row["mean_avg_load_balance"]),
                    load_balance_ci95=fmt(row["load_balance_ci95"]),
                    mean_total_runtime_ms=fmt(row["mean_total_runtime_ms"]),
                    runtime_ci95=fmt(row["runtime_ci95"]),
                    mean_latency_wins=fmt(row["mean_latency_wins"]),
                    mean_fidelity_wins=fmt(row["mean_fidelity_wins"]),
                )
            )
        md_lines.append("")
        md_lines.append("### GA vs key-aware path-match stability")
        md_lines.append("")
        md_lines.append("| req_idx | src | dst | max_hops | ga_matches_keyaware_count | ga_matches_keyaware_rate | distinct_keyaware_paths | distinct_ga_paths |")
        md_lines.append("|---:|---:|---:|---:|---:|---:|---|---|")
        for row in topo["ga_vs_keyaware_request_match"]:
            md_lines.append(
                "| {request_index} | {src} | {dst} | {max_hops} | {ga_matches_keyaware_count} | {ga_matches_keyaware_rate} | `{distinct_keyaware_paths}` | `{distinct_ga_paths}` |".format(
                    request_index=row["request_index"],
                    src=row["src"],
                    dst=row["dst"],
                    max_hops=row["max_hops"],
                    ga_matches_keyaware_count=row["ga_matches_keyaware_count"],
                    ga_matches_keyaware_rate=fmt(row["ga_matches_keyaware_rate"]),
                    distinct_keyaware_paths=row["distinct_keyaware_paths"],
                    distinct_ga_paths=row["distinct_ga_paths"],
                )
            )
        md_lines.append("")

    out_md.write_text("\n".join(md_lines) + "\n")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_csv}")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
