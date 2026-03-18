#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import heapq
import json
import math
import time
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from reference_model import (
    Chromosome,
    FidelityDecayEngine,
    MultiObjectiveGA,
    QKDLinkParams,
    QKDLinkState,
    SKAGGraph,
    build_ring6_topology,
)


DEFAULT_ALPHAS = (1.0, 1.5, 0.5, 2.0)


def build_grid_topology(
    rows: int,
    cols: int,
    *,
    base_key_rate: float = 5000.0,
    coherence_time: float = 0.050,
    qber: float = 0.03,
    horiz_distance_km: float = 20.0,
    vert_distance_km: float = 24.0,
    alphas: Tuple[float, float, float, float] = DEFAULT_ALPHAS,
) -> SKAGGraph:
    """Build a bidirectional 2-D mesh topology."""
    skag = SKAGGraph(n_nodes=rows * cols, alphas=alphas)

    def node_id(r: int, c: int) -> int:
        return r * cols + c

    for r in range(rows):
        for c in range(cols):
            u = node_id(r, c)
            if c + 1 < cols:
                v = node_id(r, c + 1)
                params = QKDLinkParams(
                    src=u,
                    dst=v,
                    distance_km=horiz_distance_km,
                    base_key_rate=base_key_rate,
                    coherence_time_s=coherence_time,
                )
                skag.add_bidirectional_link(params, QKDLinkState(qber=qber))
            if r + 1 < rows:
                v = node_id(r + 1, c)
                params = QKDLinkParams(
                    src=u,
                    dst=v,
                    distance_km=vert_distance_km,
                    base_key_rate=base_key_rate,
                    coherence_time_s=coherence_time,
                )
                skag.add_bidirectional_link(params, QKDLinkState(qber=qber))
    return skag


def build_irregular_backbone_topology(
    *,
    base_key_rate: float = 5000.0,
    coherence_time: float = 0.050,
    qber: float = 0.03,
    alphas: Tuple[float, float, float, float] = DEFAULT_ALPHAS,
) -> SKAGGraph:
    """Build a small irregular backbone-style graph for later thesis evaluation."""
    skag = SKAGGraph(n_nodes=12, alphas=alphas)
    # (u, v, distance_km)
    links = [
        (0, 1, 18.0), (1, 2, 22.0), (2, 3, 19.0),
        (0, 4, 26.0), (4, 5, 15.0), (5, 6, 21.0),
        (1, 5, 17.0), (2, 6, 23.0), (3, 7, 20.0),
        (4, 8, 18.0), (5, 9, 24.0), (6, 10, 16.0),
        (7, 11, 22.0), (8, 9, 14.0), (9, 10, 13.0),
        (10, 11, 18.0), (2, 5, 20.0), (6, 9, 12.0),
    ]
    for u, v, dist in links:
        params = QKDLinkParams(
            src=u,
            dst=v,
            distance_km=dist,
            base_key_rate=base_key_rate,
            coherence_time_s=coherence_time,
        )
        skag.add_bidirectional_link(params, QKDLinkState(qber=qber))
    return skag


def simulate_key_dynamics(
    skag: SKAGGraph,
    *,
    sim_duration_s: float,
    tick_dt_s: float,
    f_min: float,
    seed: int,
) -> None:
    rng = np.random.default_rng(seed)
    fdpe = FidelityDecayEngine()
    t = 0.0
    while t < sim_duration_s:
        skag.generate_key_arrivals(tick_dt_s, t, rng)
        skag.expire_keys(t, f_min, fdpe, use_lut=True)
        skag.update_all_edges(t, fdpe, use_lut=True)
        t += tick_dt_s



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



def topology_request(name: str) -> Tuple[int, int, int]:
    mapping = {
        "ring6": (0, 3, 6),
        "mesh9": (0, 8, 8),
        "mesh16": (0, 15, 10),
        "irregular12": (0, 11, 10),
    }
    if name not in mapping:
        raise ValueError(f"Unknown topology '{name}'")
    return mapping[name]



def build_topology(name: str, alphas: Tuple[float, float, float, float]) -> SKAGGraph:
    if name == "ring6":
        return build_ring6_topology(alphas=alphas)
    if name == "mesh9":
        return build_grid_topology(3, 3, alphas=alphas)
    if name == "mesh16":
        return build_grid_topology(4, 4, alphas=alphas)
    if name == "irregular12":
        return build_irregular_backbone_topology(alphas=alphas)
    raise ValueError(f"Unsupported topology '{name}'")



def format_num(x: object) -> str:
    if isinstance(x, float):
        if math.isinf(x):
            return "inf"
        return f"{x:.6f}"
    return str(x)



