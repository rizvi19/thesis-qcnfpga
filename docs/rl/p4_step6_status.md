# P4 Step 6 Status

Step 6 integrates the reviewed state encoder, learned policy ROM, and profile
ROM into `rl_controller.v`. A valid request accepted on `start && ready`
completes after the frozen three-stage latency with `done` and `output_valid`.
The controller is busy during the transaction and rejects additional starts
with a one-cycle `stall` indication.

The minimum-dwell guard is exactly three accepted valid decisions. The first
post-reset proposal is accepted with count one. An early different proposal is
held while the saturated count advances; an eligible different proposal is
accepted with count one and `switched`. There is no pending-action register.
No-path requests still select a policy/profile and advance dwell. Invalid
requests and busy stalls do not update dwell.

Reset is synchronous, active-high, and dominant. An invalid request completes
after the frozen one-cycle response latency with `invalid_state` and no
output-valid decision. All published state, action,
profile, switch, dwell, and no-path results are aligned with the completion
pulse. The internal dwell count saturates at three.

This step performs controller unit verification only. The broader exhaustive
integrated trace ladder remains Step 7/8. No ISE synthesis, timing claim, board
programming, EEPROM access, training, or online Q update is performed.
