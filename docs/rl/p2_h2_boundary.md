# P2 H2 Boundary and Profile-Adapter Contract

## Frozen H2 anchor

- Canonical model: `reference_model.py`
- Canonical seed: `42`
- Ring-6 source/destination: `0 -> 3`
- Alpha vector: `(1.0, 1.5, 0.5, 2.0)`
- Tchebycheff vector: `(0.4, 0.4, 0.2)`
- Canonical-result SHA-256: `e4a393bc349f064ab7709e75fe6093210cf05f6f842fee33d4cc5b0adbcdaf3f`

The hash is computed from compact, sorted-key JSON without a trailing newline.
The default H2 call and action 0 (Balanced) must remain byte-identical.

## Permitted P2 control boundary

An RL action may select only:

- `alpha1..alpha4`, used by the SKAG composite edge weight; and
- `lambda_TCH1..lambda_TCH3`, used by the weighted Tchebycheff score.

It must not change physical fiber attenuation, effective link key-generation
rate, topology, traffic trace, seed, candidate paths, feasibility threshold,
fixed-point convention, or measurement boundary.

## Profile maturity

Balanced is frozen because it is the existing H2 anchor. The other three
profiles are sensitivity seeds only. Their final coefficients must be selected
from controlled P2 sensitivity evidence before the codebook is frozen.

The software Balanced vector `(0.4, 0.4, 0.2)` is represented by the
proportional hardware ratio `(2, 2, 1)`. The ratio is recorded for later RTL
mapping; software regression continues to use the exact original vector.
