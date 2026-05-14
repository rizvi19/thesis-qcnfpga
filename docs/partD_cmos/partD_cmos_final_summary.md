# Part D CMOS/ngspice Final Summary

## Purpose

This document summarizes the completed representative CMOS/ngspice primitive evidence for the QFlow Part D extension.

Part C demonstrated standard-cell physical feasibility using the SKY130/OpenROAD RTL-to-GDS flow. Part D complements that evidence with transistor-level primitive simulations connected to the Pareto-C0 route-candidate selector/comparator path.

## Completed primitives

| Primitive | QFlow connection | Main result | Artifacts |
|---|---|---|---|
| 2:1 transmission-gate mux | Selector behavior in Pareto-C0 route-candidate selection | Single-load delay at 20 fF: average 26.64 ps; estimated load energy 32.4 fJ | SPICE, ngspice log, waveform CSV, waveform PNG, summary CSV |
| 2:1 transmission-gate mux load sweep | Capacitive-load behavior of selector primitive | Delay increased from 10.38 ps at 5 fF to 54.31 ps at 50 fF; energy increased from 8.10 fJ to 81.00 fJ | sweep CSV, delay plot, energy plot, logs, waveform CSVs |
| 1-bit XNOR/equality primitive | Comparator/equality behavior in Pareto-C0 route-candidate comparison | Average delay at 20 fF: 26.64 ps; estimated load energy 32.4 fJ | SPICE, ngspice log, waveform CSV, waveform PNG, summary CSV |

## TG mux load-sweep result

| Load capacitance | Average delay | Estimated load switching energy |
|---:|---:|---:|
| 5 fF | 10.38 ps | 8.10 fJ |
| 10 fF | 17.27 ps | 16.20 fJ |
| 20 fF | 26.64 ps | 32.40 fJ |
| 50 fF | 54.31 ps | 81.00 fJ |

## Interpretation

The Part D results provide representative CMOS-level evidence for two primitive behaviors used by the Pareto-C0 selector/comparator path:

1. Mux/selector behavior, represented by the 2:1 transmission-gate mux.
2. Comparator/equality behavior, represented by the 1-bit XNOR/equality primitive.

The mux load sweep shows the expected trend: increasing output capacitance increases propagation delay and output-load switching energy. The XNOR/equality primitive gives comparator-side transistor-level evidence with similar 20 fF delay behavior.

## Evidence boundary

These results are representative primitive-level ngspice simulations using simple Level-1 MOS models.

They are not:

- full-chip SPICE simulations,
- fabricated-silicon measurements,
- foundry signoff,
- commercial signoff,
- calibrated SKY130 transistor-level simulations,
- or extracted-layout SPICE simulations.

## Paper-safe wording

To complement the standard-cell OpenROAD physical implementation, representative CMOS primitives from the Pareto-C0 route-selection path were evaluated using ngspice. A 2:1 transmission-gate mux was used to study selector behavior, including a load sweep from 5 fF to 50 fF. A 1-bit XNOR/equality primitive was used to study comparator-side behavior. These primitive-level simulations provide transistor-level supporting evidence while remaining distinct from full-chip SPICE or fabricated-silicon measurement.

## Recommended use in paper

Use this Part D evidence as a supporting circuit-level layer, not as the main contribution. The main VLSI contribution remains the OpenROAD RTL-to-GDS implementation of SKAG-W1, FDPE-V3, and Pareto-C0.
