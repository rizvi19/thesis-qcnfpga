# Part C VLSI Kernel Evidence Summary

## Purpose

This document summarizes the current Part C ASIC/VLSI kernel-level evidence for QFlow.

The goal is to show that the post-Part-A VLSI extension is not random hardware work. It is built around the actual computational kernels of the QFlow design:

1. FDPE fidelity-decay approximation
2. SKAG edge-weight scoring
3. Pareto route-candidate selection

## Current evidence level

This is currently generic Yosys synthesis evidence plus RTL simulation and numerical approximation analysis.

It is not yet OpenROAD physical-design evidence, post-layout timing evidence, post-layout power evidence, or fabricated silicon evidence.

## Kernel family 1: FDPE

FDPE computes stored-key fidelity decay using a fixed-point exponential approximation.

### FDPE variants

| Variant | Design | Generic Yosys cells | Main meaning |
|---|---|---:|---|
| FDPE-V0 | 256-entry LUT, floor lookup | 2258 | baseline |
| FDPE-V1 | 128-entry LUT, floor lookup | 1944 | area-saving but higher error |
| FDPE-V2 | 128-entry LUT, linear interpolation | 3399 | high-accuracy but costly |
| FDPE-V3 | 64-entry LUT, linear interpolation | 3014 | balanced interpolation candidate |

### FDPE interpretation

FDPE shows a real LUT/interpolation area-accuracy tradeoff.

The 128-entry floor-LUT version reduces cell count by 13.91% compared with FDPE-V0 but increases approximation error.

The 128-entry interpolation version gives much better approximation accuracy but costs more logic.

The 64-entry interpolation version reduces the interpolation cost compared with FDPE-V2 while keeping practical-range error around 0.20%.

## Kernel family 2: SKAG weight scoring

SKAG computes edge scores from key count, average fidelity, arrival rate, and QBER.

### SKAG variants

| Variant | Design | Generic Yosys cells | Main meaning |
|---|---|---:|---|
| SKAG-W0 | runtime weighted score with four 16x16 products | 5343 | flexible but expensive |
| SKAG-W1 | fixed-alpha shift-add score | 503 | same tested scores, much smaller |

### SKAG interpretation

SKAG gives the strongest area optimization result so far.

Replacing runtime weighted multiplication with fixed shift-add weights reduced generic cell count from 5343 cells to 503 cells.

That is a 90.59% reduction while preserving the tested score outputs.

This suggests that configurable runtime weights are expensive, but fixed or policy-selected weights can be implemented very efficiently.

## Kernel family 3: Pareto comparator / selector

The Pareto selector chooses between two route candidates using score, fidelity, key count, hop count, and QBER.

### Pareto variants

| Variant | Design | Generic Yosys cells | Main meaning |
|---|---|---:|---|
| Pareto-C0 | full Pareto dominance comparator plus tie-break | 497 | compact full selector |
| Pareto-C1 | score-first priority selector | 472 | modest area reduction |

### Pareto interpretation

The full Pareto comparator is already compact.

The score-first selector reduces cell count by about 5.03%, from 497 to 472 cells.

Therefore, the Pareto selector is not the main area bottleneck. The larger optimization opportunities are in SKAG arithmetic and FDPE approximation.

## Current best kernel-level findings

| Finding | Evidence |
|---|---|
| FDPE has a meaningful LUT/interpolation area-accuracy tradeoff | V0/V1/V2/V3 comparison |
| SKAG runtime weights are expensive | W0 = 5343 cells |
| SKAG fixed shift-add weights are highly efficient | W1 = 503 cells, 90.59% reduction |
| Pareto full selector is already compact | C0 = 497 cells |
| Score-first Pareto selector gives only modest savings | C1 = 472 cells, 5.03% reduction |

## Recommended next Part C step

The next major step should be physical-design evidence.

Recommended OpenROAD/OpenLane candidates:

1. SKAG-W1 because it is compact and shows the strongest VLSI optimization.
2. FDPE-V3 because it is the best balanced FDPE interpolation candidate.
3. Pareto-C0 because it is compact and represents full route-candidate selection.

## Recommended Part D CMOS direction

Part D CMOS should be motivated by the Part C results.

The best CMOS primitive candidates are:

1. comparator chain from Pareto-C0/C1
2. adder/accumulator path from SKAG-W1
3. mux/LUT read path from FDPE
4. buffer/inverter chain for critical-path cleanup after OpenROAD timing

The CMOS work should not be random inverter/full-adder demonstration. It should be connected to a measured bottleneck from the Part C reports.

## Evidence boundary

These results are suitable as kernel-level preliminary VLSI evidence.

They should not be presented as final ASIC signoff. The next step is OpenROAD/OpenLane physical-design reporting with area, timing, utilization, and power.
