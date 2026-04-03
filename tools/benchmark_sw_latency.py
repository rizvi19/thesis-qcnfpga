#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import heapq
import json
import math
import statistics
import time
from collections import deque
from pathlib import Path

import numpy as np
import reference_model as rm


def prepare_skag(seed: int = 42,
                 sim_duration_s: float = 0.5,
                 tick_dt_s: float = 0.001,
                 f_min: float = 0.9) -> rm.SKAGGraph:
    rng = np.random.default_rng(seed)
    fdpe = rm.FidelityDecayEngine()

    skag = rm.build_ring6_topology(
        base_key_rate=5000.0,
        coherence_time=0.050,
        qber=0.03,
        link_distance_km=25.0,
        alphas=(1.0, 1.5, 0.5, 2.0),
    )

    t = 0.0
    while t < sim_duration_s:
        skag.generate_key_arrivals(tick_dt_s, t, rng)
        skag.expire_keys(t, f_min, fdpe, use_lut=True)
        skag.update_all_edges(t, fdpe, use_lut=True)
        t += tick_dt_s
    return skag


def bfs_distance_route(skag: rm.SKAGGraph, src: int, dst: int):
    q = deque([(src, [src])])
    visited = {src}
    while q:
        u, path = q.popleft()
        if u == dst:
            return path
        for v in skag.neighbours(u):
            if v not in visited:
                visited.add(v)
                q.append((v, path + [v]))
    return None


def dijkstra_keyaware_route(skag: rm.SKAGGraph, src: int, dst: int):
    pq = [(0.0, src, [src])]
    best = {src: 0.0}
    while pq:
        cost, u, path = heapq.heappop(pq)
        if u == dst:
            return path, cost
        if cost > best.get(u, math.inf):
            continue
        for v in skag.neighbours(u):
            w = skag.edge_weight(u, v)
            if math.isinf(w):
                continue
            new_cost = cost + w
            if new_cost < best.get(v, math.inf):
                best[v] = new_cost
                heapq.heappush(pq, (new_cost, v, path + [v]))
    return None, math.inf


def reduced_pmo_ga_route(skag: rm.SKAGGraph, src: int, dst: int, seed: int):
    ga = rm.MultiObjectiveGA(
        skag=skag,
        pop_size=8,
        max_generations=3,
        crossover_rate=0.8,
        mutation_rate=0.05,
        tournament_k=2,
        elite_count=2,
        max_hops=6,
        f_min=0.9,
        stall_gens=3,
        stall_epsilon=1e-6,
        obj_weights=(0.4, 0.4, 0.2),
        seed=seed,
    )
    pareto, conv = ga.solve(src, dst, verbose=False)
    best_path = pareto[0].path if pareto else None
    return best_path, len(pareto), len(conv)


def benchmark(fn, iterations: int, warmup: int):
    for _ in range(warmup):
        fn()
    samples_ns = []
    last_result = None
    for _ in range(iterations):
        t0 = time.perf_counter_ns()
        last_result = fn()
        t1 = time.perf_counter_ns()
        samples_ns.append(t1 - t0)
    return samples_ns, last_result


def summarize_ns(samples_ns):
    samples_us = [x / 1000.0 for x in samples_ns]
    return {
        "median_us": statistics.median(samples_us),
        "mean_us": statistics.fmean(samples_us),
        "min_us": min(samples_us),
        "max_us": max(samples_us),
        "p95_us": float(np.percentile(samples_us, 95)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-csv", default="results/phase10_latency/sw_latency_benchmark.csv")
    ap.add_argument("--out-json", default="results/phase10_latency/sw_latency_benchmark.json")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--distance-iters", type=int, default=3000)
    ap.add_argument("--keyaware-iters", type=int, default=3000)
    ap.add_argument("--ga-iters", type=int, default=200)
    ap.add_argument("--warmup", type=int, default=25)
    args = ap.parse_args()

    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)

    src, dst = 0, 3
    skag = prepare_skag(seed=args.seed)

    results = []

    distance_samples, distance_last = benchmark(
        lambda: bfs_distance_route(skag, src, dst),
        iterations=args.distance_iters,
        warmup=args.warmup,
    )
    distance_stats = summarize_ns(distance_samples)
    results.append({
        "method_id": "distance_sw",
        "display_name": "Distance",
        "domain": "software",
        "iterations": args.distance_iters,
        "quantity_type": "measured_median",
        "decision_repr": str(distance_last),
        **distance_stats,
    })

    keyaware_samples, keyaware_last = benchmark(
        lambda: dijkstra_keyaware_route(skag, src, dst),
        iterations=args.keyaware_iters,
        warmup=args.warmup,
    )
    keyaware_stats = summarize_ns(keyaware_samples)
    results.append({
        "method_id": "keyaware_sw",
        "display_name": "Key-aware",
        "domain": "software",
        "iterations": args.keyaware_iters,
        "quantity_type": "measured_median",
        "decision_repr": str(keyaware_last[0]),
        **keyaware_stats,
    })

    # Use the same prepared SKAG as the simpler baselines.
    # This measures decision runtime, not topology/simulation preparation time.
    def ga_call():
        return reduced_pmo_ga_route(skag, src, dst, seed=args.seed)

    ga_samples, ga_last = benchmark(
        ga_call,
        iterations=args.ga_iters,
        warmup=max(5, min(args.warmup, 10)),
    )
    ga_stats = summarize_ns(ga_samples)
    results.append({
        "method_id": "pmo_ga_sw",
        "display_name": "Software PMO-GA",
        "domain": "software",
        "iterations": args.ga_iters,
        "quantity_type": "measured_median",
        "decision_repr": str(ga_last[0]),
        **ga_stats,
    })

    with open(args.out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "method_id", "display_name", "domain", "iterations", "quantity_type",
                "median_us", "mean_us", "min_us", "max_us", "p95_us", "decision_repr"
            ]
        )
        writer.writeheader()
        writer.writerows(results)

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_json}")


if __name__ == "__main__":
    main()
