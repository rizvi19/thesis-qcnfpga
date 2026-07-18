# P4 Policy-ROM Deployment Decision

The defense P4 controller deploys `policy_rom.mem`, not a runtime Q-table
argmax. The policy contains the learned action for every one of the 256 frozen
states and has already been proven equal to the argmax of the quantized audit
Q-table at all 256 states.

This choice preserves reinforcement-learned online adaptation: live state still
selects a learned profile on every accepted decision. Only training and Q-value
updates remain offline.

The policy ROM requires 256 two-bit useful entries, while the audit Q-table
requires 1,024 signed 16-bit entries plus comparators and tie logic. Avoiding
runtime argmax reduces Spartan-6 storage, comparison logic, latency and
verification risk without changing the frozen policy.

Consequently, `rl_argmax.v` is not required and `q_update.v` remains a
journal-only option. The work must be described as reinforcement-learned
adaptive control with frozen inference, not online FPGA learning.
