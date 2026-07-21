# P6 H1 Independent ISE Project

- Source checkpoint: `06a5512e42e7e2e55ca768c527a5dcbb1b04e157`
- Top: `p6_nexys3_h1`
- Part: `xc6slx16-2-csg324`
- Policy mode: H1
- Clock target: 10 ns / 100 MHz
- UART: 115200, 8N1, TX pin N18
- Replay: frozen common 84-row P6 replay
- Formatter: iterative shift-add-3 BCD conversion
- Flow: XST → NGDBuild → Map → PAR → TRCE → BitGen

This checkpoint performs independent H1 implementation only. It does not
program the FPGA or claim physical H1 execution.
