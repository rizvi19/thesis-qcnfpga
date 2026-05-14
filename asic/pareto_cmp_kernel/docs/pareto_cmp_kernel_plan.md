# Pareto Comparator / Selector Kernel VLSI Study Plan

## Goal

Study ASIC/VLSI implementation cost of the QFlow route-candidate comparator and selector logic.

## QFlow meaning

After QFlow computes candidate route metrics, the selector must decide which candidate is better.

A candidate route can be represented by metrics such as:

- score: lower is better
- fidelity: higher is better
- key_count: higher is better
- hop_count: lower is better
- qber: lower is better

The Pareto comparator checks whether one candidate dominates another or whether a weighted tie-break rule should be used.

## Baseline kernel

Pareto-C0 will compare two candidate routes:

Candidate A:
- score_a
- fidelity_a
- key_count_a
- hop_count_a
- qber_a

Candidate B:
- score_b
- fidelity_b
- key_count_b
- hop_count_b
- qber_b

The comparator outputs:

- select_a
- select_b
- tie
- a_dominates_b
- b_dominates_a

## Planned variants

| Variant | Description | Purpose |
|---|---|---|
| Pareto-C0 | Full metric comparator | Baseline |
| Pareto-C1 | Score-first comparator with tie-breaks | Lower-area practical selector |
| Pareto-C2 | Thresholded comparator | Approximate selector |
| Pareto-C3 | Multi-candidate tournament selector | Route-set selection kernel |

## Metrics

For each variant:

- Yosys generic cell count
- comparison logic breakdown
- register count
- output match against reference cases
- selector behavior under tie cases

## Evidence boundary

This is an ASIC/VLSI kernel study. It does not claim full ASIC signoff, fabricated silicon, or complete QFlow chip implementation.
