# QFlow-RL Frozen Controller Model Card

## Identity and decision

- Model ID: `qflow_rl_tabular_h4_seed229_dwell3_v1`
- Phase: P3, frozen after the single permitted validation-only revision.
- Selected trainer seed: 229.
- Controller: offline tabular Q-learning policy with a three-decision minimum dwell guard.
- Utility decision: `PASS_DESCRIPTIVE_INSUFFICIENT_POWER`.
- P4 status: authorized for the frozen controller; no policy revision is allowed.

## Inputs and outputs

The policy addresses 256 states formed from four radix-4 features in this order:
minimum key occupancy, bottleneck fidelity, offered request load and utilization
imbalance. Each state returns one of four two-bit profile IDs: Balanced, scarcity
protection, fidelity protection or low-latency.

## Training and selection

Training was offline only. Eight train seeds, four validation seeds and eight
trainer seeds were frozen before learning. Each candidate completed 819,200
transitions. The initial run triggered the one permitted validation-only
revision. Revision v1 used balance weight 4.0 for learning targets and dwell 3
for deployment. Final evaluation retained the original frozen reward. Seed 229
was selected mechanically from seven eligible candidates. Test data was not
used for training, revision or selection.

## Held-out evidence and claim boundary

Across four untouched 512-decision test traces, H4 achieved mean reward
4.677079357437266, zero blocking, fidelity 0.96043583984375, balance utility
0.2649934199372676, mean hops 2.9541015625 and switch rate
0.2328767123287671. H4 reward exceeded H2 and H3 on all four paired seeds.

The paired bootstrap intervals excluded zero, but the exact two-sided paired
permutation p-value was 0.125 and Holm-adjusted p-value was 0.25. Four pairs
cannot attain p<0.05. The permitted claim is therefore a held-out descriptive
improvement and complete utility-gate pass, not statistical superiority.

## Deployment representation

- `policy_rom.mem`: 256 state-major one-hex-digit profile IDs (2 useful bits).
- `q_table.mem`: 1,024 state-major/action-minor signed 16-bit Q8.7 hex words.
- `profile_rom.mem`: four 18-bit payloads stored in five hex digits.
- Profile layout: alpha numerators `[17:15],[14:12],[11:9],[8:6]`, followed by
  Tchebycheff integer ratios `[5:4],[3:2],[1:0]`.
- Q quantization maximum absolute error: 0.0038979528920037865.
- Quantized-Q/policy argmax mismatches: 0.

The policy ROM is the deployed decision artifact. The Q-table is retained for
reproducibility and audit; online or on-chip learning is not claimed.

## Intended use and limitations

The controller is intended for the frozen Ring-6 QFlow research architecture
and subsequent same-board H2/H3/H4 FPGA comparison. It is not validated for
arbitrary network topologies, production QKD operation or safety-critical
autonomous deployment. P3 provides Python/reference-model evidence only. RTL,
synthesis, timing, power and physical-board evidence begin in later phases.

Defense-level feature/reward/dwell diagnostics are available. A broader
retrained ablation matrix and more held-out seeds remain journal-expansion work.
