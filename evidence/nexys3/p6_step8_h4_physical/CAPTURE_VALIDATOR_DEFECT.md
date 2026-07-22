# P6 H4 Step-8B Host Validator Defect

The physical Nexys3 H4 run completed successfully:

- FPGA SRAM programming reported success.
- The board displayed `4084`.
- LD0 was ON.
- LD1 was OFF.
- UART contained exactly 84 CRLF records, 3696 bytes total.
- Every record was 44 bytes with 11 comma-separated fields.
- Every physical record identified policy mode H4 (`policy_id = 4`).

The Step-8B host validator rejected all 84 records because its regular
expression accidentally retained the literal H2 policy digit (`2`) while its
messages and remaining checks referred to H4. This was a host-side validation
template defect, not an RTL, FPGA, UART, formatting, or physical-result defect.

The preserved physical capture was subsequently validated with the correct H4
policy digit, then compared exactly against the frozen golden H4 results.
