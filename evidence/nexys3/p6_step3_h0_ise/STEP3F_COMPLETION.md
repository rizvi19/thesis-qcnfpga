# P6 Step 3F — H0 Independent ISE Implementation, Attempt 2

- Source branch: `rl-nexys3-adaptive`
- Source checkpoint: `2fd32b4c0bb29f5158fc68352ccd1761d704551c`
- Policy mode: H0
- Top module: `p6_nexys3_h0`
- FPGA part: `xc6slx16-2-csg324`
- Formatter: iterative shift-add-3 BCD converter
- Flow: XST → NGDBuild → Map → PAR → TRCE → BitGen
- Timing target: 10 ns / 100 MHz
- Timing errors: 0
- Timing score: 0
- Post-PAR minimum period: `8.407 ns`
- Post-PAR maximum frequency: `118.948 MHz`
- Bitstream bytes: `464294`
- Bitstream SHA-256: `63f265b73df4ad4f09f50bdb1d4dcdf35f4edb0f267bb8f3ea9744b4f592ced8`
- FPGA programming: none
- Live UART access: none
- USB/Adept access: none
- EEPROM access: none

This checkpoint proves independent H0 implementation and post-PAR timing
closure. It does not yet claim physical Nexys3 execution or UART capture.
