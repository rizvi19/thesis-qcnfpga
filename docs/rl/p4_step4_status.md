# P4 Step 4 Status

Step 4 implements only the frozen learned policy-index ROM. The synthesizable
Verilog-2001 module consumes the committed
`results/rl/p3_export/policy_rom.mem` artifact directly. Its address is the
eight-bit state ID and its output is the two-bit proposed action.

The ROM contract is 256 state-major entries, one hexadecimal digit per line,
with actions 0 through 3. The memory file must remain byte-identical to the P3
checkpoint, match the selected seed-229 policy, exercise all four actions, and
retain the P3 checksum and layout record.

Verification explicitly reads every address 0 through 255. Additional vectors
prove synchronous reset dominance, deterministic action-zero reset output,
one-cycle registered valid/read behavior, disabled-read output holding, and a
first read after reset. Exact action agreement is required with zero waived
mismatches.

This step does not implement the profile ROM, dwell controller or integrated
controller. It performs no ISE synthesis, timing analysis, board programming,
EEPROM operation, training, Q-table argmax, or policy revision.
