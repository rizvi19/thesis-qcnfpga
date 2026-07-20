# P5 Step 8 — B6 Kernel-Cycle Measurement Completion

## Final status

- Measurement boundary: accepted synchronous edge to done synchronous edge
- UART, host parsing, JTAG/programming and human time excluded
- Measured H0-H4 completions: 100/100 pass
- Measurement simulation reproducibility: byte-exact pass
- Embedded B6 board self-test: 5/5 pass
- Timing errors: 0
- Minimum period: 9.252 ns
- Maximum frequency: 108.085 MHz
- 100 MHz timing gate: pass
- Bitstream size: 464294 bytes
- Bitstream SHA-256: cb856364427f2883fef522e851dc8a6edacd7b9b5458f82bcd9f801317a06457
- Measurement RTL SHA-256: e83c1916cc335755eed19d4e2fbd491a0708cd191b585add164cd710f410abeb
- Repaired testbench SHA-256: 4654cb7e440f2165f5477e5731fc4839594d797e5a72bbbf2f86de38f5a20458
- Self-test RTL SHA-256: 51d41302ea137e4903c52c0120124022275120940e49b55f1b96af5e3e751cb9
- FPGA volatile programming: pass
- Display: B610
- LD0: blinking
- LD1: on
- LD2: off
- LD3: on
- CENTER reset: returns to B610

## Host cycle summary

| Mode | Samples | Minimum | Maximum | Mean |
|---|---:|---:|---:|---:|
| H0 | 20 | 1 | 2 | 1.950000 |
| H1 | 20 | 1 | 109 | 11.750000 |
| H2 | 20 | 1 | 110 | 12.700000 |
| H3 | 20 | 1 | 110 | 12.700000 |
| H4 | 20 | 1 | 112 | 14.600000 |

The 100 MHz conversion is 10 ns per measured kernel cycle. Full independent
H0-H4 comparison builds and experimental statistics remain part of P6.
