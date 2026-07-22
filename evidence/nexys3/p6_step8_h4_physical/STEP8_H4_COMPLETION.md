# P6 Step 8 — Independent H4 Physical Campaign, Learned Profile, and Dwell Complete

## Independent implementation

- Controller: reinforcement-learned adaptive
- Policy mode: H4
- Top module: `p6_nexys3_h4`
- FPGA part: `xc6slx16-2-csg324`
- Timing target: 10 ns / 100 MHz
- Timing errors: 0
- Timing score: 0
- Post-PAR minimum period: 9.802 ns
- Post-PAR maximum frequency: 102.020 MHz
- Slice registers: 1156
- Slice LUTs: 1706
- Occupied slices: 677
- Bitstream bytes: 464294
- Bitstream SHA-256: `d0ddd6c2e8a0deab72a508a045d4727025954efafe9df962fde6c7e9534e9fe1`

## Physical Nexys3 result

- FPGA SRAM programming: pass
- UART: 115200 baud, 8N1, raw
- Physical records: 84/84
- Physical bytes: 3696/3696
- Strict H4 QF6R framing: 84/84
- Exact frozen-golden rows: 84/84
- Exact frozen-golden fields: 756/756
- Mismatches: 0
- Status distribution: 76 OK, 5 no-path, 3 invalid
- Display observed: 4084
- LD0 observed: ON
- LD1 observed: OFF
- Raw capture SHA-256: `70096b865631f2ce006d7b1b95f2c4e87155106ca84e531855318bb45821a500`
- Frozen golden SHA-256: `6df3c4052a52e662ffb07ad4ee0403e706feabcf2fdb59dd34d909b980fe6ae2`

## H4 learned profile selection and frozen dwell

The 81 valid/no-path decisions exactly match the frozen golden H4 sequence.

Only the 81 valid and no-path requests are counted as profile decisions; the
three intentionally invalid requests are excluded.

- Profile 0 decisions: 42
- Profile 1 decisions: 11
- Profile 2 decisions: 18
- Profile 3 decisions: 10
- Observed learned-profile transitions: 24
- Frozen dwell runs: 25
- Minimum dwell length: 1
- Maximum dwell length: 7
- Runtime Q update on FPGA: no
- Mean kernel cycles, all rows: 185.83333333333334
- Mean kernel cycles, normal rows: 204.76315789473685

UART serialization, host capture, JTAG programming, and display refresh remain
excluded from the deterministic kernel-cycle metric.

All raw board data, programming evidence, exact comparisons, profile sequence,
profile transitions, cycle summaries, board observations, validator-defect
documentation, and SHA-256 manifests are preserved and pushed to GitHub.
