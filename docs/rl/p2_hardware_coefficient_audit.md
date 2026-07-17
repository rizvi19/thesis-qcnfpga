# P2 Hardware-Efficient Coefficient Audit

## Purpose

The P2 exit gate requires every selected profile multiplier to be implementable
with shift/add operations or a small shared multiplier budget. This audit checks
the four selected profiles without claiming RTL implementation or synthesis.

## Alpha representation

All selected `alpha1..alpha4` values are exact multiples of one half. Each value
is stored as a 3-bit unsigned numerator with one implicit fractional bit:

`alpha = alpha_numerator / 2`.

The largest numerator is six, so every value fits without coefficient-field
overflow. Numerators use at most two nonzero binary terms. Multiplication by an
alpha therefore needs at most two shifts/addends followed by the common
one-bit fractional adjustment; no generic profile-coefficient multiplier is
required.

## Tchebycheff representation

The normalized software weights are stored for experiment readability. The
hardware representation uses the primitive integer ratios already frozen in
the profile codebook: `(2,2,1)`, `(1,1,2)`, `(1,2,1)` and `(2,1,1)`.

Each ratio element fits in two unsigned bits and is either one or two, requiring
at most a wire or one shift. Removing the common per-profile denominator scales
every candidate score by the same positive constant and therefore cannot change
the selected route. This also represents the Balanced weights `(0.4,0.4,0.2)`
exactly without attempting to encode non-dyadic `0.4` directly.

## ROM payload and evidence boundary

The coefficient payload is 18 bits per addressed profile: four 3-bit alpha
numerators plus three 2-bit Tchebycheff ratio fields. Four profiles require 72
payload bits. The two-bit action ID is the ROM address and is not duplicated in
the payload.

Route equivalence is checked on all 20 profile/scenario combinations from the
controlled sensitivity fixtures and on four canonical H2 Pareto fronts. This
is an arithmetic implementability result. Downstream datapath widths, RTL,
timing, utilization and board behavior remain later-phase evidence.
