# Phase 10A Baseline Evaluation Summary

## Configuration
- topologies: ['ring6']
- seed: 42
- sim_duration_s: 0.5
- tick_dt_s: 0.001
- f_min: 0.9
- ga_pop_size: 64
- ga_max_generations: 100

## ring6

- nodes: 6
- directed_links: 12
- request: 0 -> 3

| baseline | feasible | hops | distance_km | latency | bottleneck_fidelity | load_balance | runtime_ms | path |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| dijkstra_distance | yes | 3 | 75.000000 | 5.514356 | 0.932172 | 0.000000 | 0.024898 | `[0, 1, 2, 3]` |
| dijkstra_keyaware | yes | 3 | 75.000000 | 5.460344 | 0.928396 | 0.000000 | 0.011981 | `[0, 5, 4, 3]` |
| random_valid_path | yes | 3 | 75.000000 | 5.514356 | 0.932172 | 0.000000 | 0.061051 | `[0, 1, 2, 3]` |
| software_pmo_ga | yes | 3 | 75.000000 | 5.460344 | 0.928396 | 0.000000 | 78.080086 | `[0, 5, 4, 3]` |

