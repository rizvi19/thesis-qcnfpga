# Hardcore Local Check Step 4 — X/Z Output-Sanity Regression

This step checks simulation hygiene before AWS EC2 F2. The arithmetic and control checks already passed in Steps 1–3, but an FPGA-host wrapper must also avoid unknown or high-impedance values on observable output ports.

## What this step checks

- Outputs are driven to clean zero values during reset.
- Outputs contain no `X` or `Z` after reset.
- Outputs contain no `X` or `Z` immediately after the `start` pulse.
- Outputs contain no `X` or `Z` when `done` asserts.
- Outputs contain no `X` or `Z` after `done` deasserts.
- Selected path, score, bottleneck fidelity, latency cycles, and status flags still match the fixed-seed golden vectors.
- `done`, `valid_path`, and `no_path` remain consistent with expected-valid/no-path behavior.

## Command

```bash
./scripts/07_hardcore_step4_x_sanity.sh
```

## Expected final line

```text
STEP 4 PASS: X/Z output-sanity local regression is clean.
```

## Claim boundary

This remains local RTL simulation evidence only. It is not AWS F2 physical FPGA execution evidence.
