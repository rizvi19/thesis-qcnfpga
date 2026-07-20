# P5 UART and evidence-channel boundary

The completed P5 QFlow-Mini datapath includes state/profile selection, candidate
evaluation, deterministic status outputs and an accepted-edge-to-done kernel
cycle counter. B1-B6 have preserved RTL simulation, ISE implementation,
bitstream identities and human-observed LED/seven-segment evidence.

A physical raw-UART capture is **not claimed as completed in P5**. The current
board evidence channel is the deterministic self-test plus LEDs and
seven-segment display. The result-record fields are frozen for P6 as:

`test_id, policy_id, state_id, profile_id, selected_path, score,
bottleneck_fidelity, cycles, status`

P6 must add or validate the board transport, save the raw output, parse it into
`board_results.csv`, and keep UART/host time outside the kernel-cycle metric.
This explicit carry-over prevents a simulated or planned UART channel from
being misreported as physical evidence.
