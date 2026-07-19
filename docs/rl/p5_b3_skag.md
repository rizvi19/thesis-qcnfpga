# P5 B3 SKAG-mini

This milestone implements the frozen P5 edge-weight equation:

`alpha1/K + alpha2/F + alpha3/key_rate + alpha4*qber`.

The edge entry is 64 bits in the frozen order `K`, `F`, `key_rate`, `qber`.
The four alpha coefficients are decoded from bits 17:6 of the 18-bit profile
payload as U2.1 numerators. Each rational term is converted exactly once to
UQ16.16 using round-to-nearest, half-up. The four encoded terms are then added
with saturation. A zero key count, fidelity, or key rate produces the reserved
infinity code `FFFFFFFF`; finite overflow saturates at `FFFFFFFE`.

The RTL uses one 48-by-18-bit restoring divider shared across the four terms.
This is intentionally serialized: B3 prioritizes exact arithmetic and the
100 MHz Nexys3 clock target over single-cycle throughput. The self-test checks
16 representative cases from all four frozen profiles. A physical pass is
display `B310`, LD0 blinking, LD1 on, LD2 off, and LD3 on.

The host gate regenerates and checks 1,056 exact vectors covering all profiles,
the 12 frozen Ring-6 directed edges, zero-denominator infeasibility, finite
boundary arithmetic, rounding, and finite saturation. ISE implementation and
volatile programming are permitted only after this exact gate passes.
