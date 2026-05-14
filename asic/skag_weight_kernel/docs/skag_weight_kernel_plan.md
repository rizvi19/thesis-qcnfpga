# SKAG Weight Kernel VLSI Study Plan

## Goal

Study ASIC/VLSI implementation cost of the QFlow SKAG edge-weight computation.

## QFlow meaning

SKAG stores live QKD edge state and computes a composite edge score used by the route selector or GA fitness logic.

Each edge contains:

- key_count
- avg_fidelity
- arrival_rate
- qber

The canonical score uses weighted terms for key availability, fidelity, arrival rate, and QBER.

## Baseline kernel

SKAG-W0 will implement a simple fixed-point weighted score:

score =
  alpha_k * key_shortage_term
+ alpha_f * fidelity_penalty_term
+ alpha_l * arrival_penalty_term
+ alpha_q * qber_term

The first version will avoid true division and use shift/bucket approximations so that the kernel is realistic for ASIC/VLSI synthesis.

## Planned variants

| Variant | Description | Purpose |
|---|---|---|
| SKAG-W0 | bucketized fixed-point score | simple baseline |
| SKAG-W1 | exact-ish reciprocal LUT score | accuracy-focused |
| SKAG-W2 | rank-only score | lower-area comparison |
| SKAG-W3 | saturation/threshold score | routing-oriented approximation |

## Metrics

For each variant:

- Yosys generic cell count
- register count
- combinational logic breakdown
- output score match/rank match against Python
- edge-order preservation
- synthesis caveats

## Evidence boundary

This is an ASIC/VLSI kernel study. It does not claim full ASIC signoff, fabricated silicon, or complete QFlow chip implementation.
