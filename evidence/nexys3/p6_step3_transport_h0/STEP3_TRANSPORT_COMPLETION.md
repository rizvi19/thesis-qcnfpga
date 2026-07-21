# P6 Step 3 — Physical Result-Transport Gate Complete

- Physical board: Digilent Nexys3, XC6SLX16
- JTAG device ID: `44002093`
- Board serial: `210182697240`
- UART device: FTDI FT232R, serial `A6003R67`
- UART configuration: 115200 baud, 8N1, raw
- Program target: volatile FPGA SRAM
- Physical mode used for transport qualification: H0
- Captured records: 84/84
- Captured bytes: 3696/3696
- Framing: 84/84 strict QF6R records
- Unique test IDs: 84/84
- Frozen-golden row matches: 84/84
- Frozen-golden field matches: 756/756
- Mismatches: 0
- Raw physical capture SHA-256: `c99628496d668e3a81f204a40f8b6f8fedb6416e688066e841a1463d1c6ab124`
- Frozen golden CSV SHA-256: `6df3c4052a52e662ffb07ad4ee0403e706feabcf2fdb59dd34d909b980fe6ae2`
- EEPROM/configuration-flash writes: none

This closes the P6 physical result-transport gate. UART transmission and host
capture remain excluded from the reported deterministic kernel-cycle metric.
