# P6 Step 6 — H2 Independent ISE Implementation

- Source checkpoint: `a1bccdfc75eb3987b5d27f2c3635db079507be77`
- Policy mode: H2
- Top: `p6_nexys3_h2`
- FPGA part: `xc6slx16-2-csg324`
- Timing target: 10 ns / 100 MHz
- Timing errors: 0
- Timing score: 0
- Post-PAR minimum period: `9.724 ns`
- Post-PAR maximum frequency: `102.838 MHz`
- Bitstream bytes: `464294`
- Bitstream SHA-256: `8e7df4879dfd90fa9ed2df62755f099474f83681d082154b25e2b64fc4be8f8b`
- FPGA programming: none
- Physical UART capture: none
- EEPROM/configuration-flash writes: none

All XST, NGDBuild, Map, PAR, TRCE, BitGen, DRC, placement,
routing, timing, source-identity and bitstream artifacts are archived
under the H2 result/evidence directories and pushed to GitHub.

This checkpoint proves independent H2 implementation and timing closure only.
Physical H2 programming and UART capture remain the next gate.