def emit_markdown(summary: Dict[str, object], out_path: Path) -> None:
    lines: List[str] = []
    lines.append("# Phase 10A Baseline Evaluation Summary")
    lines.append("")
    lines.append("## Configuration")
    cfg = summary["config"]
    for key in ["topologies", "seed", "sim_duration_s", "tick_dt_s", "f_min", "ga_pop_size", "ga_max_generations"]:
        lines.append(f"- {key}: {cfg[key]}")
    lines.append("")

    for topo in summary["topologies"]:
        lines.append(f"## {topo['name']}")
        lines.append("")
        lines.append(f"- nodes: {topo['n_nodes']}")
        lines.append(f"- directed_links: {topo['n_directed_links']}")
        lines.append(f"- request: {topo['src']} -> {topo['dst']}")
        lines.append("")
        lines.append("| baseline | feasible | hops | distance_km | latency | bottleneck_fidelity | load_balance | runtime_ms | path |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---|")
        for row in topo["baselines"]:
            lines.append(
                "| {baseline} | {feasible} | {hops} | {distance_km} | {latency} | {bottleneck_fidelity} | {load_balance} | {runtime_ms} | `{path}` |".format(
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
    ap = argparse.ArgumentParser(description="Run phase10a software baseline evaluation for QFlow topologies.")
    ap.add_argument("--topologies", nargs="+", default=["ring6"], choices=["ring6", "mesh9", "mesh16", "irregular12"])
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
            "alphas": list(DEFAULT_ALPHAS),
        },
        "topologies": [],
    }

    csv_rows: List[Dict[str, object]] = []

    for topo_name in args.topologies:
        skag = build_topology(topo_name, DEFAULT_ALPHAS)
        simulate_key_dynamics(
            skag,
            sim_duration_s=args.sim_duration_s,
            tick_dt_s=args.tick_dt_s,
            f_min=args.f_min,
            seed=args.seed,
        )
        src, dst, max_hops = topology_request(topo_name)

        baselines: List[Dict[str, object]] = []

        start = time.perf_counter()
        shortest = dijkstra_path(
            skag, src, dst,
            edge_cost=lambda u, v: skag.link_params[(u, v)].distance_km,
            f_min=args.f_min,
            require_feasible=True,
        )
        runtime_ms = (time.perf_counter() - start) * 1000.0
        metrics = evaluate_path(skag, shortest, f_min=args.f_min)
        row = {
            "baseline": "dijkstra_distance",
            "runtime_ms": runtime_ms,
            **metrics,
        }
        baselines.append(row)

        start = time.perf_counter()
        keyaware = dijkstra_path(
            skag, src, dst,
            edge_cost=lambda u, v: skag.edge_weight(u, v),
            f_min=args.f_min,
            require_feasible=True,
        )
        runtime_ms = (time.perf_counter() - start) * 1000.0
        metrics = evaluate_path(skag, keyaware, f_min=args.f_min)
        row = {
            "baseline": "dijkstra_keyaware",
            "runtime_ms": runtime_ms,
            **metrics,
        }
        baselines.append(row)

        start = time.perf_counter()
        rand_path = random_valid_path(
            skag, src, dst,
            f_min=args.f_min,
            max_hops=max_hops,
            seed=args.seed,
        )
        runtime_ms = (time.perf_counter() - start) * 1000.0
        metrics = evaluate_path(skag, rand_path, f_min=args.f_min)
        row = {
            "baseline": "random_valid_path",
            "runtime_ms": runtime_ms,
            **metrics,
        }
        baselines.append(row)

        start = time.perf_counter()
        ga_path, ga_extra = run_software_ga(
            skag, src, dst,
            f_min=args.f_min,
            max_hops=max_hops,
            seed=args.seed,
            pop_size=args.ga_pop_size,
            max_generations=args.ga_max_generations,
        )
        runtime_ms = (time.perf_counter() - start) * 1000.0
        metrics = evaluate_path(skag, ga_path, f_min=args.f_min)
        row = {
            "baseline": "software_pmo_ga",
            "runtime_ms": runtime_ms,
            **metrics,
            **ga_extra,
        }
        baselines.append(row)

        topo_summary = {
            "name": topo_name,
            "n_nodes": skag.n_nodes,
            "n_directed_links": len(skag.link_params),
            "src": src,
            "dst": dst,
            "baselines": baselines,
        }
        summary["topologies"].append(topo_summary)

        for row in baselines:
            csv_rows.append({
                "topology": topo_name,
                "src": src,
                "dst": dst,
                **row,
            })

    out_json = Path(args.out_json)
    out_csv = Path(args.out_csv)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    out_json.write_text(json.dumps(summary, indent=2) + "\n")

    fieldnames = [
        "topology", "src", "dst", "baseline", "feasible", "hops", "distance_km",
        "latency", "bottleneck_fidelity", "load_balance", "runtime_ms", "path",
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
