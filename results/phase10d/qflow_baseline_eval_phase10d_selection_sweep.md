# Phase 10D GA Selection-Policy Sweep

## Why this exists

Phase 10C showed software PMO-GA matching key-aware shortest path on the current suites.
This sweep tests whether the collapse comes from how the final GA answer is selected: minimum latency from the Pareto front versus weighted Tchebycheff selection.

## Configuration

- topologies: ['mesh9', 'mesh16', 'irregular12']
- repetitions: 6
- ga_pop_size: 64
- ga_max_generations: 100
- profiles: ['current_like', 'depletion_plus_stricter_fidelity']

## current_like / mesh9

### Aggregate baseline stats

| baseline | runs | mean_avg_latency | latency_ci95 | mean_avg_bottleneck_fidelity | fidelity_ci95 | mean_avg_load_balance | load_balance_ci95 | mean_total_runtime_ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dijkstra_keyaware | 6 | 6.069915 | 0.119106 | 0.920505 | 0.003217 | 0.153819 | 0.052888 | 0.090202 |
| ga_latency_pick_default | 6 | 6.069915 | 0.119106 | 0.920505 | 0.003217 | 0.153819 | 0.052888 | 288.084543 |
| ga_tcheby_pick_default | 6 | 6.079002 | 0.116304 | 0.920096 | 0.004000 | 0.123865 | 0.032409 | 288.862689 |
| ga_tcheby_pick_fidelityheavy | 6 | 6.079001 | 0.116305 | 0.919881 | 0.003911 | 0.121261 | 0.030702 | 288.464592 |

### GA variants vs key-aware

| variant | request_instances | same_path_rate_vs_keyaware | ga_lower_latency_rate | ga_higher_fidelity_rate | ga_lower_balance_rate |
|---|---:|---:|---:|---:|---:|
| ga_latency_pick_default | 24 | 1.000000 | 0.000000 | 0.000000 | 0.000000 |
| ga_tcheby_pick_default | 24 | 0.791667 | 0.083333 | 0.166667 | 0.250000 |
| ga_tcheby_pick_fidelityheavy | 24 | 0.791667 | 0.083333 | 0.166667 | 0.250000 |

## current_like / mesh16

### Aggregate baseline stats

| baseline | runs | mean_avg_latency | latency_ci95 | mean_avg_bottleneck_fidelity | fidelity_ci95 | mean_avg_load_balance | load_balance_ci95 | mean_total_runtime_ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dijkstra_keyaware | 6 | 9.412682 | 0.087190 | 0.913123 | 0.003635 | 0.178571 | 0.034558 | 0.167024 |
| ga_latency_pick_default | 6 | 9.412682 | 0.087190 | 0.913123 | 0.003635 | 0.178571 | 0.034558 | 385.702052 |
| ga_tcheby_pick_default | 6 | 9.453969 | 0.143075 | 0.913568 | 0.003839 | 0.152877 | 0.086557 | 385.065833 |
| ga_tcheby_pick_fidelityheavy | 6 | 9.453969 | 0.143075 | 0.913568 | 0.003839 | 0.152877 | 0.086557 | 384.980846 |

### GA variants vs key-aware

| variant | request_instances | same_path_rate_vs_keyaware | ga_lower_latency_rate | ga_higher_fidelity_rate | ga_lower_balance_rate |
|---|---:|---:|---:|---:|---:|
| ga_latency_pick_default | 24 | 1.000000 | 0.000000 | 0.000000 | 0.000000 |
| ga_tcheby_pick_default | 24 | 0.708333 | 0.041667 | 0.125000 | 0.208333 |
| ga_tcheby_pick_fidelityheavy | 24 | 0.708333 | 0.041667 | 0.125000 | 0.208333 |

## current_like / irregular12

### Aggregate baseline stats

| baseline | runs | mean_avg_latency | latency_ci95 | mean_avg_bottleneck_fidelity | fidelity_ci95 | mean_avg_load_balance | load_balance_ci95 | mean_total_runtime_ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dijkstra_keyaware | 6 | 6.252080 | 0.109629 | 0.925011 | 0.002094 | 0.095500 | 0.048100 | 0.124439 |
| ga_latency_pick_default | 6 | 6.252080 | 0.109629 | 0.925011 | 0.002094 | 0.095500 | 0.048100 | 302.253680 |
| ga_tcheby_pick_default | 6 | 6.259215 | 0.105204 | 0.925202 | 0.001958 | 0.064344 | 0.037453 | 303.153186 |
| ga_tcheby_pick_fidelityheavy | 6 | 6.267877 | 0.103174 | 0.924529 | 0.002056 | 0.045660 | 0.040288 | 304.303543 |

### GA variants vs key-aware

| variant | request_instances | same_path_rate_vs_keyaware | ga_lower_latency_rate | ga_higher_fidelity_rate | ga_lower_balance_rate |
|---|---:|---:|---:|---:|---:|
| ga_latency_pick_default | 24 | 1.000000 | 0.000000 | 0.000000 | 0.000000 |
| ga_tcheby_pick_default | 24 | 0.916667 | 0.083333 | 0.041667 | 0.125000 |
| ga_tcheby_pick_fidelityheavy | 24 | 0.833333 | 0.125000 | 0.041667 | 0.250000 |

## depletion_plus_stricter_fidelity / mesh9

### Aggregate baseline stats

