# P6 H0 Independent ISE Project — Attempt 2

- Source checkpoint: `2fd32b4c0bb29f5158fc68352ccd1761d704551c`
- Top: `p6_nexys3_h0`
- Part: `xc6slx16-2-csg324`
- Policy mode: H0
- Clock constraint: 10 ns / 100 MHz
- UART: 115200, 8N1, FPGA TX on N18
- Replay: common frozen 84-row P6 replay
- Result validation: internal comparison against committed expected-result ROM
- Formatter: iterative shift-add-3 BCD conversion
- Build flow: XST → NGDBuild → Map → PAR → TRCE → BitGen

UART serialization, host parsing, JTAG and programming time remain outside the
kernel-cycle metric. This checkpoint performs implementation only.
