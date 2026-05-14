# SKAG Weight Kernel Area Tradeoff Summary

## Purpose

This document summarizes the ASIC/VLSI-style kernel study for the QFlow SKAG edge-weight computation.

The goal is to compare a flexible runtime-weighted score kernel against a lower-cost fixed-alpha shift-add score kernel.

## QFlow meaning

SKAG stores live edge-state information for QKD-style routing decisions. Each edge may include:

- key_count
- avg_fidelity
- arrival_rate
- qber

The edge score is used by the route-selection logic to prefer edges with enough key material, higher fidelity, better arrival behavior, and lower QBER.

Lower score means better edge.

## Variants evaluated

| Variant | Description | Purpose |
|---|---|---|
| SKAG-W0 | Runtime weighted bucket score using four 16x16 products | Flexible baseline |
| SKAG-W1 | Fixed-alpha shift-add score | Low-area optimized variant |

## Score model

The W0 baseline computes:

score =
  alpha_k * key_shortage
+ alpha_f * fidelity_penalty
+ alpha_l * arrival_penalty
+ alpha_q * qber

The W1 optimized version freezes the weights:

- alpha_k = 1.0
- alpha_f = 1.5
- alpha_l = 0.5
- alpha_q = 2.0

So the score becomes:

score =
  key_shortage
+ fidelity_penalty
+ (fidelity_penalty >> 1)
+ (arrival_penalty >> 1)
+ (qber << 1)

This removes runtime multiplication and replaces it with shift-add logic.

## Simulation result

Both W0 and W1 produced the same tested score outputs:

| Case | Description | Score |
|---|---|---:|
| 1 | Good edge | 2502 |
| 2 | Moderate edge | 9494 |
| 3 | Bad edge | 27660 |
| 4 | No-key style edge | 7254 |

This confirms that W1 preserves the tested W0 score behavior for the fixed alpha configuration.

## Generic Yosys synthesis result

| Variant | Total cells | Delta vs W0 | Cell reduction vs W0 |
|---|---:|---:|---:|
| SKAG-W0 runtime weighted score | 5343 | 0 | 0.00% |
| SKAG-W1 fixed-alpha shift-add | 503 | -4840 | 90.59% |

## Interpretation

SKAG-W0 is flexible but expensive because it uses four runtime 16x16 weighted products.

SKAG-W1 is much smaller because it replaces those products with shift-add logic. For the tested alpha configuration, W1 preserves the same score outputs while reducing generic Yosys cell count by approximately 90.59%.

This is a strong VLSI co-design result: if the alpha weights are fixed or selected from a small configuration set, the SKAG edge-scoring kernel can be made much smaller.

## Important caveat

W1 is not a universal replacement for W0. W0 supports runtime-configurable alpha weights, while W1 assumes fixed alpha values.

Therefore:

- Use W0 when runtime tunability is required.
- Use W1 when area/power efficiency is more important and the weight policy is fixed.

## Evidence boundary

These results are generic Yosys synthesis and RTL simulation results. They are not post-layout OpenROAD results and not fabricated silicon results.
