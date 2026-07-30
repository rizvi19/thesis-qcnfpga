# Final Thesis Numerical Traceability

## Evidence snapshots

- FPGA/controller evidence: branch `rl-nexys3-adaptive`, commit
  `290b4ad75eef2af2b9da2f1f281a2b89416cfd24`.
- VLSI/CMOS evidence: branch `vlsi-kernel-study`, commit
  `0093ba288f26a1520e4318f207e13f52d38db5a8`.
- Thesis source: branch `thesis-final-submission-corrections`; exact remotely
  resolvable source SHA is embedded in Appendix A after the source commit.

## Controller and numeric contract

| Quantity | Value | Source |
|---|---:|---|
| State features/address space | 4 radix-4 fields / 256 states | `rl/ring6_environment.py`; policy-shell RTL |
| Feature thresholds | K: .25/.50/.75; Q: .90/.93/.96; load: .25/.50/.75; imbalance: .125/.25/.50 | model/threshold manifests |
| Profile payloads Pi0--Pi3 | `0x13329`, `0x1B516`, `0x14399`, `0x0A2A5` | `rl/config/profile_codebook_v0.json`; profile ROM |
| Policy ROM | 256 x 2 bits; counts 145/43/44/24 | freeze record and frozen policy |
| Minimum dwell | 3 accepted decisions | H4 RTL/reference |
| Path-cost UQ16.16 finite maximum | `0xFFFFFFFE = 2^16 - 2^-15` | mini-contract and SKAG reference |
| Path-cost infinity | `0xFFFFFFFF` | mini-contract and SKAG reference |
| Utilization UQ16.16 maximum | `0xFFFFFFFF = 2^16 - 2^-16`; no infinity sentinel | candidate-evaluator contract/RTL |

The software-training action uses four alpha coefficients and three objective ratios.
The physical candidate evaluator consumes only the three ratios because path cost is
supplied precomputed. See `PROFILE_TRAINING_DEPLOYMENT_SEMANTICS_REPORT.md`.

## Verification counts

| Quantity | Value | Source family |
|---|---:|---|
| Encoded states | 256/256 | `results/rl/p4_exhaustive/` |
| Threshold boundary cases | 36 | `results/rl/p4_exhaustive/` |
| Policy actions exercised | 4/4 | `results/rl/p4_exhaustive/` |
| Python tests / lint warnings | 74 / 0 | `results/rl/p4_exhaustive/` |
| Candidate-evaluator vectors | 519/519 | `results/rl/p4_integrated/` |
| Policy-shell vectors | 101/101 | `results/rl/p4_integrated/` |

## Same-board H0--H4 campaign

Sources: `results/nexys3/p6_step10_closure/final_summary.json`, the per-mode physical
rows, and `data/p6_same_board.csv`.

| Mode | fmax MHz | Mean cycles | Latency at 100 MHz, us | Registers | LUTs | Slices |
|---|---:|---:|---:|---:|---:|---:|
| H0 | 118.948 | 2.000000 | 0.020000 | 493 | 801 | 301 |
| H1 | 107.538 | 201.763158 | 2.017632 | 1,000 | 1,484 | 589 |
| H2 | 102.838 | 202.763158 | 2.027632 | 1,085 | 1,650 | 649 |
| H3 | 102.648 | 202.763158 | 2.027632 | 1,097 | 1,836 | 645 |
| H4 | 102.020 | 204.763158 | 2.047632 | 1,156 | 1,706 | 677 |

There are five independently built implementations, 84 records per implementation,
420 records total, nine compared fields per record, 3,780 exact field comparisons,
and zero mismatches. H0 is a feasible minimum-hop baseline, not a distance baseline.

H4 versus H3 changes are: +0.986% mean latency, -0.612% maximum frequency,
-7.081% LUTs, +5.378% registers, and +4.961% occupied slices. These are mapping-
specific physical results, not universal RL resource properties.

## Adaptive behavior and paired route quality

| Mode | Pi0 | Pi1 | Pi2 | Pi3 | Transitions | Valid decisions |
|---|---:|---:|---:|---:|---:|---:|
| H3 | 24 | 36 | 18 | 3 | 44 | 81 |
| H4 | 42 | 11 | 18 | 10 | 24 | 81 |

The physical bootstrap reads the raw H2/H3/H4 rows at the evidence commit.
Executable: `reproduce_physical_bootstrap.py`. Summary:
`data/physical_bootstrap_recomputed.csv`. Row differences:
`data/physical_paired_differences.csv`.

| Comparison | Pairs | Mean UNORM16 | Normalized mean | Bootstrap 95% CI | Sign p | dz | Path changes |
|---|---:|---:|---:|---:|---:|---:|---:|
| H4-H2 | 58 | 86.465517 | 0.00131938 | [-25.120690, 226.620690] | 0.218750 | 0.176084 | 6 |
| H4-H3 | 58 | -78.051724 | -0.00119099 | [-242.281466, 77.534483] | 0.453125 | -0.126716 | 7 |

Intervals use 10,000 paired-row nonparametric percentile replicates, Python MT19937
seed 20260731, and R-7 linear quantiles. Both cross zero; route-quality superiority
is not established.

## Supporting isolated VLSI/CMOS quantities

| Quantity | Value | Source |
|---|---:|---|
| SKAG generic synthesis | 5,343 to 503 cells; 90.585813% reduction | SKAG Yosys comparison |
| SKAG-W1 routed area/utilization | 6,451 um^2 / 26% | OpenROAD report |
| FDPE-V3 routed area/utilization | 22,186 um^2 / 13% | OpenROAD report |
| Pareto-C0 routed area/utilization | 3,368 um^2 / 13% | OpenROAD report |
| 2:1 mux average delay at 20 fF | 26.64 ps | load-sweep CSV |
| Analytical 0.5 C V^2 at 20 fF, 1.8 V | 32.4 fJ | load-sweep CSV |

These are separate kernels and a primitive/load calculation. They are not summed or
presented as an integrated QFlow ASIC, measured accelerator energy, or commercial
cost.
