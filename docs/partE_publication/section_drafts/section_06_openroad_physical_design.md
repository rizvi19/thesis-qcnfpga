# Section Draft: OpenROAD/SKY130 Physical Design of QFlow Kernels

## Section purpose

This section reports the open-source physical-design implementation of the selected QFlow decision kernels using the SKY130/OpenROAD flow. The goal is to show that the optimized QFlow kernels are not only RTL/generic-synthesis blocks, but can also be taken through a complete RTL-to-GDS physical-design path.

## Physical-design scope

Three representative QFlow kernels were selected for physical implementation:

1. SKAG-W1: fixed-alpha shift-add edge-weight scoring kernel.
2. FDPE-V3: LUT64 linear-interpolation fidelity-decay approximation kernel.
3. Pareto-C0: full route-candidate selector/comparator kernel.

Together, these kernels cover the main QFlow decision pipeline:

FDPE fidelity decay -> SKAG edge scoring -> Pareto route selection.

## Tool flow

The physical implementation used the open-source SKY130/OpenROAD-flow-scripts environment. Each kernel was processed through synthesis, floorplanning, placement, clock-tree synthesis, routing, final report generation, RC extraction, IR-drop reporting, and GDS/DEF/SPEF generation.

The flow stages were:

1. RTL import and synthesis.
2. Floorplanning and power-grid preparation.
3. Global and detailed placement.
4. Clock-tree synthesis.
5. Global and detailed routing.
6. Final extraction/reporting.
7. Final GDS/DEF/SPEF/netlist generation.

## Physical-design results

| Kernel | Design role | Flow status | Final area | Final utilization | Final artifacts |
|---|---|---|---:|---:|---|
| SKAG-W1 | Edge-weight scoring | RTL-to-GDS complete | 6451 um^2 | 26% | GDS/DEF/SPEF/Verilog/SDC |
| FDPE-V3 | Fidelity-decay approximation | RTL-to-GDS complete | 22186 um^2 | 13% | GDS/DEF/SPEF/Verilog/SDC |
| Pareto-C0 | Route-candidate selector/comparator | RTL-to-GDS complete | 3368 um^2 | 13% | GDS/DEF/SPEF/Verilog/SDC |

## Interpretation

The three completed physical-design runs provide a layered implementation view of the QFlow decision pipeline. SKAG-W1 demonstrates that the edge-scoring logic can be implemented compactly after replacing runtime multiplier-based weighting with fixed shift-add scoring. FDPE-V3 demonstrates that the LUT/interpolation fidelity-decay approximation can be physically implemented despite its larger arithmetic and lookup structure. Pareto-C0 demonstrates that the route-candidate selector/comparator block can be implemented as a compact physical kernel.

The physical-design evidence strengthens the QFlow hardware story because it moves beyond RTL simulation and generic synthesis. The generated artifacts include final GDS, DEF, SPEF, Verilog netlists, SDC files, logs, reports, and layout images for the selected kernels.

## Figure references

Recommended figures for this section:

- OpenROAD RTL-to-GDS flow diagram.
- SKAG-W1 final layout/routing/IR-drop views.
- FDPE-V3 final layout/routing/IR-drop views.
- Pareto-C0 final layout/routing/IR-drop views.
- Combined OpenROAD physical-design summary table.

## Safe wording

The correct claim is:

The SKAG-W1, FDPE-V3, and Pareto-C0 kernels completed an open-source SKY130/OpenROAD RTL-to-GDS physical-design flow, including final GDS/DEF/SPEF artifact generation.

Do not claim:

- fabricated silicon,
- tapeout,
- commercial signoff,
- measured silicon timing,
- measured silicon power,
- or full-system chip implementation.

## Limitations

These results are open-source PDK/OpenROAD physical-design feasibility results. They are not fabricated-silicon measurements and should not be interpreted as commercial signoff. Full-chip integration, calibrated power analysis, board validation, and fabricated-silicon evaluation remain future work.

## Paper-ready paragraph

To evaluate the physical feasibility of the QFlow decision kernels, three representative blocks were implemented using the open-source SKY130/OpenROAD flow. The SKAG-W1 edge-scoring kernel, FDPE-V3 fidelity-decay approximation kernel, and Pareto-C0 route-candidate selector each completed synthesis, floorplanning, placement, clock-tree synthesis, routing, final report generation, RC extraction, IR-drop reporting, and final GDS/DEF/SPEF generation. The final reported design areas were 6451 um^2 for SKAG-W1, 22186 um^2 for FDPE-V3, and 3368 um^2 for Pareto-C0. These results provide physical-design feasibility evidence for the major QFlow decision-kernel classes while remaining distinct from fabricated-silicon measurement or commercial signoff.
