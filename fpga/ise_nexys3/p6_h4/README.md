# P6 H4 Independent ISE Project

- Source checkpoint: `9b88e7f6628b8e9dd719c9081465d95a4bb14f77`
- Top: `p6_nexys3_h4`
- Part: `xc6slx16-2-csg324`
- Policy mode: H4
- Clock target: 10 ns / 100 MHz
- UART: 115200, 8N1, TX pin N18
- Replay: frozen common 84-row P6 replay
- Formatter: iterative shift-add-3 BCD conversion
- Flow: XST → NGDBuild → Map → PAR → TRCE → BitGen

This checkpoint performs independent H4 implementation only. It does not
program the FPGA or claim physical H4 execution.
