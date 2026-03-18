#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import csv
import heapq
import json
import math
import sys
import time
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
for _p in (REPO_ROOT, SCRIPT_DIR, Path.cwd()):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

from reference_model import (
    FidelityDecayEngine,
    MultiObjectiveGA,
    QKDLinkParams,
    QKDLinkState,
    SKAGGraph,
    build_ring6_topology,
)

DEFAULT_ALPHAS = (1.0, 1.5, 0.5, 2.0)


def add_bidir(
    skag: SKAGGraph,
    u: int,
    v: int,
    *,
    distance_km: float,
    qber: float,
    base_key_rate: float,
    coherence_time_s: float,
) -> None:
    params = QKDLinkParams(
        src=u,
        dst=v,
        distance_km=distance_km,
        base_key_rate=base_key_rate,
        coherence_time_s=coherence_time_s,
    )
    skag.add_bidirectional_link(params, QKDLinkState(qber=qber))


def build_heterogeneous_grid_topology(
    rows: int,
    cols: int,
    *,
    alphas: Tuple[float, float, float, float] = DEFAULT_ALPHAS,
) -> SKAGGraph:
    """Build a mesh with deterministic link heterogeneity.

    The goal is not random noise; it is to create repeatable, thesis-friendly
    cases where shortest geometric distance is not always the best routing
    choice once key quality and availability are considered.
    """
    skag = SKAGGraph(n_nodes=rows * cols, alphas=alphas)

    def node_id(r: int, c: int) -> int:
        return r * cols + c

    center_rows = {rows // 2} if rows % 2 == 1 else {rows // 2 - 1, rows // 2}
    center_cols = {cols // 2} if cols % 2 == 1 else {cols // 2 - 1, cols // 2}

    for r in range(rows):
        for c in range(cols):
            u = node_id(r, c)

            if c + 1 < cols:
                v = node_id(r, c + 1)
                dist = 18.0 + 1.5 * r + 2.5 * (c % 2)
                qber = 0.021 + 0.003 * ((r + c) % 3)
                base_key_rate = 5400.0 - 220.0 * ((2 * r + c) % 3)
                coherence = 0.050 - 0.002 * ((r + 2 * c) % 3)

                # Degrade center corridor so distance-only routing is challenged.
                if r in center_rows or c in center_cols:
                    qber += 0.010
                    base_key_rate -= 450.0
                    coherence -= 0.006
                    dist += 4.0

                add_bidir(
                    skag,
                    u,
                    v,
                    distance_km=dist,
                    qber=qber,
                    base_key_rate=base_key_rate,
                    coherence_time_s=coherence,
                )

            if r + 1 < rows:
                v = node_id(r + 1, c)
                dist = 20.0 + 2.0 * c + 1.0 * (r % 2)
                qber = 0.022 + 0.0025 * ((2 * r + c) % 4)
                base_key_rate = 5250.0 - 180.0 * ((r + 2 * c) % 3)
                coherence = 0.049 - 0.0015 * ((r + c) % 4)

                if r in center_rows or c in center_cols:
                    qber += 0.008
                    base_key_rate -= 380.0
                    coherence -= 0.005
                    dist += 3.0

                add_bidir(
                    skag,
                    u,
                    v,
                    distance_km=dist,
                    qber=qber,
                    base_key_rate=base_key_rate,
                    coherence_time_s=coherence,
                )

    return skag


def build_irregular_backbone_topology(
    *,
    alphas: Tuple[float, float, float, float] = DEFAULT_ALPHAS,
) -> SKAGGraph:
    skag = SKAGGraph(n_nodes=12, alphas=alphas)
    # (u, v, distance_km, qber, base_key_rate, coherence_time_s)
    links = [
        (0, 1, 18.0, 0.022, 5600.0, 0.052),
        (1, 2, 22.0, 0.026, 5200.0, 0.048),
        (2, 3, 19.0, 0.021, 5650.0, 0.053),
        (0, 4, 27.0, 0.035, 4700.0, 0.042),
        (4, 5, 16.0, 0.023, 5550.0, 0.054),
        (5, 6, 21.0, 0.036, 4800.0, 0.041),
        (1, 5, 17.0, 0.039, 4600.0, 0.039),
        (2, 6, 24.0, 0.021, 5750.0, 0.055),
        (3, 7, 20.0, 0.022, 5500.0, 0.051),
        (4, 8, 18.0, 0.024, 5400.0, 0.052),
        (5, 9, 25.0, 0.029, 5000.0, 0.045),
        (6, 10, 16.0, 0.020, 5750.0, 0.055),
        (7, 11, 22.0, 0.023, 5450.0, 0.051),
        (8, 9, 14.0, 0.021, 5700.0, 0.056),
        (9, 10, 13.0, 0.020, 5800.0, 0.057),
        (10, 11, 18.0, 0.022, 5650.0, 0.053),
        (2, 5, 20.0, 0.037, 4700.0, 0.040),
        (6, 9, 12.0, 0.019, 5900.0, 0.058),
    ]
    for u, v, d, q, rate, coh in links:
        add_bidir(skag, u, v, distance_km=d, qber=q, base_key_rate=rate, coherence_time_s=coh)
    return skag


def build_topology(name: str, alphas: Tuple[float, float, float, float]) -> SKAGGraph:
    if name == "ring6":
        return build_ring6_topology(alphas=alphas)
    if name == "mesh9":
        return build_heterogeneous_grid_topology(3, 3, alphas=alphas)
    if name == "mesh16":
        return build_heterogeneous_grid_topology(4, 4, alphas=alphas)
    if name == "irregular12":
        return build_irregular_backbone_topology(alphas=alphas)
    raise ValueError(f"Unsupported topology '{name}'")


REQUEST_SUITES: Dict[str, List[Tuple[int, int, int]]] = {
    "ring6": [(0, 3, 6), (1, 4, 6), (2, 5, 6)],
    "mesh9": [(0, 8, 8), (2, 6, 8), (0, 5, 8), (1, 7, 8)],
    "mesh16": [(0, 15, 10), (3, 12, 10), (1, 14, 10), (4, 11, 10)],
    "irregular12": [(0, 11, 10), (1, 10, 10), (4, 7, 10), (2, 9, 10)],
}


def simulate_key_dynamics(
    skag: SKAGGraph,
    *,
    sim_duration_s: float,
    tick_dt_s: float,
    f_min: float,
    seed: int,
) -> float:
    rng = np.random.default_rng(seed)
    fdpe = FidelityDecayEngine()
    t = 0.0
    while t < sim_duration_s:
        skag.generate_key_arrivals(tick_dt_s, t, rng)
        skag.expire_keys(t, f_min, fdpe, use_lut=True)
        skag.update_all_edges(t, fdpe, use_lut=True)
        t += tick_dt_s
    return t



def reconstruct_path(prev: Dict[int, int], src: int, dst: int) -> List[int]:
    if src == dst:
        return [src]
    if dst not in prev:
        return []
    path = [dst]
    cur = dst
    while cur != src:
        cur = prev[cur]
        path.append(cur)
    path.reverse()
    return path



def dijkstra_path(
    skag: SKAGGraph,
    src: int,
    dst: int,
    *,
    edge_cost: Callable[[int, int], float],
    f_min: float,
    require_feasible: bool,
) -> List[int]:
    dist = {src: 0.0}
    prev: Dict[int, int] = {}
    heap: List[Tuple[float, int]] = [(0.0, src)]
    visited = set()

    while heap:
        cur_dist, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        if u == dst:
            break

        for v in skag.neighbours(u):
            edge = skag.get_edge(u, v)
            if edge is None:
                continue
            if require_feasible and (edge.key_count < 1 or edge.avg_fidelity < f_min):
                continue
            cost = edge_cost(u, v)
            if not math.isfinite(cost):
                continue
            cand = cur_dist + cost
            if cand < dist.get(v, float("inf")):
                dist[v] = cand
                prev[v] = u
                heapq.heappush(heap, (cand, v))
    return reconstruct_path(prev, src, dst)



def evaluate_path(skag: SKAGGraph, path: Sequence[int], *, f_min: float) -> Dict[str, object]:
    if not path or len(path) < 2:
        return {
            "feasible": False,
            "path": list(path),
            "hops": max(len(path) - 1, 0),
            "latency": float("inf"),
            "bottleneck_fidelity": 0.0,
            "load_balance": float("inf"),
            "distance_km": float("inf"),
        }

    total_weight = 0.0
    bottleneck_fidelity = float("inf")
    max_util = 0.0
    total_distance = 0.0

    for u, v in zip(path[:-1], path[1:]):
        edge = skag.get_edge(u, v)
        params = skag.link_params.get((u, v))
        state = skag.link_states.get((u, v))
        if edge is None or params is None or state is None:
            return {
                "feasible": False,
                "path": list(path),
                "hops": len(path) - 1,
                "latency": float("inf"),
                "bottleneck_fidelity": 0.0,
                "load_balance": float("inf"),
                "distance_km": float("inf"),
            }
        if edge.key_count < 1 or edge.avg_fidelity < f_min or not math.isfinite(edge.composite_weight):
            return {
                "feasible": False,
                "path": list(path),
                "hops": len(path) - 1,
                "latency": float("inf"),
                "bottleneck_fidelity": 0.0,
                "load_balance": float("inf"),
                "distance_km": float("inf"),
            }
        total_weight += edge.composite_weight
        bottleneck_fidelity = min(bottleneck_fidelity, edge.avg_fidelity)
        total_distance += params.distance_km
        util = state.consumed_keys / max(edge.key_count, 1)
        max_util = max(max_util, util)

    return {
        "feasible": True,
        "path": list(path),
        "hops": len(path) - 1,
        "latency": total_weight,
        "bottleneck_fidelity": bottleneck_fidelity,
        "load_balance": max_util,
        "distance_km": total_distance,
    }



def random_valid_path(
    skag: SKAGGraph,
    src: int,
    dst: int,
    *,
    f_min: float,
    max_hops: int,
    seed: int,
    tries: int = 256,
) -> List[int]:
    helper = MultiObjectiveGA(skag=skag, max_hops=max_hops, seed=seed)
    for _ in range(tries):
        path = helper._random_valid_path(src, dst)
        metrics = evaluate_path(skag, path, f_min=f_min)
        if metrics["feasible"]:
            return path
    return []



def run_software_ga(
    skag: SKAGGraph,
    src: int,
    dst: int,
    *,
    f_min: float,
    max_hops: int,
    seed: int,
    pop_size: int,
    max_generations: int,
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
        obj_weights=(0.4, 0.4, 0.2),
        seed=seed,
    )
    pareto, convergence = ga.solve(src, dst, verbose=False)
    best_path = pareto[0].path if pareto else []
    return best_path, {
        "pareto_front_size": len(pareto),
        "convergence_points": len(convergence),
        "best_tchebycheff": convergence[-1] if convergence else None,
    }



def apply_path_consumption(skag: SKAGGraph, path: Sequence[int], *, t_now: float) -> None:
    if not path or len(path) < 2:
        return
    fdpe = FidelityDecayEngine()
    for u, v in zip(path[:-1], path[1:]):
        state = skag.link_states.get((u, v))
        if state is None:
            continue
        if state.key_pool:
            state.key_pool.pop(0)
        state.consumed_keys += 1
    skag.update_all_edges(t_now, fdpe, use_lut=True)



def finite_mean(values: Iterable[float]) -> Optional[float]:
    vals = [x for x in values if isinstance(x, (int, float)) and math.isfinite(float(x))]
    if not vals:
        return None
    return float(sum(vals) / len(vals))



def count_wins(request_rows: List[Dict[str, object]], metric: str, *, higher_is_better: bool) -> Dict[str, int]:
    wins: Dict[str, int] = {}
    by_request: Dict[int, List[Dict[str, object]]] = {}
    for row in request_rows:
        by_request.setdefault(int(row["request_index"]), []).append(row)

    for _, rows in sorted(by_request.items()):
        feasible = [r for r in rows if r["feasible"]]
        if not feasible:
            continue
        best_value = None
        for r in feasible:
            value = float(r[metric])
            if best_value is None:
                best_value = value
            elif higher_is_better and value > best_value:
                best_value = value
            elif (not higher_is_better) and value < best_value:
                best_value = value
        for r in feasible:
            value = float(r[metric])
            if abs(value - best_value) <= 1e-12:
                wins[r["baseline"]] = wins.get(r["baseline"], 0) + 1
    return wins



def format_num(x: object) -> str:
    if x is None:
        return "-"
    if isinstance(x, float):
        if math.isinf(x):
            return "inf"
        return f"{x:.6f}"
    return str(x)



def emit_markdown(summary: Dict[str, object], out_path: Path) -> None:
    lines: List[str] = []
    lines.append("# Phase 10B Baseline Evaluation Summary")
    lines.append("")
    lines.append("## Configuration")
    cfg = summary["config"]
    for key in [
        "topologies",
        "seed",
        "sim_duration_s",
        "tick_dt_s",
        "f_min",
        "ga_pop_size",
        "ga_max_generations",
        "request_mode",
    ]:
        lines.append(f"- {key}: {cfg[key]}")
    lines.append("")

    for topo in summary["topologies"]:
        lines.append(f"## {topo['name']}")
        lines.append("")
        lines.append(f"- nodes: {topo['n_nodes']}")
        lines.append(f"- directed_links: {topo['n_directed_links']}")
        lines.append(f"- requests: {topo['requests']}")
        lines.append("")
        lines.append("### Aggregate baseline summary")
        lines.append("")
        lines.append("| baseline | feasible_count | avg_hops | avg_distance_km | avg_latency | avg_bottleneck_fidelity | avg_load_balance | total_runtime_ms | latency_wins | fidelity_wins |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for row in topo["aggregate_baselines"]:
            lines.append(
                "| {baseline} | {feasible_count}/{request_count} | {avg_hops} | {avg_distance_km} | {avg_latency} | {avg_bottleneck_fidelity} | {avg_load_balance} | {total_runtime_ms} | {latency_wins} | {fidelity_wins} |".format(
                    baseline=row["baseline"],
                    feasible_count=row["feasible_count"],
                    request_count=row["request_count"],
                    avg_hops=format_num(row["avg_hops"]),
                    avg_distance_km=format_num(row["avg_distance_km"]),
                    avg_latency=format_num(row["avg_latency"]),
                    avg_bottleneck_fidelity=format_num(row["avg_bottleneck_fidelity"]),
                    avg_load_balance=format_num(row["avg_load_balance"]),
                    total_runtime_ms=format_num(row["total_runtime_ms"]),
                    latency_wins=row["latency_wins"],
                    fidelity_wins=row["fidelity_wins"],
                )
            )
        lines.append("")
        lines.append("### Per-request detail")
        lines.append("")
        lines.append("| req_idx | src | dst | baseline | feasible | hops | distance_km | latency | bottleneck_fidelity | load_balance | runtime_ms | path |")
        lines.append("|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---|")
        for row in topo["request_results"]:
            lines.append(
                "| {request_index} | {src} | {dst} | {baseline} | {feasible} | {hops} | {distance_km} | {latency} | {bottleneck_fidelity} | {load_balance} | {runtime_ms} | `{path}` |".format(
                    request_index=row["request_index"],
                    src=row["src"],
                    dst=row["dst"],
                    baseline=row["baseline"],
                    feasible="yes" if row["feasible"] else "no",
                    hops=row["hops"],
                    distance_km=format_num(row["distance_km"]),
                    latency=format_num(row["latency"]),
                    bottleneck_fidelity=format_num(row["bottleneck_fidelity"]),
                    load_balance=format_num(row["load_balance"]),
                    runtime_ms=format_num(row["runtime_ms"]),
                    path=row["path"],
                )
            )
        lines.append("")
    out_path.write_text("\n".join(lines) + "\n")



def main() -> None:
    ap = argparse.ArgumentParser(description="Run phase10b multi-request software baseline evaluation for QFlow topologies.")
    ap.add_argument("--topologies", nargs="+", default=["mesh9", "mesh16", "irregular12"], choices=["ring6", "mesh9", "mesh16", "irregular12"])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--sim-duration-s", type=float, default=0.5)
    ap.add_argument("--tick-dt-s", type=float, default=0.001)
    ap.add_argument("--f-min", type=float, default=0.9)
    ap.add_argument("--ga-pop-size", type=int, default=64)
    ap.add_argument("--ga-max-generations", type=int, default=100)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-csv", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    summary: Dict[str, object] = {
        "config": {
            "topologies": args.topologies,
            "seed": args.seed,
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

    csv_rows: List[Dict[str, object]] = []

    for topo_name in args.topologies:
        base_skag = build_topology(topo_name, DEFAULT_ALPHAS)
        t_eval = simulate_key_dynamics(
            base_skag,
            sim_duration_s=args.sim_duration_s,
            tick_dt_s=args.tick_dt_s,
            f_min=args.f_min,
            seed=args.seed,
        )
        requests = REQUEST_SUITES[topo_name]

        request_rows: List[Dict[str, object]] = []
        for baseline_name in [
            "dijkstra_distance",
            "dijkstra_keyaware",
            "random_valid_path",
            "software_pmo_ga",
        ]:
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
                        f_min=args.f_min,
                        require_feasible=True,
                    )
                elif baseline_name == "dijkstra_keyaware":
                    path = dijkstra_path(
                        skag,
                        src,
                        dst,
                        edge_cost=lambda u, v: skag.edge_weight(u, v),
                        f_min=args.f_min,
                        require_feasible=True,
                    )
                elif baseline_name == "random_valid_path":
                    path = random_valid_path(
                        skag,
                        src,
                        dst,
                        f_min=args.f_min,
                        max_hops=max_hops,
                        seed=args.seed + 101 * (req_idx + 1),
                    )
                elif baseline_name == "software_pmo_ga":
                    path, extra = run_software_ga(
                        skag,
                        src,
                        dst,
                        f_min=args.f_min,
                        max_hops=max_hops,
                        seed=args.seed + 1009 * (req_idx + 1),
                        pop_size=args.ga_pop_size,
                        max_generations=args.ga_max_generations,
                    )
                else:
                    raise AssertionError(baseline_name)

                runtime_ms = (time.perf_counter() - start) * 1000.0
                metrics = evaluate_path(skag, path, f_min=args.f_min)
                row = {
                    "topology": topo_name,
                    "request_index": req_idx,
                    "src": src,
                    "dst": dst,
                    "baseline": baseline_name,
                    "runtime_ms": runtime_ms,
                    **metrics,
                    **extra,
                }
                request_rows.append(row)
                csv_rows.append(row)
                if metrics["feasible"]:
                    apply_path_consumption(skag, path, t_now=t_eval)

        latency_wins = count_wins(request_rows, "latency", higher_is_better=False)
        fidelity_wins = count_wins(request_rows, "bottleneck_fidelity", higher_is_better=True)

        aggregate_baselines: List[Dict[str, object]] = []
        for baseline_name in [
            "dijkstra_distance",
            "dijkstra_keyaware",
            "random_valid_path",
            "software_pmo_ga",
        ]:
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

        summary["topologies"].append(
            {
                "name": topo_name,
                "n_nodes": base_skag.n_nodes,
                "n_directed_links": len(base_skag.link_params),
                "requests": [{"src": s, "dst": d, "max_hops": h} for (s, d, h) in requests],
                "aggregate_baselines": aggregate_baselines,
                "request_results": request_rows,
            }
        )

    out_json = Path(args.out_json)
    out_csv = Path(args.out_csv)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    out_json.write_text(json.dumps(summary, indent=2) + "\n")

    fieldnames = [
        "topology", "request_index", "src", "dst", "baseline", "feasible", "hops",
        "distance_km", "latency", "bottleneck_fidelity", "load_balance", "runtime_ms", "path",
        "pareto_front_size", "convergence_points", "best_tchebycheff",
    ]
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in csv_rows:
            writer.writerow({k: row.get(k) for k in fieldnames})

    emit_markdown(summary, out_md)
    print(f"Wrote {out_json}")
    print(f"Wrote {out_csv}")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
