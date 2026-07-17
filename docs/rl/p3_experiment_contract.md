# P3 Experiment and Decision Contract

## Purpose

P3 determines whether a four-action, offline-trained tabular Q-learning policy
adds value beyond H2 forced-fixed and H3 deterministic threshold control before
any P4 RTL work is accepted. This document freezes the experiment before
training. It does not report a learned-policy result.

## Controller matrix

All controllers use the same Ring-6 traces, state encoder, four-profile
codebook, reward, transition order and candidate-route logic.

- **H2:** action 0 (Balanced) on every decision.
- **H3:** a non-learning, deterministic threshold controller. Priority is
  critical key scarcity -> marginal fidelity -> high imbalance -> safe
  saturated low-latency -> Balanced default.
- **H4:** a 256-state by 4-action tabular Q-learning controller trained offline.
  Deployment is deterministic policy inference, not on-chip learning.

The four actions remain the P2 codebook. Eight-action training is not authorized
unless the four-action validation result later justifies a separately frozen
extension.

## Frozen H3 rules

The decoded state bins are ordered as key occupancy, bottleneck fidelity,
offered load and utilization imbalance. The first matching rule wins:

1. key bin 0 -> action 1, Scarcity protection;
2. fidelity bin 0 or 1 -> action 2, Fidelity protection;
3. imbalance bin 2 or 3 -> action 1, Scarcity protection;
4. load bin 3 with key and fidelity bins at least 2 and imbalance at most 1 ->
   action 3, Low-latency;
5. otherwise -> action 0, Balanced.

These rules are frozen before H3 results are generated. They are not fitted to
the validation or test partitions.

## Frozen H4 training

Each of eight trainer RNG seeds trains one Q-table. A trainer executes 200
epochs; every epoch visits all eight training traces once, for 819,200
transitions per trainer. Q-values start at zero. Learning rate is 0.10,
discount is 0.95 and terminal bootstrap is zero. Epsilon decreases linearly
from 1.00 to 0.05 over the first 80% of training transitions and then remains
0.05. Early stopping and hyperparameter sweeps are disabled.

Training uses the explicit xorshift32 generator for trace ordering, exploration
and random training tie breaks. Evaluation and deployment break equal Q-values
by the smallest action ID. Only the epoch-200 table is eligible for selection.

## Partition discipline

- Training traces: seeds 101, 211, 307, 401, 503, 601, 701 and 809.
- Validation traces: seeds 1009, 1103, 1201 and 1301.
- Test traces: seeds 2003, 2111, 2203 and 2309.

Validation selects one final-epoch trainer candidate. The test partition remains
locked until that policy, Q-table, configuration and selection record have
checksums. Test results cannot cause a policy, reward, state or hyperparameter
revision.

## Model selection

A validation candidate must use at least two profiles, give the secondary
profile at least 1% of decisions, remain within 0.5 percentage point absolute
blocking of H2 and keep switching at or below 25%. Eligible candidates are
ranked by mean total reward, blocking, successful bottleneck fidelity, switching
and finally trainer seed. If none is eligible, a safety-first candidate is
retained for diagnosis and at most one validation-only controlled revision is
allowed before the final policy freeze.

## Metrics and statistics

The primary quality metric is mean total reward. Blocking rate and successful
bottleneck fidelity are safety metrics. Balance utility, successful hops,
switching and complete profile usage are also reported per trace seed.

H4-H2 and H4-H3 comparisons are paired by environment seed. Reporting includes
paired means, a 95% paired percentile-bootstrap interval using 10,000 resamples,
an exact two-sided paired permutation test, raw paired mean difference and
paired Cohen's dz when defined. Holm correction covers the two primary
comparisons. With only four held-out seeds, insufficient power must be stated;
statistical superiority is claimed only when the interval excludes zero and the
corrected p-value is below 0.05.

## Predeclared P3 utility gate

H4 must use at least two profiles, remain within the 0.005 absolute blocking
margin of H2, keep switching at or below 0.25 and exceed both H2 and H3 in
held-out mean total reward. Successful bottleneck fidelity may not degrade by
more than 0.005 absolute and balance utility may not degrade by more than 0.05.
All seeds, intervals, tests, effects and adverse metrics are reported.

If H4 equals H3 while costing more, H3 is used for the defense demonstration.
If H4 fails validation safety, only one controlled pre-test revision is
permitted. Negative or inconclusive results are retained honestly.

## Scope firewall

P3 does not include DQN, neural networks, on-chip learning, RTL, synthesis,
board programming, an eight-action sweep, a new ASIC flow or any claim of
online FPGA learning.
