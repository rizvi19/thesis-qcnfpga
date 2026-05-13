# QFlow AWS F2 Local Readiness Note

## Status

The QFlow cloud-FPGA kernel has passed local pre-AWS hardening gates through the AWS-style MMIO/register-map wrapper stage.

## Local gates completed

- Gate 1: extended deterministic regression
- Gate 2: fixed-seed randomized regression
- Gate 3: reset/control/start-pulse stress
- Gate 4: X/Z output-sanity regression
- Gate 5: strict compile, lint-style checks, and generic synthesis
- Gate 6: AWS-style MMIO/register-map wrapper simulation and generic synthesis

## Evidence boundary

This package proves local RTL, control, MMIO, and generic synthesis readiness. It is not yet AWS F2 physical FPGA execution evidence.

## Next AWS action after this gate

Only after committing this gate should the AWS account/quota/budget/session setup begin. The first cloud session should run the official AWS FPGA example before integrating QFlow.
