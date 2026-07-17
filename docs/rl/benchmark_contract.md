# QFlow-RL H0-H4 Benchmark Contract

## Purpose

This contract ensures that the defense comparison answers controller quality
and hardware-cost questions without presenting cross-platform speed as
algorithm superiority.

## Comparison classes

| Class | Purpose | Permitted conclusion |
|---|---|---|
| A | H0-H4 on the same Nexys 3 shell | Direct controller hardware comparison |
| B | Same algorithm and vectors on CPU and FPGA | Platform acceleration only |
| C | H0-H4 on identical network traces | Network-utility comparison |
| D | Published FPGA routing, GA, RL and QKD work | Component-level context only |

## Same-board controllers

| ID | Controller | Role |
|---|---|---|
| H0 | Feasible shortest-distance | Minimal routing baseline |
| H1 | Fixed key-aware | Value of key awareness |
| H2 | Existing fixed QFlow | Current alpha/lambda anchor |
| H3 | Threshold/rule adaptive | Whether adaptation alone is sufficient |
| H4 | Tabular QFlow-RL | Learned adaptive contribution |

H5 tiny DQN is journal-only and excluded from the defense critical path.

## Common experimental shell

All H0-H4 builds use the same Ring-6 topology, directed-link state, candidate
paths, replay requests, numeric widths, clock/reset/start/done protocol, clock
constraint, Nexys 3 UCF, output fields and measurement code. `POLICY_MODE` is
compile-time so only one controller is synthesized per build while the
external shell remains unchanged.

Initial numeric contract: Q0.16 fidelity, Q16.16 weights where feasible,
four candidate paths, four coefficient profiles and deterministic tie-breaking
by lowest path/profile index. Any reduction requires a new build tag and
renewed golden-vector validation.

## Frozen measurement definitions

- Kernel cycles: accepted `start` to asserted `route_valid`.
- Kernel time: kernel cycles divided by achieved post-PAR clock frequency.
- UART/host time: reported separately and never added to kernel latency.
- Resources: total LUT/FF/BRAM/DSP plus controller-only incremental cost.
- Timing: achieved post-PAR timing for the exact reported bitstream.
- Power: one common method and activity assumption; estimated remains labelled estimated.
- Network metrics: blocking ratio, success ratio, bottleneck fidelity, path
  cost/hops, balance/utilization and profile-switch rate on paired traces.

## Reproducibility and statistics

Every comparison uses identical trace checksums and seeds. Raw per-request
rows are retained. Report paired means, 95% confidence intervals, effect size
and a suitable paired test when the sample count supports it. Negative or
non-significant results remain visible.

## Defense gates

H4 must use at least two profiles on held-out changing conditions, remain
within a predeclared 0.5 percentage-point blocking margin of H2, and improve
at least one predeclared quality metric without hiding serious degradation.
Forced-balanced H4 must reproduce H2 before learned-policy results are valid.
