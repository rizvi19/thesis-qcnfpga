# P4 Step 8 Status

Step 8 is the exhaustive vector, Verilog-2001 lint, and reproducibility gate
for the reviewed P4 controller. It changes no RTL, policy, profile, Q table,
training result, or prior evidence.

Every state ID from 0 through 255 is exercised as an isolated post-reset
decision. This makes the selected action equal to the frozen policy proposal
without dwell history, and requires the exact action-indexed 18-bit profile
payload. All 36 below/equal/above threshold cases are also isolated and checked;
equality must enter the higher bin. The all-zero and all-65535 encoded endpoints
and one isolated case for each of the four policy actions are explicit.

A final directed sequence covers reset dominance, the one-cycle invalid
response, start while busy, back-to-back requests, no-path passthrough, dwell
hold, and dwell switch. Every valid request must complete after three cycles.
No unexplained state, action, payload, handshake, or status mismatch is allowed.

The deployment decision remains the reviewed policy-index ROM. The 1,024-word
Q table is audit-only; runtime argmax, `rl_argmax.v`, `q_update.v`, and online or
on-chip learning are excluded. Icarus is run in Verilog-2001 mode with warning
and implicit-net checks as the portable lint gate. This is not ISE synthesis,
timing closure, resource measurement, board programming, or EEPROM access;
those authorized synthesis activities begin only in Step 9.
