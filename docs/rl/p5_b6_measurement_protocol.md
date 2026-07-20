# P5 Step 8 / B6 Kernel-Cycle Measurement Protocol

B6 wraps the accepted B5 H0-H4 policy shell without changing its routing,
profile-selection, status or handshake behavior.

A request is accepted on synchronous edge N only when `start && ready` is true.
The counter is zeroed on N. During the one-cycle `done` pulse, `cycles` records
`N_done - N` and `cycles_valid` is asserted. An invalid accepted request therefore
records one cycle. A start presented while busy is not accepted and cannot reset
or restart the active counter.

The counter measures synchronous kernel cycles only. It excludes UART
serialization, host parsing, USB/JTAG transfer, FPGA programming and human
observation. At 100 MHz, kernel time in nanoseconds is `cycles * 10`.

The host audit covers 20 deterministic request cases across all five modes,
yielding 100 measured completions. It compares every published count with the
testbench-observed accepted-edge-to-done distance and writes both per-case and
per-mode CSV evidence. The simulation is executed twice and must be byte-exact.
