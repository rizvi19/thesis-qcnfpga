# Section Draft: Discussion and Limitations

## Section purpose

This section discusses what the layered QFlow hardware evidence demonstrates, how the RTL/Yosys, OpenROAD, and CMOS/ngspice results should be interpreted, and what limitations remain before the work can be considered a complete fabricated hardware system.

## Evidence hierarchy

The QFlow evaluation is organized as a layered hardware evidence stack:

1. RTL and generic Yosys synthesis evidence.
2. SKY130/OpenROAD physical-design evidence for selected decision kernels.
3. Representative CMOS/ngspice primitive evidence for route-selection logic.

This hierarchy is important because each layer answers a different question. RTL/Yosys evaluation compares kernel-level design alternatives. OpenROAD physical design shows that selected kernels can be taken through a complete open-source RTL-to-GDS flow. CMOS/ngspice primitive simulation provides a lower-level circuit perspective for selected selector/comparator primitives.

## Interpretation of RTL/Yosys results

The RTL/Yosys results are useful for comparing design alternatives under a common generic synthesis setup. They show how different architectural choices affect generic cell count and approximation behavior.

The FDPE results should be interpreted as an area-accuracy tradeoff. Reducing LUT depth can reduce some logic cost, while interpolation improves approximation behavior but increases synthesized logic. The SKAG results show that replacing runtime multiplier-heavy scoring with fixed shift-add scoring strongly reduces generic synthesized cell count for the evaluated scoring kernel. The Pareto selector results show that the selector/comparator logic is compact relative to the larger FDPE and SKAG kernels.

These results should not be interpreted as final commercial ASIC area or fabricated-silicon measurements.

## Interpretation of OpenROAD physical-design results

The OpenROAD results provide the strongest VLSI evidence in this work. Three representative QFlow decision kernels completed the open-source SKY130/OpenROAD RTL-to-GDS flow:

- SKAG-W1 for edge-weight scoring.
- FDPE-V3 for fidelity-decay approximation.
- Pareto-C0 for route-candidate selector/comparator logic.

The physical-design results demonstrate that the selected kernels can pass through synthesis, floorplanning, placement, clock-tree synthesis, routing, final extraction/reporting, and final GDS/DEF/SPEF generation.

The final physical-design areas were:

| Kernel | Final area | Final utilization |
|---|---:|---:|
| SKAG-W1 | 6451 um^2 | 26% |
| FDPE-V3 | 22186 um^2 | 13% |
| Pareto-C0 | 3368 um^2 | 13% |

These results strengthen the work beyond simulation-only evaluation because they show a reproducible physical-design path for the main QFlow decision-kernel classes.

## Interpretation of CMOS/ngspice primitive results

The CMOS/ngspice results complement the standard-cell physical-design evidence with representative primitive-level circuit behavior. The selected primitives are connected to the Pareto-C0 route-selection path:

- A 2:1 transmission-gate mux represents selector behavior.
- A 1-bit XNOR/equality primitive represents comparator/equality behavior.

The mux load sweep showed the expected trend: delay and estimated load-switching energy increase as output load capacitance increases.

| Load capacitance | Average delay | Estimated load switching energy |
|---:|---:|---:|
| 5 fF | 10.38 ps | 8.10 fJ |
| 10 fF | 17.27 ps | 16.20 fJ |
| 20 fF | 26.64 ps | 32.40 fJ |
| 50 fF | 54.31 ps | 81.00 fJ |

The XNOR/equality primitive gave an average delay of approximately 26.64 ps under a 1.8 V supply and 20 fF load.

These CMOS/ngspice results should be interpreted as representative primitive-level support, not as full-chip transistor-level simulation.

## What the evidence proves

The current evidence supports the following claims:

1. The QFlow decision pipeline can be decomposed into hardware-relevant decision kernels.
2. FDPE, SKAG, and Pareto selector kernels can be evaluated at RTL/generic synthesis level.
3. Selected optimized kernels can complete an open-source SKY130/OpenROAD RTL-to-GDS physical-design flow.
4. Representative selector and comparator primitives from the Pareto-C0 path can be evaluated with ngspice at transistor level.
5. The work provides a layered hardware feasibility path from RTL to physical design and primitive-level CMOS simulation.

## What the evidence does not prove

The current evidence does not prove:

- fabricated-silicon functionality,
- commercial signoff readiness,
- measured silicon timing,
- measured silicon power,
- full-chip transistor-level simulation,
- full-system ASIC tapeout,
- or complete FPGA/cloud board validation.

## Main limitations

### No fabricated silicon

The work does not include fabricated ASIC measurements. The OpenROAD results are physical-design feasibility evidence using an open-source PDK and flow, not silicon measurement.

### No commercial signoff

The generated GDS/DEF/SPEF artifacts are valuable research evidence, but they are not equivalent to commercial signoff. Additional signoff-quality timing, power, physical verification, and foundry checks would be required before fabrication.

### Primitive-level CMOS only

The ngspice experiments evaluate representative mux and XNOR/equality primitives. They do not simulate the entire QFlow datapath at transistor level.

### First-order MOS model

The CMOS/ngspice simulations use simple Level-1 MOS models. These are useful for first-pass circuit behavior and educational/research interpretation, but they are not calibrated SKY130 transistor-level models.

### FPGA/cloud validation pending

The FPGA/cloud validation path remains a parallel work item. The ASIC/VLSI evidence strengthens the paper, but it does not replace real FPGA/cloud execution evidence.

## Future work

Future work should include:

1. Completing FPGA/cloud validation.
2. Running calibrated SKY130 transistor-level simulations for selected extracted primitives.
3. Extending OpenROAD implementation from individual kernels toward larger integrated subsystems.
4. Performing more detailed post-layout timing and power analysis.
5. Exploring memory macro integration for lookup-heavy FDPE structures.
6. Investigating a future tapeout-oriented flow if resources become available.

## Paper-ready paragraph

The QFlow evidence stack should be interpreted as a layered hardware feasibility study rather than a fabricated-chip demonstration. RTL/Yosys evaluation compares kernel-level design alternatives, OpenROAD/SKY130 physical design demonstrates RTL-to-GDS feasibility for three representative decision kernels, and ngspice primitive simulations provide circuit-level support for selected selector/comparator behaviors. The strongest physical-design evidence is the successful OpenROAD implementation of SKAG-W1, FDPE-V3, and Pareto-C0, which generated final GDS/DEF/SPEF artifacts. However, the work does not report fabricated-silicon measurement, commercial signoff, full-chip transistor-level simulation, or completed FPGA/cloud validation. These boundaries are important for accurately positioning the contribution as a reproducible open-source hardware feasibility stack.
