# QFlow Part C OpenROAD Physical-Design Summary

## Purpose

This document summarizes the completed OpenROAD/SKY130 physical-design evidence for the QFlow Part C VLSI extension.

The purpose is to separate generic synthesis evidence from physical-design evidence and to provide paper-ready wording for the completed RTL-to-GDS kernel implementations.

## Completed physical-design kernels

| Kernel | Design role | Optimization story | Flow status | Final area (µm²) | Final utilization | Route status | Final artifacts |
|---|---|---|---|---:|---:|---|---|
| SKAG-W1 | edge-weight scoring | fixed-alpha shift-add optimization | RTL-to-GDS complete | 6451 | 26% | clean final route evidence | GDS/DEF/SPEF/Verilog/SDC |
| FDPE-V3 | fidelity-decay approximation | 64-entry LUT with linear interpolation | RTL-to-GDS complete | 22186 | 13% | clean final route evidence | GDS/DEF/SPEF/Verilog/SDC |

## Evidence interpretation

The completed OpenROAD physical-design results support two different VLSI claims:

1. **SKAG-W1:** the fixed-alpha shift-add edge-score kernel is physically implementable through the SKY130/OpenROAD flow and supports the multiplier-removal area-optimization story.
2. **FDPE-V3:** the LUT64 linear-interpolation fidelity-decay kernel is physically implementable through the SKY130/OpenROAD flow and supports the FDPE area-accuracy tradeoff story.

## Paper-safe wording

Use wording like:

> The optimized SKAG-W1 and FDPE-V3 kernels were implemented through the open-source SKY130/OpenROAD physical-design flow, completing synthesis, floorplanning, placement, CTS, routing, RC extraction, IR-drop reporting, and final GDS/DEF/SPEF generation.

Do not write:

> The design was fabricated.

Do not write:

> This is commercial ASIC signoff.

Correct boundary:

> These are open-source PDK/OpenROAD physical-design feasibility results, not fabricated-silicon measurements.

## Current publication value

This is now stronger than a pure FPGA/simulation paper because Part C includes two completed RTL-to-GDS kernel implementations.

Recommended next step:

- Run Pareto-C0 through OpenROAD if quick.
- Then start Part D CMOS/ngspice primitive study.
