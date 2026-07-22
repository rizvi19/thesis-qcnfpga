# P6 Step 9 — H0–H4 Same-Board Comparison Complete

## Evidence layer

This is a Class A direct hardware comparison. H0–H4 were independently
implemented and physically executed on the same Digilent Nexys3
XC6SLX16-2-CSG324 using the same 100 MHz constraint, replay order,
fixed-point fields, UART record format and common shell.

## Correctness

- Five independent bitstreams: pass
- Physical records: 420/420
- Exact frozen-golden rows: 420/420
- Exact frozen-golden fields: 3780/3780
- Physical-to-golden mismatches: 0
- Per-mode status distribution: 76 OK, 5 no-path, 3 invalid
- UART overhead excluded from kernel-cycle measurements

## Main H4 hardware result

- Controller: reinforcement-learned adaptive
- Achieved Fmax: 102.020 MHz
- Mean normal kernel cycles: 204.763158
- Mean normal kernel latency: 2.047632 us
- Slice registers: 1156
- Slice LUTs: 1706
- Occupied slices: 677
- BRAM: 0
- DSP: 0
- Physical display: 4084
- LD0: ON
- LD1: OFF

## Adaptation evidence

- H3 profile distribution: 24, 36, 18, 3
- H3 profile transitions: 44
- H4 profile distribution: 42, 11, 18, 10
- H4 learned-profile transitions: 24
- H4 frozen dwell runs: 25
- H4 minimum/maximum dwell: 1 / 7
- Runtime Q update on FPGA: no

## Direct H4 context

- H2 achieved Fmax: 102.838 MHz
- H3 achieved Fmax: 102.648 MHz
- H4 achieved Fmax: 102.020 MHz
- All three meet the required 100 MHz constraint.
- H4 adds learned state-to-profile selection while preserving exact
  fixed-point agreement on all 84 physical vectors.

## Statistics and claim boundary

Paired held-out fidelity statistics are reported for H4 versus H2 and H3.
Blocking/success, path changes, bootstrap 95% confidence intervals, exact
two-sided sign tests and paired effect sizes are preserved in
`heldout_pairwise_h4_statistics.csv`.

Raw scalar score is not compared across modes because the scalarization
profile itself changes. This prevents an invalid comparison between scores
computed using different weights.

## Explicit limitations

Power and energy are explicitly omitted because no common
activity-calibrated H0–H4 report is available. No measured or estimated
power-superiority claim is made. Photo/video status is recorded as
`OMITTED_NOT_ARCHIVED_IN_REPOSITORY`. The physical evidence matrix still preserves each
bitstream identity, programming-success log, raw UART identity and observed
display/LED result.
