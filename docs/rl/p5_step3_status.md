# P5 Step 3 - Nexys3 B1 I/O sanity completion

Status: **COMPLETE**  
P5 progress after this gate: **3 of 9 completed**

The B1 RTL/simulation, deterministic ISE implementation, operational USB/JTAG
enumeration, volatile FPGA programming, direct-input diagnosis, repaired B1
implementation, and final physical reset validation all passed.

The root cause of the failed reset test was an internal FPGA `PULLDOWN` applied
to the externally driven Nexys3 Rev. B center button. A direct no-pulldown
diagnostic proved SW0 and all five buttons. The final UCF removes only that
active pull constraint.

Final repaired B1 bitstream:

- Bytes: 464,294
- SHA-256: `7eefc2e1cae4089cc47e58c2cca11a8b91efa359630d2e3b70fefe1074bc5347`
- Minimum period: 6.253 ns
- Maximum frequency: 159.923 MHz
- Timing score/errors: 0 / 0

Physical validation passed:

- Hexadecimal display counts upward.
- LD0 alternates with odd/even count.
- CENTER holds the display at `0000`.
- LD1 is ON while reset is held and OFF after release.
- Counting restarts from `0001` after release.

Controller recovery evidence showed exact stored firmware and intermittent
VendAX read transport. No EEPROM write was performed during P5. Routine startup
must follow the fast runbook and must not repeat full EEPROM reads.
