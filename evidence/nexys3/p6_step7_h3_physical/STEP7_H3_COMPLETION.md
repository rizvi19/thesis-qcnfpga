# P6 Step 7 — Independent H3 Physical Campaign and Profile Switching Complete

## Independent implementation

- Policy mode: H3
- Top module: `p6_nexys3_h3`
- FPGA part: `xc6slx16-2-csg324`
- Timing target: 10 ns / 100 MHz
- Timing errors: 0
- Timing score: 0
- Post-PAR minimum period: 9.742 ns
- Post-PAR maximum frequency: 102.648 MHz
- Slice registers: 1097
- Slice LUTs: 1836
- Occupied slices: 645
- Bitstream bytes: 464294
- Bitstream SHA-256: `b0fdbb435b73f95b392d5ca9c20df25a0c544a0154f557425d4f9a7c7f1e7b95`

## Physical Nexys3 result

- FPGA SRAM programming: pass
- UART: 115200 baud, 8N1, raw
- Physical records: 84/84
- Physical bytes: 3696/3696
- Strict H3 QF6R framing: 84/84
- Exact frozen-golden rows: 84/84
- Exact frozen-golden fields: 756/756
- Mismatches: 0
- Status distribution: 76 OK, 5 no-path, 3 invalid
- Display observed: 3084
- LD0 observed: ON
- LD1 observed: OFF
- Raw capture SHA-256: `3c5b2bc97ffa8dd24a6cfd1556b643166e121f004b81d4332786284c3874af17`
- Frozen golden SHA-256: `6df3c4052a52e662ffb07ad4ee0403e706feabcf2fdb59dd34d909b980fe6ae2`

## H3 profile switching

Only the 81 valid and no-path requests are counted as profile decisions; the
three intentionally invalid requests are excluded.

- Profile 0 decisions: 24
- Profile 1 decisions: 36
- Profile 2 decisions: 18
- Profile 3 decisions: 3
- Observed profile transitions: 44
- Mean kernel cycles, all rows: 183.9047619047619
- Mean kernel cycles, normal rows: 202.76315789473685

UART serialization, host capture, JTAG programming, and display refresh remain
excluded from the deterministic kernel-cycle metric.

All raw board data, programming evidence, exact comparisons, profile sequence,
profile transitions, cycle summaries, board observations, validator-defect
documentation, and SHA-256 manifests are preserved and pushed to GitHub.
