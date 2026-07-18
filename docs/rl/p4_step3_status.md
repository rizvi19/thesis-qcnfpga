# P4 Step 3 Status

Step 3 implements only the frozen `rl_state_encoder.v` boundary from the P4
RTL contract. The module is synthesizable Verilog-2001 with a synchronous,
active-high reset and one registered output stage.

The four inputs are 16-bit UNORM codes. Exact threshold equality enters the
higher bin, and the packed result is `{key_bin, fidelity_bin, load_bin,
imbalance_bin}`. The encoded endpoints `0` and `65535`, reset dominance,
disabled-output hold behavior, every threshold below/equal/above case, and all
256 radix-4 state categories are required.

`p4_generate_state_encoder_vectors.py` deterministically emits 297 explicit
unit vectors in reviewable CSV and numeric RTL-testbench formats. The tracked
vectors must regenerate byte-for-byte, the independent Python contract tests
must pass, and the Verilog-2001 testbench must report zero mismatches before
Step 3 can be reviewed.

This step does not implement the policy ROM, profile ROM, dwell controller or
integrated controller. It performs no ISE synthesis, timing analysis, board
programming, EEPROM operation, training, or policy revision.
