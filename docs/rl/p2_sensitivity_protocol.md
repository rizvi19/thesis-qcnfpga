# P2 Profile Sensitivity Protocol

## Purpose

The canonical uniform Ring-6 smoke test changes weighted path values but does
not distinguish routing decisions. Therefore the three adaptive actions are
selected on deterministic asymmetric Ring-6 stress fixtures before their
coefficients are frozen.

These fixtures are controlled sensitivity cases, not board measurements,
training traces, held-out evaluation data, or evidence of network-level
superiority.

## Decision boundary

Each candidate path uses the existing QFlow objective definitions:

1. summed SKAG composite path cost;
2. bottleneck fidelity; and
3. maximum utilization imbalance `(consumed + 1) / key_count`.

The objectives are converted to minimization form and normalized by the
candidate-set ideal/nadir range with epsilon `2^-16`. The selected route is the
minimum normalized weighted-Tchebycheff score. This makes `lambda_TCH` part of
the actual route-selection boundary instead of using it only for convergence
reporting.

The legacy H2 function and canonical H2 result hash are not changed. Action 0
(Balanced) must still select the first legacy H2 route on the canonical case.

## Fixtures

Five deterministic cases are used:

- three equal-hop resource-versus-fidelity tradeoffs from node 0 to node 3;
- one moderate short-path-versus-quality tradeoff from node 0 to node 2; and
- one severe short-path-versus-quality tradeoff from node 0 to node 2.

Every path is simple and uses only edges of the six-node ring. Link values are
stress fixtures chosen to expose intended controller behavior; they must not be
presented as measured QKD deployment values.

## Candidate selection rule

A profile is eligible only if it:

1. chooses the intent-labelled path in all five fixtures; and
2. has a normalized Tchebycheff score margin of at least `0.19` in every case.

Eligible candidates are ranked, in order, by:

1. minimum L1 alpha distance from the Balanced H2 anchor;
2. minimum sum of the integer `lambda_TCH` hardware ratio;
3. maximum mean score margin; and
4. coefficient tuple as a deterministic final tie-break.

This rule favors the smallest hardware-friendly change that expresses the
required behavior. It prevents choosing more extreme coefficients merely
because they produce a larger synthetic margin.

## Evidence

The executable protocol writes controlled outputs under
`results/rl/p2_sensitivity/`, including the complete candidate ranking,
selected-profile scenario matrix, selection summary, and checksums.
