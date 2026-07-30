# Final Thesis Numerical Audit

## Evidence snapshots

- Primary FPGA/controller evidence: branch `rl-nexys3-adaptive`, commit
  `290b4ad75eef2af2b9da2f1f281a2b89416cfd24`.
- Supporting VLSI/CMOS evidence: branch `vlsi-kernel-study`, commit
  `0093ba288f26a1520e4318f207e13f52d38db5a8`.

## Controller and policy

| Reported value | Verification/source artifact |
|---|---|
| Four radix-4 features; 4^4 = 256 states; four profile actions | `docs/rl/rl_model_card.md`, policy/state RTL, and fixed-point contract |
| 256-entry, two-bit policy ROM | `results/rl/p3_policy_freeze/freeze_record.json` and frozen policy artifact |
| Four 18-bit profile words: 13329, 1B516, 14399, 0A2A5 (hex) | profile ROM/RTL and Appendix B fixed-point contract |
| Eight policy candidates; seven eligible; selected seed 229 | `results/rl/p3_revision/selection_record.json` |
| 819,200 training transitions per candidate | retained training summaries/configuration in `results/rl/` |
| Four held-out traces × 512 decisions = 2,048 decisions/controller | held-out controller result artifacts under `results/rl/p3_heldout/` |
| Minimum dwell parameter: 3 decisions | `results/rl/p3_policy_freeze/freeze_record.json` |
| Runtime Q-value updates on FPGA: false | `results/nexys3/p6_step10_closure/final_summary.json` |

## Verification counts

| Reported value | Verification/source artifact |
|---|---|
| 256/256 encoded-state addresses; 36 threshold boundary cases; 4/4 actions | controller exhaustive verification summaries under `results/rl/p4_exhaustive/` |
| 1,509 cycle vectors; 302 valid decisions; zero unexplained mismatch | controller verification summaries under `results/rl/p4_exhaustive/` |
| 74 Python regression tests; zero lint warnings | controller verification logs under `results/rl/p4_exhaustive/` |
| Isolated controller estimate: 103 LUTs, 79 registers, 247.812 MHz | controller synthesis report; treated only as an isolated post-synthesis estimate |
| 2,125 integrated cycle vectors; 530 valid decisions | integrated verification summaries under `results/rl/p4_integrated/` |
| Candidate evaluator: 519/519; integrated policy shell: 101/101 | integrated RTL regression summaries |

## Same-board physical campaign

Primary sources: `results/nexys3/p6_step10_closure/final_summary.json` and
`thesis_ready_same_board_table.csv`.

| Quantity | Verified value |
|---|---:|
| Independent configurations | 5 (H0–H4) |
| Records/configuration | 84 |
| Physical records | 420 |
| Checked fields/record | 9 |
| Checked fields/configuration | 756 |
| Total checked fields | 3,780 |
| Mismatches | 0 |
| Implementations meeting 100 MHz | 5 |

| Configuration | Post-route fmax (MHz) | Mean cycles | Kernel latency (microseconds) | Registers | LUTs | Occupied slices |
|---|---:|---:|---:|---:|---:|---:|
| H0 | 118.948 | 2.000 | 0.020 | 493 | 801 | 301 |
| H1 | 107.538 | 201.763 | 2.018 | 1,000 | 1,484 | 589 |
| H2 | 102.838 | 202.763 | 2.028 | 1,085 | 1,650 | 649 |
| H3 | 102.648 | 202.763 | 2.028 | 1,097 | 1,836 | 645 |
| H4 | 102.020 | 204.763 | 2.047632 (2.048 rounded) | 1,156 | 1,706 | 677 |

The 2.048-microsecond value is accepted-request-to-done kernel latency at the common
100 MHz operating contract. It excludes UART serialization, host processing, KMS/SDN work,
candidate generation, security checks, and route installation.

## H4 relative to H3

Source: `results/nexys3/p6_step10_closure/final_summary.json`.

| Metric | Exact source value | Thesis rounding |
|---|---:|---:|
| Mean normal-case latency | +0.9863724849% | +0.986% |
| Post-route fmax | -0.6117995480% | -0.612% |
| LUT count | -7.0806100218% | -7.081% |
| Register count | +5.3783044667% | +5.378% |
| Occupied slices | +4.9612403101% | +4.961% |
| Profile transitions | -45.4545454545% | -45.455% |

The transition comparison is 44 transitions for configuration H3 versus 24 for
configuration H4 over 81 valid adaptive decisions. Profile counts are (24, 36, 18, 3) for
H3 and (42, 11, 18, 10) for H4. The thesis attributes the reduction to the complete H4
policy-ROM-plus-dwell controller, not to reinforcement learning alone.

## Held-out physical route-quality statistics

Source: `results/nexys3/p6_step10_closure/thesis_ready_pairwise_statistics.csv` and the
corresponding section of `final_summary.json`.

| Comparison | Joint pairs | Mean difference | Bootstrap 95% CI | Sign-test p | dz | Path changes |
|---|---:|---:|---:|---:|---:|---:|
| H4 vs H2 | 58 | 86.465517 | [-23.517241, 228.224138] | 0.218750 | 0.176084 | 6 |
| H4 vs H3 | 58 | -78.051724 | [-242.534483, 79.931034] | 0.453125 | -0.126716 | 7 |

Both intervals cross zero. The thesis therefore reports that route-quality superiority is
not established and retains the non-support of RH5.

## Supporting VLSI and CMOS evidence

| Reported value | Verification/source artifact |
|---|---|
| SKAG specialized scoring: 5,343 to 503 generic cells; 90.585813% reduction | `asic/skag_weight_kernel/results/skag_yosys_comparison.csv` |
| SKAG-W1 routed area 6,451 square micrometres, 26% utilization | `results/partC_vlsi/openroad_skag_w1/logs/6_report.log` |
| FDPE-V3 routed area 22,186 square micrometres, 13% utilization | `results/partC_vlsi/openroad_fdpe_v3/logs/6_report.log` |
| Pareto-C0 routed area 3,368 square micrometres, 13% utilization | `results/partC_vlsi/openroad_pareto_c0/logs/6_report.log` |
| Transmission-gate mux at 20 fF: 26.635155 ps average delay | `results/partD_cmos/pareto_cmp_primitive/load_sweep/tg_mux_load_sweep.csv` |
| Analytical 0.5 C V^2 quantity at 20 fF and 1.8 V: 32.4 fJ | same load-sweep CSV; explicitly not measured QFlow energy |

The three routed areas remain separate isolated-kernel results and are not summed or called
an integrated QFlow ASIC area.

## Document/build quantities

| Quantity | Result |
|---|---:|
| Baseline compiled PDF | 68 pages at the start of the scientific-integrity pass |
| Revised compiled PDF | 97 pages |
| Abstract length | approximately 369 words |
| Bibliography records | 41 |
| Citation commands | 42 |
| Undefined references/citations | 0 |
| Overfull boxes | 0 |
| Rendered pages visually inspected | 97 |

This first-pass audit is retained for package continuity. The authoritative second-pass
mapping is `FINAL_NUMERICAL_TRACEABILITY.md`; the scientific interpretation audit is
`SCIENTIFIC_SEMANTIC_CONSISTENCY_REPORT.md`.
