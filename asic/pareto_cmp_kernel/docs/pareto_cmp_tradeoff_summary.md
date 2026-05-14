# Pareto Comparator / Selector Kernel Tradeoff Summary

## Purpose

This document summarizes the ASIC/VLSI-style kernel study for the QFlow route-candidate comparator and selector logic.

The goal is to compare a full Pareto-dominance comparator against a simpler score-first practical selector.

## QFlow meaning

After QFlow computes candidate route metrics, the selector chooses which route candidate should be preferred.

Candidate metrics include:

- score: lower is better
- fidelity: higher is better
- key_count: higher is better
- hop_count: lower is better
- qber: lower is better

## Variants evaluated

| Variant | Description | Purpose |
|---|---|---|
| Pareto-C0 | Full Pareto dominance comparator plus tie-break rule | Baseline full selector |
| Pareto-C1 | Score-first priority selector | Lower-area practical selector |

## Pareto-C0 behavior

Pareto-C0 computes whether candidate A dominates candidate B or candidate B dominates candidate A.

A candidate dominates another candidate if it is no worse in all metrics and strictly better in at least one metric.

If neither candidate dominates, C0 uses a tie-break order:

1. lower score
2. higher fidelity
3. higher key_count
4. lower hop_count
5. lower qber

## Pareto-C1 behavior

Pareto-C1 does not compute full dominance. It directly applies the same priority order:

1. lower score
2. higher fidelity
3. higher key_count
4. lower hop_count
5. lower qber

This is simpler and intended as a practical low-area selector.

## Simulation result

Pareto-C0 passed the following cases:

| Case | Expected behavior |
|---|---|
| A_DOM | A dominates B |
| B_DOM | B dominates A |
| TIE | exact tie |
| A_SCORE_TB | no dominance, A wins by lower score |
| B_FID_TB | no dominance, B wins by higher fidelity |

Pareto-C1 passed the following cases:

| Case | Expected behavior |
|---|---|
| A_SCORE | A wins by lower score |
| B_SCORE | B wins by lower score |
| A_FID | A wins by higher fidelity |
| B_KEY | B wins by higher key_count |
| A_HOP | A wins by lower hop_count |
| B_QBER | B wins by lower qber |
| TIE | exact tie |

## Generic Yosys synthesis result

| Variant | Total cells | Delta vs C0 | Cell reduction vs C0 |
|---|---:|---:|---:|
| Pareto-C0 full comparator | 497 | 0 | 0.00% |
| Pareto-C1 score-first selector | 472 | -25 | 5.03% |

## Interpretation

Pareto-C1 is slightly smaller than Pareto-C0, reducing the generic Yosys cell count from 497 to 472 cells. This is a 5.03% reduction.

However, the difference is small. Therefore, the full Pareto comparator is already compact. Compared with FDPE interpolation arithmetic and SKAG weighted scoring, the Pareto selector is not a major area bottleneck.

## Current conclusion

- Use Pareto-C0 when full Pareto-dominance information is needed.
- Use Pareto-C1 when only priority-ordered route selection is required.
- The main VLSI optimization opportunity is not in the Pareto comparator; it is stronger in SKAG scoring and FDPE approximation.

## Evidence boundary

These results are generic Yosys synthesis and RTL simulation results. They are not post-layout OpenROAD results and not fabricated silicon results.
