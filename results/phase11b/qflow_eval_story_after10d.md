# QFlow Evaluation Story After Phase 10D
## Decision
- Recommended software PMO-GA thesis variant: **ga_tcheby_pick_default**
- Reason: it is the most thesis-faithful multi-objective selector across the current Phase 10D sweep.

## Why this matters
- Phase 10C showed the old software PMO-GA evaluation collapsing to the key-aware shortest-path baseline on the prior suite.
- Phase 10D shows that this collapse was substantially influenced by **final-answer selection policy**.
- Once the Pareto-front member is chosen with **weighted Tchebycheff selection**, PMO-GA separates from the key-aware baseline on a meaningful subset of cases.

## Recommendation by profile/topology
| profile | topology | recommended_ga_variant | Δ latency (GA-keyaware) | Δ fidelity (GA-keyaware) | Δ load_balance (GA-keyaware) |
|---|---|---|---:|---:|---:|
| current_like | mesh9 | ga_tcheby_pick_fidelityheavy | 0.009086 | -0.000624 | -0.032559 |
| current_like | mesh16 | ga_tcheby_pick_default | 0.041286 | 0.000444 | -0.025694 |
| current_like | irregular12 | ga_tcheby_pick_default | 0.007135 | 0.000190 | -0.031157 |
| depletion_plus_stricter_fidelity | mesh9 | ga_tcheby_pick_default | 0.000000 | 0.000000 | 0.000000 |
| depletion_plus_stricter_fidelity | mesh16 | ga_tcheby_pick_default | 0.006393 | 0.000000 | -0.033333 |
| depletion_plus_stricter_fidelity | irregular12 | ga_tcheby_pick_default | -0.002931 | -0.001342 | -0.145170 |

## Detailed tradeoff table
| profile | topology | ga_variant | keyaware_latency | ga_latency | Δ latency | keyaware_fidelity | ga_fidelity | Δ fidelity | keyaware_load_balance | ga_load_balance | Δ load_balance |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| current_like | mesh9 | ga_tcheby_pick_default | 6.069915 | 6.079002 | 0.009087 | 0.920505 | 0.920096 | -0.000409 | 0.153819 | 0.123865 | -0.029955 |
| current_like | mesh9 | ga_tcheby_pick_fidelityheavy | 6.069915 | 6.079001 | 0.009086 | 0.920505 | 0.919881 | -0.000624 | 0.153819 | 0.121261 | -0.032559 |
| current_like | mesh16 | ga_tcheby_pick_default | 9.412682 | 9.453969 | 0.041286 | 0.913123 | 0.913568 | 0.000444 | 0.178571 | 0.152877 | -0.025694 |
| current_like | mesh16 | ga_tcheby_pick_fidelityheavy | 9.412682 | 9.453969 | 0.041286 | 0.913123 | 0.913568 | 0.000444 | 0.178571 | 0.152877 | -0.025694 |
| current_like | irregular12 | ga_tcheby_pick_default | 6.252080 | 6.259215 | 0.007135 | 0.925011 | 0.925202 | 0.000190 | 0.095500 | 0.064344 | -0.031157 |
| current_like | irregular12 | ga_tcheby_pick_fidelityheavy | 6.252080 | 6.267877 | 0.015797 | 0.925011 | 0.924529 | -0.000483 | 0.095500 | 0.045660 | -0.049840 |
| depletion_plus_stricter_fidelity | mesh9 | ga_tcheby_pick_default | 7.194369 | 7.194369 | 0.000000 | 0.930587 | 0.930587 | 0.000000 | 0.479886 | 0.479886 | 0.000000 |
| depletion_plus_stricter_fidelity | mesh9 | ga_tcheby_pick_fidelityheavy | 7.194369 | 7.194369 | 0.000000 | 0.930587 | 0.930587 | 0.000000 | 0.479886 | 0.479886 | 0.000000 |
| depletion_plus_stricter_fidelity | mesh16 | ga_tcheby_pick_default | 11.407773 | 11.414166 | 0.006393 | 0.928707 | 0.928707 | 0.000000 | 0.610648 | 0.577315 | -0.033333 |
| depletion_plus_stricter_fidelity | mesh16 | ga_tcheby_pick_fidelityheavy | 11.407773 | 11.414166 | 0.006393 | 0.928707 | 0.928707 | 0.000000 | 0.610648 | 0.577315 | -0.033333 |
| depletion_plus_stricter_fidelity | irregular12 | ga_tcheby_pick_default | 6.536211 | 6.533281 | -0.002931 | 0.934657 | 0.933315 | -0.001342 | 0.478456 | 0.333286 | -0.145170 |
| depletion_plus_stricter_fidelity | irregular12 | ga_tcheby_pick_fidelityheavy | 6.536211 | 6.563657 | 0.027446 | 0.934657 | 0.932754 | -0.001903 | 0.478456 | 0.291967 | -0.186490 |

## Thesis-safe interpretation
- The strongest observed PMO-GA benefit is usually **better load spreading / lower load-balance metric**, sometimes with a very small latency penalty.
- Fidelity improvements exist in some current-like cases, but they are not universal.
- Therefore the honest claim is **tradeoff-aware separation**, not universal domination.
