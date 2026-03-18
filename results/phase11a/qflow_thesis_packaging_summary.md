# QFlow thesis packaging summary

## Timing-closure progression

| stage | kind | WNS_ns | TNS_ns | delay_ns | approx_Fmax_MHz | timing_met | worst_path |
|---|---|---:|---:|---:|---:|---|---|
| tc3 | post-synthesis | -68.443 | -1412.372 | 78.292 | 12.773 | no | `u_skag/fdpe_s0_fidelity_reg[0]/C -> u_skag/fdpe_s1_dyn_term_reg[0]/D` |
| tc4 | post-synthesis | -8.154 | -178.942 | 18.002 | 55.549 | no | `u_fdpe/s1_f_init_reg[15]/C -> u_fdpe/s2_result_reg[0]/D` |
| tc5 | post-synthesis | 0.033 | 0.000 | 9.815 | 101.885 | yes | `u_fdpe/s1_y0_reg[6]/C -> u_fdpe/s2_decay_reg[14]/D` |
| tc5_ooc_impl | OOC post-route | 0.039 | 0.000 | - | 100.392 | no | `None -> None` |

OOC route confirmation: routable=3828, fully_routed=3828, routing_errors=0, WHS_ns=0.098, THS_ns=0.000.

## Baseline comparison by topology

| topology | best_latency | best_fidelity | best_load_balance | distance_latency | keyaware_latency | random_latency | ga_latency | keyaware_vs_ga_same_latency |
|---|---|---|---|---:|---:|---:|---:|---|
| mesh9 | dijkstra_keyaware | random_valid_path | dijkstra_distance | 6.320 | 6.225 | 7.356 | 6.225 | yes |
| mesh16 | dijkstra_keyaware | dijkstra_keyaware | dijkstra_keyaware | 9.848 | 9.529 | 12.160 | 9.529 | yes |
| irregular12 | dijkstra_keyaware | dijkstra_keyaware | dijkstra_keyaware | 6.345 | 6.196 | 9.142 | 6.196 | yes |

## GA vs key-aware path-match stability

| topology | request | src | dst | ga_matches_keyaware_rate |
|---|---:|---:|---:|---:|
| mesh9 | 0 | 0 | 8 | 1.000 |
| mesh9 | 1 | 2 | 6 | 1.000 |
| mesh9 | 2 | 0 | 5 | 1.000 |
| mesh9 | 3 | 1 | 7 | 1.000 |
| mesh16 | 0 | 0 | 15 | 1.000 |
| mesh16 | 1 | 3 | 12 | 1.000 |
| mesh16 | 2 | 1 | 14 | 1.000 |
| mesh16 | 3 | 4 | 11 | 1.000 |
| irregular12 | 0 | 0 | 11 | 1.000 |
| irregular12 | 1 | 1 | 10 | 1.000 |
| irregular12 | 2 | 4 | 7 | 1.000 |
| irregular12 | 3 | 2 | 9 | 1.000 |

## Thesis-safe interpretation

- tc5 is the first post-synthesis variant that clears the 10 ns target.

- OOC post-route also meets timing, so the core hardware timing claim is strong.

- On the current baseline suites, key-aware shortest path beats plain distance routing on latency in the harder topologies and random routing is clearly weakest.

- Software PMO-GA matches key-aware shortest path on the current evaluation suites, so the present data supports hardware/software acceleration claims and key-awareness claims more strongly than GA-vs-key-aware solution-quality superiority claims.

