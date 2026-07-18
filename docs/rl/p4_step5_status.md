# P4 Step 5 Status

Step 5 implements only the frozen four-entry profile ROM. The Verilog-2001
module consumes `results/rl/p3_export/profile_rom.mem` directly. Its two-bit
action address selects one registered 18-bit coefficient payload.

The artifact must remain four action-major, uppercase, five-hex-digit words.
All four payloads must be distinct, fit in 18 useful bits, total exactly 72
useful bits, match the frozen profile codebook, and round-trip through the P3
decoder to four U2.1 alpha numerators and three two-bit Tchebycheff ratios.

Verification explicitly reads actions 0 through 3 and checks every payload
bit. Additional vectors prove synchronous reset dominance, deterministic zero
reset output, one-cycle registered valid/read behavior, disabled-read output
holding, and the first read following reset. No payload mismatch may be waived.

This step does not implement dwell logic or the integrated controller. It
performs no ISE synthesis, timing analysis, board programming, EEPROM access,
training, Q-table argmax, or policy/profile revision.
