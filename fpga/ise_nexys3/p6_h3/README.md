# P6 H3 Independent ISE Project

- Source checkpoint: `c2edac943fe8390dcc24b620428fa08e461005e0`
- Top: `p6_nexys3_h3`
- Part: `xc6slx16-2-csg324`
- Policy mode: H3
- Clock target: 10 ns / 100 MHz
- UART: 115200, 8N1, TX pin N18
- Replay: frozen common 84-row P6 replay
- Formatter: iterative shift-add-3 BCD conversion
- Flow: XST → NGDBuild → Map → PAR → TRCE → BitGen

This checkpoint performs independent H3 implementation only. It does not
program the FPGA or claim physical H3 execution.
