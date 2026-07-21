# P6 Step 7 — H3 Independent ISE Implementation

- Source checkpoint: `c2edac943fe8390dcc24b620428fa08e461005e0`
- Policy mode: H3
- Top: `p6_nexys3_h3`
- FPGA part: `xc6slx16-2-csg324`
- Timing target: 10 ns / 100 MHz
- Timing errors: 0
- Timing score: 0
- Post-PAR minimum period: `9.742 ns`
- Post-PAR maximum frequency: `102.648 MHz`
- Bitstream bytes: `464294`
- Bitstream SHA-256: `b0fdbb435b73f95b392d5ca9c20df25a0c544a0154f557425d4f9a7c7f1e7b95`
- FPGA programming: none
- Physical UART capture: none
- EEPROM/configuration-flash writes: none

All XST, NGDBuild, Map, PAR, TRCE, BitGen, DRC, placement,
routing, timing, source-identity and bitstream artifacts are archived
under the H3 result/evidence directories and pushed to GitHub.

This checkpoint proves independent H3 implementation and timing closure only.
Physical H3 programming, UART capture, exact golden comparison, and profile-
switching evidence remain the next gates.
