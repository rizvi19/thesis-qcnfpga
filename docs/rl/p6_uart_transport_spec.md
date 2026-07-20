# P6 UART Result Transport Specification

P6 uses `QF6R` schema version 1:

```text
QF6R,1,TTTT,P,SSS,R,PPP,CCCCCC,FFFFF,LLL,E\r\n
```

All fields are unsigned decimal with intentional leading zeroes.

| Field | Width | Range |
|---|---:|---:|
| test ID | 4 | 0–9999 |
| policy ID | 1 | 0–4 |
| state ID | 3 | 0–255 |
| profile ID | 1 | 0–3 |
| selected path | 3 | 0–3 or 255 |
| score | 6 | 0–262143 |
| bottleneck fidelity | 5 | 0–65535 |
| kernel cycles | 3 | 0–999 |
| status | 1 | 0–2 |

Every record is exactly 44 bytes including CRLF. For status 1 or 2,
selected path is 255, score is zero and bottleneck fidelity is zero.

Production UART is 100 MHz, 115200 baud, 8N1, idle high, no flow control.
The rounded divider is 868 clocks per bit. UART serialization and host
parsing are excluded from kernel cycles.

Step 3D accelerates only the bit-level simulation to 1 MHz/100000 baud,
preserving 10 clocks per bit. All 18480 serialized bytes are decoded and
compared. The resulting raw log is simulated transport evidence, not
physical UART evidence. A later physical wrapper must feed the same QF6R
field order and parser.
