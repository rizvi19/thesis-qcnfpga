# P5 Step 6 — B4 Candidate Evaluator Completion

## Final status

- Host regression: 519/519 exact pass
- Embedded self-test: 16/16 pass
- Timing errors: 0
- Minimum period: 8.391 ns
- Maximum frequency: 119.175 MHz
- 100 MHz timing gate: pass
- Bitstream size: 464294 bytes
- Bitstream SHA-256: e0259334129fd8b1b7aff52a8fd923e8c06792c91f7b20a3ba3017a38966a977
- Evaluator RTL SHA-256: e9fea3a07cfe37b219aa6c9ea95c8e96591f2cf45c3ff260240f972e7c52c985
- Self-test RTL SHA-256: d067684132b89b654d93ac45515a4d1a3fdfa6e20aeda54e8f42d032c839f566
- FPGA volatile programming: pass
- Display: B410
- LD0: blinking
- LD1: on
- LD2: off
- LD3: on
- CENTER reset: returns to B410

## Repairs

1. Pipelined difference scaling and round-half-up numerator preparation.
2. Preserved the frozen normalization mathematics.
3. Corrected embedded vector 11's expected physical slot from 0 to 1.
4. Preserved failed timing and physical-self-test evidence.
