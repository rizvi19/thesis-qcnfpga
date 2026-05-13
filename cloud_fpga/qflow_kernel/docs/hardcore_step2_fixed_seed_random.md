# Hardcore Local Check Step 2 — Fixed-Seed Randomized Regression

## Goal

Step 2 expands the local pre-AWS regression beyond the deterministic Step-1 cases. It keeps the 15 deterministic tests and appends 200 fixed-seed randomized tests.

## Why this matters before AWS

AWS EC2 F2 time should not be used to discover simple selector, invalid-path, threshold, status-bit, or score-arithmetic bugs. This step increases confidence while still remaining fully local and free.

## What is checked

- 215 total vectors are generated.
- 200 vectors are fixed-seed randomized.
- RTL compilation passes.
- RTL simulation passes.
- Hardware-output CSV exactly matches Python golden CSV.
- All compare rows are PASS.
- Valid-path and no-path cases both appear.
- `status_flags` are sanity-checked.
- `latency_cycles` remains stable in the current wrapper.

## Claim boundary

This is local RTL simulation evidence only. It must not be described as AWS F2 physical FPGA execution evidence.
