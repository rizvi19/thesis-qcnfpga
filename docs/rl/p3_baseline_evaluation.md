# P3 H2/H3 Baseline Evaluation

## Scope

Step 3 implements the two mandatory pre-training comparators on the frozen P2
environment:

- H2 always selects action 0, the byte-anchored Balanced profile.
- H3 applies the Step 2 first-match threshold contract without learning.

Both controllers replay identical 512-decision Ring-6 traces. Step 3 evaluates
the eight training and four validation seeds only. Seeds 2003, 2111, 2203 and
2309 remain locked; their access count remains zero.

## Per-seed measurements

Every controller/trace pair records decisions, successes, blocking rate, mean
total reward, successful bottleneck fidelity, successful balance utility,
successful hop count, switches and all four profile counts. Metrics are retained
per environment seed so later H4 comparisons remain paired.

Bottleneck fidelity is reconstructed exactly from the frozen P2 fidelity reward
term. No reward, transition, route, state or profile definition is changed.

## Evidence

`results/rl/p3_baselines/` contains the per-seed table, aggregate descriptive
summary, profile usage, trace/config manifest and checksums. The evaluator is
required to reproduce these files byte-for-byte on repeated runs.

These are baseline results, not evidence that H4 is superior. Model selection,
held-out testing, confidence intervals and significance tests occur only after
H4 training and policy freeze.
