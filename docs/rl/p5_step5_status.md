# P5 Step 5 Status — B3 SKAG-mini

Status: **COMPLETE**

- Frozen SKAG equation: `alpha1/K + alpha2/F + alpha3/key_rate + alpha4*qber`.
- Four deployed 18-bit profiles decoded exactly.
- Host vectors: 1,056 of 1,056 exact pass.
- Board-wrapper cases: 16 of 16 exact pass.
- Infeasible zero-key, zero-fidelity, and zero-rate cases return `FFFFFFFF`.
- Finite overflow saturates at `FFFFFFFE`.
- Post-route timing: zero errors, 6.517 ns minimum period, 153.445 MHz.
- Volatile bitstream: 464,294 bytes, SHA-256
  `0e1b78eaf17dc6a56b2d6c6794b4b807841286f60b3ce9d43f87f53d3e2cb1f4`.
- Physical validation: display `B310`, LD0 blinking, LD1 on, LD2 off,
  LD3 on, CENTER restarts and returns to `B310`.
- Controller EEPROM and FPGA configuration flash accesses: zero.

The first `Nexys3` programming call failed transiently. Adept then enumerated
the same operational USB/JTAG controller as `DOnbUsb`, serial
`000000000000`. Read-only JTAG initialization still returned XC6SLX16 ID
`44002093`; addressing that enumerated Adept name directly programmed the exact
bitstream successfully. This fallback is preserved separately for reuse.

P5 progress after this checkpoint: **5 of 9 completed**.
Next milestone: **P5 Step 6 / B4 candidate evaluator**.
