# QFlow Cloud FPGA Kernel — Evidence Snapshot 04

This snapshot records Hardcore Local Check Step 3 before AWS EC2 F2 launch.

## Result

- Golden vectors reused: 215
- Full pulse-control transaction checks: 215
- Back-to-back transaction subset checks: 32
- Reset-output check: PASS
- Start-during-reset ignored check: PASS
- Reset-mid-transaction clear check: PASS
- RTL compile: PASS
- RTL simulation: PASS
- Control stress rows recorded: 247
- Latency cycles observed in transaction rows: [2]

## Coverage purpose

This step checks the control behavior around the already-passing QFlow cloud kernel: synchronous reset, start pulse, done pulse width, status flags, latency counter reset, repeated transactions, and reset during an active transaction.

## Claim boundary

This is still local RTL simulation evidence only. It is not AWS F2 physical FPGA execution evidence yet.