| baseline | runs | mean_avg_latency | latency_ci95 | mean_avg_bottleneck_fidelity | fidelity_ci95 | mean_avg_load_balance | load_balance_ci95 | mean_total_runtime_ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dijkstra_keyaware | 6 | 7.194369 | 0.430850 | 0.930587 | 0.002111 | 0.479886 | 0.230128 | 0.175494 |
| ga_latency_pick_default | 6 | 7.194369 | 0.430850 | 0.930587 | 0.002111 | 0.479886 | 0.230128 | 2302.981484 |
| ga_tcheby_pick_default | 6 | 7.194369 | 0.430850 | 0.930587 | 0.002111 | 0.479886 | 0.230128 | 2303.884392 |
| ga_tcheby_pick_fidelityheavy | 6 | 7.194369 | 0.430850 | 0.930587 | 0.002111 | 0.479886 | 0.230128 | 2304.538407 |

### GA variants vs key-aware

| variant | request_instances | same_path_rate_vs_keyaware | ga_lower_latency_rate | ga_higher_fidelity_rate | ga_lower_balance_rate |
|---|---:|---:|---:|---:|---:|
| ga_latency_pick_default | 48 | 0.687500 | 0.000000 | 0.000000 | 0.000000 |
| ga_tcheby_pick_default | 48 | 0.687500 | 0.000000 | 0.000000 | 0.000000 |
| ga_tcheby_pick_fidelityheavy | 48 | 0.687500 | 0.000000 | 0.000000 | 0.000000 |

## depletion_plus_stricter_fidelity / mesh16

### Aggregate baseline stats

| baseline | runs | mean_avg_latency | latency_ci95 | mean_avg_bottleneck_fidelity | fidelity_ci95 | mean_avg_load_balance | load_balance_ci95 | mean_total_runtime_ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dijkstra_keyaware | 6 | 11.407773 | 0.788177 | 0.928707 | 0.001922 | 0.610648 | 0.261845 | 0.280178 |
| ga_latency_pick_default | 6 | 11.407773 | 0.788177 | 0.928707 | 0.001922 | 0.610648 | 0.261845 | 2956.327937 |
| ga_tcheby_pick_default | 6 | 11.414166 | 0.788811 | 0.928707 | 0.001922 | 0.577315 | 0.240853 | 2952.781997 |
| ga_tcheby_pick_fidelityheavy | 6 | 11.414166 | 0.788811 | 0.928707 | 0.001922 | 0.577315 | 0.240853 | 2963.897703 |

### GA variants vs key-aware

| variant | request_instances | same_path_rate_vs_keyaware | ga_lower_latency_rate | ga_higher_fidelity_rate | ga_lower_balance_rate |
|---|---:|---:|---:|---:|---:|
| ga_latency_pick_default | 48 | 0.604167 | 0.000000 | 0.000000 | 0.000000 |
| ga_tcheby_pick_default | 48 | 0.583333 | 0.000000 | 0.000000 | 0.020833 |
| ga_tcheby_pick_fidelityheavy | 48 | 0.583333 | 0.000000 | 0.000000 | 0.020833 |

## depletion_plus_stricter_fidelity / irregular12

### Aggregate baseline stats

| baseline | runs | mean_avg_latency | latency_ci95 | mean_avg_bottleneck_fidelity | fidelity_ci95 | mean_avg_load_balance | load_balance_ci95 | mean_total_runtime_ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dijkstra_keyaware | 6 | 6.536211 | 0.206432 | 0.934657 | 0.002291 | 0.478456 | 0.121032 | 0.243892 |
| ga_latency_pick_default | 6 | 6.536211 | 0.206432 | 0.934657 | 0.002291 | 0.478456 | 0.121032 | 830.479453 |
| ga_tcheby_pick_default | 6 | 6.533281 | 0.201454 | 0.933315 | 0.001756 | 0.333286 | 0.093950 | 830.422007 |
| ga_tcheby_pick_fidelityheavy | 6 | 6.563657 | 0.215212 | 0.932754 | 0.001640 | 0.291967 | 0.095692 | 830.777206 |

### GA variants vs key-aware

| variant | request_instances | same_path_rate_vs_keyaware | ga_lower_latency_rate | ga_higher_fidelity_rate | ga_lower_balance_rate |
|---|---:|---:|---:|---:|---:|
| ga_latency_pick_default | 48 | 1.000000 | 0.000000 | 0.000000 | 0.000000 |
| ga_tcheby_pick_default | 48 | 0.875000 | 0.166667 | 0.020833 | 0.229167 |
| ga_tcheby_pick_fidelityheavy | 48 | 0.791667 | 0.125000 | 0.062500 | 0.270833 |

## Headline findings

- max_tcheby_separation_rate: 0.416667
- best_tcheby_variant_by_fidelity_gain_rate: {'variant': 'ga_tcheby_pick_default', 'request_instances': 24, 'same_path_rate_vs_keyaware': 0.7916666666666666, 'ga_lower_latency_rate': 0.08333333333333333, 'ga_higher_fidelity_rate': 0.16666666666666666, 'ga_lower_balance_rate': 0.25}
- best_tcheby_variant_by_balance_gain_rate: {'variant': 'ga_tcheby_pick_fidelityheavy', 'request_instances': 48, 'same_path_rate_vs_keyaware': 0.7916666666666666, 'ga_lower_latency_rate': 0.125, 'ga_higher_fidelity_rate': 0.0625, 'ga_lower_balance_rate': 0.2708333333333333}
- interpretation: If tcheby-picked GA separates from key-aware here, the collapse seen in Phase 10C was largely a final-answer selection-policy issue. If it still matches key-aware, then the current topology/request suite truly does not induce enough multi-objective conflict.

