# Hardcore Local Check Step 3 — Control/Reset/Start-Pulse Stress

## Goal

Step 3 checks control behavior after the arithmetic and randomized vector checks are already passing.

## Why this matters before AWS

An AWS host program will interact with the kernel through register-style transactions. Even if arithmetic is correct, AWS time can be wasted if reset, start, done, status flags, or repeated transactions behave unexpectedly.

## What is checked

- Reset clears output/status registers.
- Start asserted during reset is ignored.
- Reset during an active transaction clears the kernel.
- One-cycle start pulse produces a done response.
- Done deasserts after one cycle.
- `latency_cycles` is stable at the current local-wrapper value.
- Valid/no-path status bits match the golden expectation.
- A back-to-back subset of transactions runs without stale state carryover.

## Claim boundary

This is local RTL simulation evidence only. It must not be described as AWS F2 physical FPGA execution evidence.
