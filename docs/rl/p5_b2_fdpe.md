# P5 Step 4 / B2 FDPE-mini

## Frozen arithmetic

B2 implements the exact P5 contract path: `x` is UQ4.12, the 256-word
UNORM16 table contains `round_half_up(exp(-i/32)*65535)`, the low seven input
bits select a 1/128 interpolation fraction, interpolation rounds half upward,
and the final full `f_initial * decay` product is truncated by shifting right
16 bits. `x >= 8` returns zero. `tau_zero` returns zero with error asserted.

The RTL uses synchronous active-high dominant reset and a six-cycle latency
from accepted `start && ready` to the one-cycle `done` pulse. A start while
busy is ignored by this isolated arithmetic unit; the integrated policy shell
owns the later transaction-level stall response.

The two exponential-table reads are synchronous replicated distributed-ROM
ports. Registered stages separately capture the table outputs, form the
interpolation delta/base, multiply the delta by the fraction, round the decay,
and perform the final DSP multiply. This avoids the Spartan-6 RAMB8
initialization warning and does not change any encoded arithmetic result.

## Verification

The deterministic generator produces 519 exact vectors: all 256 LUT interval
boundaries, all 256 interval midpoints, the endpoint/zero-tau cases and
representative input-fidelity multiplication cases. The test reruns the
generator, requires byte-identical artifacts, and compares all 519 RTL outputs
exactly. No tolerance replaces encoded equality.

The board wrapper runs 16 representative cases internally. On success the
display shows `B210` (B2 plus hexadecimal 0x10 passed cases), LD1 is ON, LD2 is
OFF and LD3 is ON. LD0 is a heartbeat. CENTER synchronously restarts the test.

Only volatile FPGA SRAM programming is authorized. EEPROM and configuration
flash access are prohibited. Physical claims require the user-observed board
result after successful implementation and programming.
