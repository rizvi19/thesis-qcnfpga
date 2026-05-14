# QFlow Part C/D — VLSI and CMOS Kernel Study

This branch adds the Post-Part-A ASIC/VLSI and CMOS-level extension for QFlow.

## Evidence boundary

Part A remains frozen and is not rewritten here. The completed QFlow evidence includes:
- mathematical framework,
- Python golden reference,
- RTL verification,
- integrated top-level smoke tests,
- timing/resource evidence,
- canonical 85-cycle / 850 ns hardware decision latency,
- software and OMNeT++ comparison evidence.

This branch adds a new evidence layer:
- ASIC-style physical design feasibility for selected QFlow kernels,
- approximation-vs-quality study,
- area/timing/power reports,
- optional OpenRAM memory macro study,
- CMOS/transistor-level explanation of critical primitives.

## Main research direction

The VLSI extension studies whether QFlow's FDPE, SKAG, and Pareto-selection kernels can be made more area- and energy-efficient by controlled approximation while preserving routing quality.

## Kernels

1. FDPE fidelity-decay kernel
2. SKAG edge-weight kernel
3. PMO-GA Pareto comparator / selector
4. Optional combined QFlow-PPA mini tile

## CMOS primitives

CMOS-level work must be motivated by Part C reports. It should focus on:
- tolerance-aware comparator slice,
- mux / selector logic,
- adder / accumulator path,
- inverter / buffer chain,
- SRAM or memory-interface behavior if OpenRAM is used.

## Claim discipline

Do not claim fabricated silicon.
Do not claim tapeout.
Do not claim full ASIC signoff.
This branch produces open-source physical-design feasibility and transistor-level analysis evidence.
