# Part D CMOS/ngspice Execution Plan

## Purpose

Part D adds a transistor/circuit-level evidence layer to the QFlow VLSI extension.

Part C already completed RTL-to-GDS OpenROAD physical implementation for:

- SKAG-W1
- FDPE-V3
- Pareto-C0

Part D will not transistor-model the full QFlow system. Instead, it studies representative CMOS primitives from the QFlow decision datapath.

## Selected primitive

Initial target: Pareto-C0 selector/mux primitive.

Reason:

- Pareto-C0 is route-selection logic.
- Selector and mux behavior directly appears in candidate selection.
- CMOS mux delay and energy are easy to explain at transistor level.
- This complements the standard-cell OpenROAD physical-design evidence.

## Planned evidence

1. CMOS-level SPICE netlist
2. ngspice transient simulation
3. input/output waveform CSV
4. propagation delay estimate
5. simple dynamic-energy estimate
6. paper-safe interpretation

## Boundary

This is representative primitive-level CMOS/ngspice evidence, not full-chip SPICE and not fabricated-silicon signoff.

## First circuit

Start with a 2:1 transmission-gate mux, because route/candidate selection uses mux-style data selection.
