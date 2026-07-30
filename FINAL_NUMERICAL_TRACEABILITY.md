# Final Numerical Traceability

## Evidence snapshots

- Primary FPGA/controller evidence: branch `rl-nexys3-adaptive`, commit
  `290b4ad75eef2af2b9da2f1f281a2b89416cfd24`.
- Supporting VLSI/CMOS evidence: branch `vlsi-kernel-study`, commit
  `0093ba288f26a1520e4318f207e13f52d38db5a8`.
- Submission extracts used by the thesis are retained under `data/`; they are compact
  copies of or reductions from the registered results, not new measurements.

## Semantic, policy, and training values

| Thesis quantity | Value | Authoritative source |
|---|---:|---|
| Deployed state features | 4 radix-4 fields, 256 addresses | `docs/rl/rl_model_card.md`; state-threshold manifest; H4 RTL/reference |
| Feature thresholds: occupancy | 0.25, 0.50, 0.75 | training/MDP configuration and threshold manifest |
| Feature thresholds: route quality | 0.90, 0.93, 0.96 | training/MDP configuration and threshold manifest |
| Feature thresholds: offered load | 0.25, 0.50, 0.75 | training/MDP configuration and threshold manifest |
| Feature thresholds: imbalance | 0.125, 0.25, 0.50 | training/MDP configuration and threshold manifest |
| Profile payloads Pi0-Pi3 | `13329`, `1B516`, `14399`, `0A2A5` hex | registered profile manifest and profile-ROM RTL |
| Policy ROM | 256 x 2 bits; action counts (145, 43, 44, 24) | `results/rl/p3_policy_freeze/freeze_record.json` and frozen policy file |
| Policy candidates | 8 trained; 7 eligible; seed 229 selected | `results/rl/p3_revision/selection_record.json` |
| Training volume | 819,200 transitions per candidate | retained training configuration/summaries |
| Held-out evaluation | 4 traces x 512 decisions = 2,048 decisions/controller | registered held-out summaries; `data/p3_heldout_summary.json` |
| H4 held-out reward | 4.677079357437266 | `data/p3_heldout_summary.json` |
| Minimum dwell | 3 accepted decisions | freeze record and H4 RTL/reference |
| Runtime Q update | No | H4 RTL/reference and closure summary |

Reward values in the thesis resolve to the registered training implementation. The
successful-decision reward is `4 + 2 U_q + U_b - 0.25 h - 0.25 switch`; blocking is
`-4`, or `-4.25` when a profile switch also occurs. The validation-only revision changes
the balance coefficient from one to four; the final physical replay still evaluates
the original registered scale.

## Verification counts

| Quantity | Value | Registered source family |
|---|---:|---|
| Encoded-state addresses | 256/256 | `results/rl/p4_exhaustive/` |
| Threshold boundary cases | 36 | `results/rl/p4_exhaustive/` |
| Policy actions exercised | 4/4 | `results/rl/p4_exhaustive/` |
| Controller cycle vectors / valid decisions | 1,509 / 302 | `results/rl/p4_exhaustive/` |
| Python regression tests / lint warnings | 74 / 0 | `results/rl/p4_exhaustive/` |
| Candidate evaluator vectors | 519/519 | `results/rl/p4_integrated/` |
| Integrated policy-shell vectors | 101/101 | `results/rl/p4_integrated/` |
| Integrated cycle vectors / valid decisions | 2,125 / 530 | `results/rl/p4_integrated/` |

## Same-board H0-H4 physical campaign

Primary registered sources are
`results/nexys3/p6_step10_closure/final_summary.json` and
`results/nexys3/p6_step10_closure/thesis_ready_same_board_table.csv`. The retained
submission extract is `data/p6_same_board.csv`.

| Mode | fmax (MHz) | Mean cycles | Kernel latency at 100 MHz (us) | Registers | LUTs | Slices |
|---|---:|---:|---:|---:|---:|---:|
| H0 | 118.948 | 2.000000 | 0.020000 | 493 | 801 | 301 |
| H1 | 107.538 | 201.763158 | 2.017632 | 1,000 | 1,484 | 589 |
| H2 | 102.838 | 202.763158 | 2.027632 | 1,085 | 1,650 | 649 |
| H3 | 102.648 | 202.763158 | 2.027632 | 1,097 | 1,836 | 645 |
| H4 | 102.020 | 204.763158 | 2.047632 | 1,156 | 1,706 | 677 |

