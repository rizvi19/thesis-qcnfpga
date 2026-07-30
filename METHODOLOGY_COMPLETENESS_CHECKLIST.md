# Methodology Completeness Checklist

Authoritative FPGA snapshot: `rl-nexys3-adaptive` at
`290b4ad75eef2af2b9da2f1f281a2b89416cfd24`.

## Candidate and fixed-point contract

- [x] Every H0-H4 candidate field is tabulated: validity, path cost, bottleneck
  route-quality code, utilization objective, hop count, and candidate slot.
- [x] Meaning, source, route aggregation, width, signedness/format, numerical range,
  saturation, infinity, and invalid-input behavior are stated.
- [x] UNORM16 and UQ16.16 encodings are defined, including round-half-up behavior,
  saturation, and exact comparison order.
- [x] Worked fixed-point encoding, normalization, product, max, and tie-break examples
  are included.

## State and policy

- [x] The four deployed features are minimum key occupancy, bounded bottleneck
  route-quality code, offered request load, and utilization imbalance.
- [x] All three numerical thresholds per feature are given in real and encoded form.
- [x] Threshold equality enters the higher bin; below, at, and above cases are tested.
- [x] The radix-4 state address and bit layout are defined.
- [x] Pi0-Pi3 registered names, alpha coefficients, Tchebycheff weights, hardware
  ratios, and packed 18-bit payloads are listed.
- [x] “Low-latency” is defined as path-cost/hop preference, not hardware run time.

## Exact H0-H4 behavior

- [x] H0 feasible shortest-distance selection is specified.
- [x] H1 fixed key-aware scoring is specified.
- [x] H2 forced Pi0 evaluation is specified.
- [x] H3 first-match rule order and complete Pi0-Pi3 action table are specified.
- [x] H4 256-entry policy-ROM lookup and minimum-dwell behavior are specified.
- [x] Feasibility, no-path, invalid request, stable slot tie-break, and score direction
  are explicit.
- [x] `N_c`, `o_min`, `I_b`, ideal point `z*`, normalized penalties, route objectives,
  and the relation between alpha path cost and Tchebycheff selection are defined.

## Reward and training

- [x] Complete immediate reward equation and Q-learning update are present.
- [x] Success/blocking, route-quality, balance, hop, and profile-switch terms have
  coefficients, signs, ranges, and activation conditions.
- [x] The validation-only balance-weight revision is distinguished from the original
  evaluation reward; no new reward was invented.
- [x] A reward near 4.67 is interpreted as a dimensionless average under the stated
  synthetic contract, not as a physical QKD metric.
- [x] Environment/topology, candidate generation, candidate count, initialization,
  demand/resource evolution, episode length, and terminal behavior are documented.
- [x] Training, validation, test, and trainer seeds are separated; independence limits
  are stated.
- [x] Q-table initialization, exploration schedule, ranking/revision rules, eight
  candidates, seven eligible candidates, seed 229 selection, and freeze point are
  documented.
- [x] Offline training and ROM-only FPGA inference are explained.

## RTL and timing

- [x] Detailed architecture contains input registers, quantizers, radix-4 encoder,
  policy ROM, profile ROM, H3 controller, dwell controller, candidate storage/stream,
  feasibility/range logic, normalizer, ratio products/Tchebycheff max, winner/tie
  registers, FSM, cycle counter, and status/result registers.
- [x] Supported field, state, policy, profile, score, and datapath widths are shown.
- [x] Request acceptance, initialization/bypass, iterative evaluation, comparison,
  commit, and output stability are described.
- [x] H0 two-cycle behavior, H1 roughly 202-cycle behavior, H2/H3 extra cycle, and H4
  controller/dwell increment are tied to RTL/replay measurements without speculative
  pipeline attribution.

## Physical protocol and verification

- [x] UART request ordering, bit/byte convention, candidate count, state/profile
  fields, and busy handling are documented.
- [x] Status codes OK, NO_PATH, and INVALID_REQUEST are defined.
- [x] Nine checked fields are listed: request ID, policy ID, state ID, profile ID,
  selected path/slot, score, route-quality code, result/status, and cycles.
- [x] Invalid and no-path response payload behavior is defined.
- [x] Software, state/policy, candidate evaluator, integrated RTL, synthesis,
  implementation, and physical replay verification levels are separated.

## Statistics

- [x] Pairing unit is the jointly successful physical replay row.
- [x] Route-quality direction and UNORM16 units are defined.
- [x] Bootstrap intervals are identified as percentile confidence intervals over
  paired rows.
- [x] Exact two-sided sign tests exclude zero differences; ties are reported.
- [x] Paired effect size uses `d_z = mean(delta)/sd(delta)` for nonzero variance.
- [x] No multiple-comparison correction was applied to the two physical exploratory
  comparisons, and both are interpreted as non-significant.
- [!] The retained physical summary does not preserve bootstrap repetition count or
  random seed. This missing metadata is disclosed in the thesis and is not fabricated.

## Results interpretation and presentation

- [x] Common physical and held-out status counts are explained as a shared hard
  feasibility contract.
- [x] The 81 adaptive decisions exclude the three invalid rows; valid no-path rows
  remain controller decisions.
- [x] Resource reporting gives used/available capacity, percentages, BRAM, DSP, clock
  resources, and device slice capacity where officially reported; missing quantities
  are not inferred as zero.
- [x] Route-quality integer effects are translated to normalized units.
- [x] Timing/resource/transition trade-offs and fair comparison boundaries are stated.
- [x] Verification ladder, detailed RTL, trade-off, paired-CI, and isolated-kernel
  routed-layout figures are present and technically captioned.
- [x] Related-work comparisons preserve differing functions and measurement boundaries.

Result: complete at reproducible thesis level, with the single unavailable bootstrap
metadata item explicitly marked rather than reconstructed.
