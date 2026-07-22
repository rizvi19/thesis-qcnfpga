# P6 Step 8 — H4 Independent ISE Implementation

- Source checkpoint: `9b88e7f6628b8e9dd719c9081465d95a4bb14f77`
- Policy mode: H4
- Top: `p6_nexys3_h4`
- FPGA part: `xc6slx16-2-csg324`
- Timing target: 10 ns / 100 MHz
- Timing errors: 0
- Timing score: 0
- Post-PAR minimum period: `9.802 ns`
- Post-PAR maximum frequency: `102.02 MHz`
- Bitstream bytes: `464294`
- Bitstream SHA-256: `d0ddd6c2e8a0deab72a508a045d4727025954efafe9df962fde6c7e9534e9fe1`
- FPGA programming: none
- Physical UART capture: none
- EEPROM/configuration-flash writes: none

All XST, NGDBuild, Map, PAR, TRCE, BitGen, DRC, placement,
routing, timing, source-identity and bitstream artifacts are archived
under the H4 result/evidence directories and pushed to GitHub.

This checkpoint proves independent H4 implementation and timing closure only.
Physical H4 programming, UART capture, exact golden comparison, learned-profile
selection, and frozen dwell evidence remain the next gates.
