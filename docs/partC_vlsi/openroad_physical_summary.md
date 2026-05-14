# QFlow Part C OpenROAD Physical-Design Summary

## Purpose

This document summarizes the completed SKY130/OpenROAD physical-design evidence for the QFlow Part C VLSI extension.

These are open-source PDK/OpenROAD physical-design feasibility results, not fabricated-silicon measurements.

## Completed physical-design kernels

| Kernel | Design role | Optimization / implementation story | Flow status | Final area (um^2) | Final utilization | Route status | Final artifacts |
|---|---|---|---|---:|---:|---|---|
| SKAG-W1 | edge-weight scoring | fixed-alpha shift-add scoring; removes runtime multipliers | RTL-to-GDS complete | 6451 | 26% | clean final route evidence | GDS/DEF/SPEF/Verilog/SDC |
| FDPE-V3 | fidelity-decay approximation | 64-entry LUT with linear interpolation | RTL-to-GDS complete | 22186 | 13% | clean final route evidence | GDS/DEF/SPEF/Verilog/SDC |
| Pareto-C0 | route-candidate selector/comparator | full Pareto comparator with tie-break logic | RTL-to-GDS complete | 3368 | 13% | clean final route evidence | GDS/DEF/SPEF/Verilog/SDC |


## Interpretation

The completed OpenROAD results support three different physical-design claims:

1. SKAG-W1 supports the multiplier-removal / shift-add edge-score optimization story.
2. FDPE-V3 supports the LUT/interpolation area-accuracy approximation story.
3. Pareto-C0 supports the physical feasibility of the route-candidate selector/comparator.

Together, these three kernels cover the main QFlow decision pipeline:

FDPE fidelity decay -> SKAG edge scoring -> Pareto route selection

## Paper-safe wording

Recommended wording:

The optimized QFlow kernels were implemented through the open-source SKY130/OpenROAD physical-design flow. The SKAG-W1, FDPE-V3, and Pareto-C0 kernels completed synthesis, floorplanning, placement, clock-tree synthesis, routing, RC extraction, IR-drop reporting, and final GDS/DEF/SPEF generation.

Important boundary:

These are open-source PDK/OpenROAD physical-design feasibility results. They are not fabricated-silicon measurements and not commercial signoff.

## Publication value

This strengthens the QFlow paper beyond pure simulation or FPGA-only evidence because the work now includes a reproducible RTL-to-GDS path for the three major hardware kernels.
