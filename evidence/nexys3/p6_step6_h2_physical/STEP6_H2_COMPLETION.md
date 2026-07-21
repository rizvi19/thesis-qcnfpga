# P6 Step 6 — Independent H2 Physical Campaign Complete

## Independent implementation

- Policy mode: H2
- Top module: `p6_nexys3_h2`
- FPGA part: `xc6slx16-2-csg324`
- Timing target: 10 ns / 100 MHz
- Timing errors: 0
- Timing score: 0
- Post-PAR minimum period: 9.724 ns
- Post-PAR maximum frequency: 102.838 MHz
- Slice registers: 1085
- Slice LUTs: 1650
- Occupied slices: 649
- Bitstream bytes: 464294
- Bitstream SHA-256: `8e7df4879dfd90fa9ed2df62755f099474f83681d082154b25e2b64fc4be8f8b`

## Physical Nexys3 result

- FPGA SRAM programming: pass
- UART: 115200 baud, 8N1, raw
- Physical records: 84/84
- Physical bytes: 3696/3696
- Strict QF6R framing: 84/84
- Exact frozen-golden rows: 84/84
- Exact frozen-golden fields: 756/756
- Mismatches: 0
- Status distribution: 76 OK, 5 no-path, 3 invalid
- Minimum observed kernel cycles: 1
- Maximum observed kernel cycles: 310
- Display observed: 2084
- LD0 observed: ON
- LD1 observed: OFF
- Raw capture SHA-256: `49a9d37a0355974c9f82bb90194403744159a6369ba56f6778a246c7f37563b3`
- Frozen golden SHA-256: `6df3c4052a52e662ffb07ad4ee0403e706feabcf2fdb59dd34d909b980fe6ae2`

UART serialization, host capture, JTAG programming, and display refresh remain
excluded from the deterministic kernel-cycle metric.

All raw board data, parsed results, exact comparisons, timing data, programming
evidence, board observations, cycle summaries, and SHA-256 manifests are
preserved in the repository and pushed to GitHub.
