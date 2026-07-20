# P5 Step 7 — B5 H0-H4 Policy Shell Completion

## Final status

- H0-H4 host-mode results: 101/101 pass
- Accepted P4 controller regression: 12/12 pass
- Accepted B4 evaluator regression: 519/519 exact pass
- Embedded B5 board self-test: 17/17 pass
- Timing errors: 0
- Minimum period: 9.670 ns
- Maximum frequency: 103.413 MHz
- 100 MHz timing gate: pass
- Bitstream size: 464294 bytes
- Bitstream SHA-256: 28b5aee122d8a8a951497a436dac1c1b406d6b668ba15aef31ecf2d22be5ae1c
- Policy-shell RTL SHA-256: 6138ce00d262129f9d3436bc6b0ba1b4a43d1601c31ee6ca146a5f20f60cae71
- Self-test RTL SHA-256: c86ccba4c716a6f4ea40f5b35d423d057c7c90180bd473f9cd340658ed44218f
- FPGA volatile programming: pass
- Display: B510
- LD0: blinking
- LD1: on
- LD2: off
- LD3: on
- CENTER reset: returns to B510

## Mode boundary

- H0: feasible shortest-hop route
- H1: fixed key-aware cost-only selection
- H2: accepted fixed profile 0
- H3: frozen first-match threshold/rule controller
- H4: accepted P4 learned policy ROM with minimum dwell

The B5 cycle outputs remain explicit invalid placeholders. P5 Step 8/B6 adds
the accepted-edge-to-done kernel cycle counter and measurement protocol.