There are five independent implementations, 84 records per implementation, 420 total
physical records, nine checked fields per record, 3,780 checked fields, and zero
mismatches. Each full physical replay contains 76 OK, five NO_PATH, and three
INVALID_REQUEST records. Each 64-row held-out subset contains 58 OK, four NO_PATH, and
two INVALID_REQUEST records. These counts are shared by construction because hard
feasibility inputs are common across modes.

The 2.047632 us H4 value is accepted-request-to-done kernel latency at the common
100 MHz contract. It excludes UART serialization, host work, candidate generation,
KMS/SDN control, security validation, and route installation.

Official H4 capacity reporting is 1,156/18,224 registers (6%), 1,706/9,112 LUTs (18%),
677/2,278 occupied slices (29%), 0/32 block RAMs (0%), 0/32 DSP48A1 blocks (0%), and
one clock resource/BUFG. Zero BRAM and DSP values are taken from the official report,
not inferred.

## Adaptive behavior and paired route-quality results

Sources: `data/p6_adaptation.csv`, `data/p6_pairwise.csv`, and the corresponding
registered `p6_step10_closure` summaries.

| Mode | Pi0 | Pi1 | Pi2 | Pi3 | Transitions | Decisions |
|---|---:|---:|---:|---:|---:|---:|
| H3 | 24 | 36 | 18 | 3 | 44 | 81 |
| H4 | 42 | 11 | 18 | 10 | 24 | 81 |

The 81 decisions are the 84 records minus three invalid requests. Valid no-path rows are
included because they still exercise state quantization and controller behavior.

| Comparison | Joint OK pairs | Mean difference (UNORM16) | Normalized difference | Bootstrap 95% CI | Sign-test p | dz | Path changes |
|---|---:|---:|---:|---:|---:|---:|---:|
| H4-H2 | 58 | +86.465517 | +0.00131938 | [-23.517241, 228.224138] | 0.218750 | 0.176084 | 6 |
| H4-H3 | 58 | -78.051724 | -0.00119099 | [-242.534483, 79.931034] | 0.453125 | -0.126716 | 7 |

UNORM16 ranges from 0 to 65,535; larger is better and one LSB is `1/65535`.
Both intervals cross zero, so the thesis does not claim route-quality superiority.
The sign test is exact and two-sided over nonzero differences; zeros are reported as
ties and excluded from the binomial trial count. `d_z` is the paired mean difference
divided by its sample standard deviation. No multiplicity correction is claimed for
these two exploratory physical comparisons. The registered bootstrap repetition count
and seed were not preserved, and the thesis discloses that limitation.

## Supporting isolated VLSI/CMOS quantities

| Quantity | Value | Source |
|---|---:|---|
| SKAG generic synthesis | 5,343 to 503 cells; 90.585813% reduction | `asic/skag_weight_kernel/results/skag_yosys_comparison.csv` |
| SKAG-W1 routed area/utilization | 6,451 um^2 / 26% | `data/openroad_physical_summary.csv`; registered OpenROAD report |
| LUT/interpolation kernel FDPE-V3 routed area/utilization | 22,186 um^2 / 13% | same source family |
| Pareto-C0 routed area/utilization | 3,368 um^2 / 13% | same source family |
| 2:1 transmission-gate mux at 20 fF | 26.64 ps average delay | `data/tg_mux_20ff_summary.csv` |
| Analytical 0.5 C V^2 at 20 fF, 1.8 V | 32.4 fJ | `data/tg_mux_20ff_summary.csv` |

The routed areas are three separate kernels and are never summed into a complete QFlow
ASIC. The 32.4 fJ quantity is an analytical load-transition estimate, not measured
QFlow energy.

## Traceability conclusion

All headline numerical results in the revised thesis resolve to a registered source or
to a retained compact extract listed above. Missing metadata is disclosed, and no
number was synthesized to fill a gap.
