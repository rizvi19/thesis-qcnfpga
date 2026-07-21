# P6 H2 Independent ISE Project

- Source checkpoint: `a1bccdfc75eb3987b5d27f2c3635db079507be77`
- Top: `p6_nexys3_h2`
- Part: `xc6slx16-2-csg324`
- Policy mode: H2
- Clock target: 10 ns / 100 MHz
- UART: 115200, 8N1, TX pin N18
- Replay: frozen common 84-row P6 replay
- Formatter: iterative shift-add-3 BCD conversion
- Flow: XST → NGDBuild → Map → PAR → TRCE → BitGen

This checkpoint performs independent H2 implementation only. It does not
program the FPGA or claim physical H2 execution.
