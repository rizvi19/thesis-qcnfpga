# P6 Step 7 H3 Transport-Recovery Incident

## Scope

This record preserves the stopped recovery incident encountered before physical
H3 programming. It does not claim that H3 was programmed or executed during
this incident.

## Observations

- Repository checkpoint before the incident: `27f31581b1c81ffebb6dc444cc038a767db75fdc`.
- UART FTDI identity `0403:6001` remained visible.
- The onboard JTAG controller appeared as raw Cypress `04b4:8613` instead of
  operational Digilent `1443:0007` after the laptop and board had been powered
  down.
- One deep cold restart was performed and raw mode persisted.
- The verified VendAX helper was loaded into volatile FX2 RAM only:
  3,359 bytes in 41 segments.
- A3 RAM self-test passed exactly, 16/16 bytes.
- Two AA speed-selection commands returned zero.
- The first 16-byte A9 read returned all `0xCD` transfer failure-fill.
- One delayed read-only A9 reprobe also returned all `0xCD` transfer
  failure-fill.
- No EEPROM write occurred.
- No FPGA programming occurred.
- No H3 physical UART data was generated or lost.

## Engineering classification

The all-`0xCD` result is recorded as transfer failure-fill, not erased EEPROM.
Prior exact stored-image readback evidence remains authoritative. Because the
single permitted delayed reprobe also returned failure-fill, the EEPROM
investigation is stopped. The incident is classified as intermittent FX2
boot/read-transport or power-sequencing reliability.

The next safe recovery action is to seek a later operational `1443:0007`
startup window through a controlled power restart only. No additional VendAX
load, EEPROM read, or EEPROM write is authorized by this checkpoint.

## Evidence handling

Raw local logs remain under `~/Downloads` and are not copied into the public
repository. `local_evidence_manifest.csv` preserves their file names, sizes,
and SHA-256 identities. The recovery wrapper did not create its optional local
`SHA256SUMS` file because the A9 probe returned failure-fill and the wrapper
exited before its success-only manifest stage; the repository manifest is
therefore reconstructed directly from the five existing source evidence files. This avoids committing unnecessary host-specific logs
or firmware material while maintaining an auditable chain of evidence.
