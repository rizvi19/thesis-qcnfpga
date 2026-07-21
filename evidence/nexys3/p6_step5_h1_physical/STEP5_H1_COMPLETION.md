# P6 Step 5 — Independent H1 Physical Campaign Complete

## Independent implementation

- Policy mode: H1
- Top module: `p6_nexys3_h1`
- FPGA part: `xc6slx16-2-csg324`
- Timing target: 10 ns / 100 MHz
- Timing errors: 0
- Timing score: 0
- Post-PAR minimum period: 9.299 ns
- Post-PAR maximum frequency: 107.538 MHz
- Slice registers: 1000
- Slice LUTs: 1484
- Occupied slices: 589
- Bitstream bytes: 464294
- Bitstream SHA-256: `98156a9674992f7414b93b15aba5a60eff8ed5957a50ee07a7c73fccf61caa23`

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
- Display observed: 1084
- LD0 observed: ON
- LD1 observed: OFF
- Raw capture SHA-256: `ab6010229b166e55d7056253a6ebd848b10b3c1e7d2ded0903fcbb0523780787`
- Frozen golden SHA-256: `6df3c4052a52e662ffb07ad4ee0403e706feabcf2fdb59dd34d909b980fe6ae2`

UART serialization, host capture, JTAG programming and display refresh remain
excluded from the deterministic kernel-cycle metric.
