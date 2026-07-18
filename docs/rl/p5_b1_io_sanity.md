# P5 B1 I/O Sanity — Stage A

## Scope and evidence boundary

This stage implements and simulates the B1 clock/reset, four-digit hexadecimal
display and transmit-only UART sanity design. It creates a reviewed UCF but
does not activate ISE, synthesize, implement, generate a bitstream, enumerate
or program a board, open a UART device or access EEPROM. Its evidence level is
RTL simulation only.

Source checkpoint:
`238400187af1e819746a7751363ff1c6ff4d6a11` on
`rl-nexys3-adaptive`.

## Frozen board choices

The Digilent Nexys 3 rev. B reference manual (DOC 502-182, revised 11 April
2016) identifies the 100 MHz oscillator on V10, USB-UART pins N17/N18, the
common-anode display pins and basic I/O pins. The project uses only UART TX, on
N18. Pin names and directions are cross-checked against the Nexys3 master UCF.

| Logical signal | Board function | FPGA pin | Polarity/direction |
|---|---|---|---|
| `clk_100mhz` | GCLK | V10 | input, 100 MHz |
| `btn_reset` | BTNS | B8 | input, pressed high |
| `led_heartbeat` | LD0 | U16 | output, high lights LED |
| `led_reset` | LD1 | V16 | output, high lights LED |
| `seg_n[0..7]` | CA..CG, DP | T17,T18,U17,U18,M14,N14,L14,M13 | active low |
| `an_n[0..3]` | AN0..AN3 | N16,N15,P18,P17 | active low |
| `uart_tx` | FPGA transmit to USB-UART | N18 | 8N1, idle high |

Reference manual:
<https://digilent.com/reference/_media/nexys:nexys3:nexys3_rm.pdf>

## Clock, display and reset

The design uses the 100 MHz board clock directly; the UCF declares a 10 ns
period. A two-flop synchronizer converts the mechanical center-button input to
the synchronous active-high reset used by the B1 logic. No asynchronous reset
is introduced.

The 16-bit displayed counter increments once per second. `LD0` reflects its
least-significant bit, giving a visible heartbeat, and `LD1` reflects the
synchronized reset. The display scans with an 18-bit divider. Each digit is
active for 655.36 microseconds and all four digits refresh every 2.62144 ms,
inside the manual's 1–16 ms guidance. Pressing reset visibly returns the value
to `0000`.

## UART choice and record

The UART is 115200 baud, 8 data bits, no parity, one stop bit, idle high. With
100 MHz input and integer clocks-per-bit 868:

```text
actual baud = 100000000 / 868 = 115207.3732718894
relative error = +0.0064004096 percent
```

Once per accepted one-second update, the transmitter snapshots the newly
displayed counter and sends exactly 16 bytes:

```text
QF5B1,1,<counter_hex4>,0\r\n
```

Hexadecimal letters are uppercase. The snapshot is immutable for the entire
record. Status 0 means B1 OK; it does not claim FDPE, SKAG, routing, policy,
timing closure or physical-board correctness.

## Stage A pass conditions

1. Plain Verilog-2001 compiles with Icarus Verilog in `-g2005` mode.
2. Reset dominance, reset LED, UART idle, all 16 record bytes, counter snapshot,
   four digit enables and hexadecimal segment patterns pass simulation.
3. The UCF contains only the frozen top-level I/O and a 10 ns clock constraint.
4. Exact source and evidence hashes are retained.

ISE build/implementation and physical observation are later B1 sub-gates and
remain prohibited in Stage A.

## Independent assistant review

Decision: **PASS**.

The complete Stage-A installer output was reviewed after execution. Package
and installer hashes matched; branch, local HEAD, upstream and live remote all
matched the accepted Step 2 checkpoint; and the pre-install worktree/index was
clean. All seventeen UCF locations, the 10 ns clock constraint, UART divider
868 and +0.0064004096 percent baud error passed. Simulation matched all sixteen
UART record bytes, all four display digits and both reset cases.

The resulting repository scope was exactly seven authored files plus three
checksum-bound evidence files. Stage A performed zero ISE/XST/NGDBuild/Map/PAR/
TRCE/BitGen operations, zero live-board enumeration, zero UART-device access,
zero programming, zero EEPROM access, zero staging, zero commits and zero
pushes. This review authorizes only the isolated Stage-A checkpoint operation.
B1 ISE implementation remains a separate later sub-gate, and B1 is not yet
complete.
