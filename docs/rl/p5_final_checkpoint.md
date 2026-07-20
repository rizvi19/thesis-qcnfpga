# P5 final integration and evidence checkpoint

## Status

P5 QFlow-Mini is complete under the tracked nine-step execution sequence.

- Branch: `rl-nexys3-adaptive`
- Source checkpoint before final P5 commit: `aea8533e41674f8c6b38ce32e33285ffec39ea87`
- B1-B6 commit lineage: 6/6 verified
- Final integrated regression ladder: pass
- B4 exact candidate vectors: 519/519 pass
- B5 H0-H4 mode results: 101/101 pass
- B6 measured completions: 100/100 pass
- B6 measurement reproducibility: byte-exact pass
- B1-B6 bitstream hashes: 6/6 pass
- B1-B6 timing-report audit: 6/6 pass
- B1-B6 physical evidence records: 6/6 pass
- FPGA target: Digilent Nexys3, XC6SLX16-2-CSG324
- Declared clock: 100 MHz
- Latest integrated B6 timing: 9.252 ns minimum period, 108.085 MHz
- Latest integrated board signature: B610, LD0 blink, LD1 on, LD2 off,
  LD3 on, CENTER reset pass

## Measurement boundary

Kernel latency is counted from the accepted synchronous request edge to the
synchronous done edge. UART, host parsing, JTAG/programming and human time are
excluded.

## Evidence-channel boundary

LED and seven-segment physical evidence is complete. Physical raw-UART capture
is not claimed in P5 and is explicitly carried into P6, where the independent
H0-H4 board campaign requires raw transport logs and parsed board CSVs.

## P6 entry condition

P6 may now begin. It must compile H0-H4 independently with the same external
shell, numeric widths, replay, clock constraint and measurement boundary.
