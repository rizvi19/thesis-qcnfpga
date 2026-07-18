# P5 Board Interface Contract

## Boundary

This file freezes externally observable P5 behavior without creating pin
assignments or a UCF. Pin selection, electrical constraints, ISE execution and
live board access are later reviewed steps.

Target identity is Digilent Nexys3, XC6SLX16-2-CSG324. FPGA programming, when
later authorized, is volatile SRAM programming only. EEPROM read, write,
erase, diagnosis or repair is prohibited in normal P5.

## Logical controls and status

The board wrapper shall provide logical `clk`, synchronous active-high `rst`,
`start`, `input_valid`, `ready`, `busy`, `done`, `route_valid`, `stall`, and
the result fields frozen in the QFlow-Mini contract. Mechanical inputs must be
synchronized; a later B1 design may debounce them. No pin is frozen here.

LEDs and the four-digit seven-segment display are compact sanity/demo outputs.
UART is the primary exact-value evidence channel.

## B1 sanity boundary

B1 is independent of QFlow datapath implementation. It must demonstrate:

1. the declared board clock drives a deterministic counter;
2. synchronous reset visibly returns the counter to `0000`;
3. the four-digit display scans correctly and shows the low 16 counter bits in
   hexadecimal at a human-observable update rate;
4. at least one LED provides heartbeat/status and one reflects reset state;
5. UART emits deterministic B1 records containing the same displayed counter;
6. captured display/UART values agree for reviewed samples.

The historical SW0-to-LD0 smoke test is prerequisite evidence but does not
satisfy B1. Step 2 performs none of these physical actions.

## UART electrical/configuration contract

The logical format is 8 data bits, no parity, one stop bit, idle high. Baud rate
and physical pins are intentionally deferred to the B1/UCF review because the
authoritative PDFs do not freeze them. A B1 package must choose both explicitly,
derive the divider from the declared clock, and validate baud error before RTL
or UCF acceptance.

Records are printable ASCII, comma separated, terminated by CRLF, and contain
no spaces. Numeric identifiers/cycles are unsigned decimal. Exact fixed-point
values are uppercase hexadecimal without `0x`.

### B1 record

```text
QF5B1,1,<counter_hex4>,<status_dec>\r\n
```

### QFlow result record

```text
QF5R,1,<test_id>,<policy_id>,<state_id>,<profile_id>,<selected_path>,<score_hex5>,<bottleneck_hex4>,<cycles>,<status>\r\n
```

`selected_path=255`, `score_hex5=FFFFF`, and `bottleneck_hex4=0000` are used
when no route result exists. A successful finite score is 18 useful bits and
must be encoded in five hexadecimal digits. Every completed request produces
exactly one `QF5R` line. A busy stall may produce an additional event line only
in a later versioned schema; version 1 exposes the stall signal in simulation
and counters but does not create an ambiguous request-completion record.

Status codes are frozen:

| Code | Name | Meaning |
|---:|---|---|
| 0 | OK | route valid and result fields meaningful |
| 1 | NO_PATH | valid request, no feasible candidate |
| 2 | INVALID_REQUEST | request rejected at idle because input is invalid |
| 3 | CONTRACT_ERROR | encoded input or invariant violation detected |
| 4 | INTERNAL_ERROR | impossible/unclassified hardware error |

Host parsing must reject an unknown prefix, schema version, field count,
numeric width or status code. UART capture time is never kernel latency.

## Evidence separation

Simulation records are labeled simulation. ISE reports are labeled synthesis
or implementation as applicable. Only captured output from the identified
physical board is board evidence. B1 does not establish FDPE, SKAG, route
selection or H4 correctness.
