# Section Draft: Conclusion and Future Work

## Section purpose

This section concludes the QFlow VLSI/CMOS extension paper by summarizing the layered hardware evidence stack, highlighting the main technical results, restating the evidence boundaries, and identifying future work.

## Conclusion summary

This work presented QFlow as a layered hardware feasibility study for quantum-inspired network decision acceleration. The central idea is to decompose the network decision process into hardware-oriented kernels and evaluate those kernels through progressively deeper implementation layers.

The QFlow pipeline is organized around three main decision-kernel families:

1. FDPE for stored-key fidelity decay approximation.
2. SKAG for edge-weight and link-state scoring.
3. Pareto selector logic for route-candidate comparison and selection.

The work then evaluates these kernels across RTL/generic synthesis, OpenROAD/SKY130 physical design, and representative CMOS/ngspice primitive simulation.

## Summary of RTL/Yosys evidence

At the RTL and generic Yosys level, the work evaluated FDPE, SKAG, and Pareto selector variants to study kernel-level design tradeoffs.

The FDPE variants showed the tradeoff between LUT depth, interpolation, approximation behavior, and synthesized logic cost. The SKAG variants showed that replacing runtime multiplier-heavy scoring with fixed-alpha shift-add scoring can substantially reduce generic synthesized cell count for the evaluated edge-scoring kernel. The Pareto selector variants showed that route-candidate comparison and selection logic remains compact relative to the larger FDPE and SKAG kernels.

## Summary of OpenROAD physical-design evidence

The strongest VLSI evidence in this work is the OpenROAD/SKY130 physical implementation of three representative QFlow decision kernels:

| Kernel | Role | Final area | Final utilization | Flow status |
|---|---|---:|---:|---|
| SKAG-W1 | Edge-weight scoring | 6451 um^2 | 26% | RTL-to-GDS complete |
| FDPE-V3 | Fidelity-decay approximation | 22186 um^2 | 13% | RTL-to-GDS complete |
| Pareto-C0 | Route-candidate selector/comparator | 3368 um^2 | 13% | RTL-to-GDS complete |

Each selected kernel completed synthesis, floorplanning, placement, clock-tree synthesis, routing, final report generation, RC extraction, IR-drop reporting, and final GDS/DEF/SPEF generation in the open-source SKY130/OpenROAD flow.

This result moves the work beyond simulation-only evaluation and provides reproducible physical-design feasibility evidence for the major QFlow decision-kernel classes.

## Summary of CMOS/ngspice primitive evidence

To complement the standard-cell physical-design evidence, the work also evaluated representative CMOS primitives from the Pareto-C0 selector/comparator path using ngspice.

The completed primitives are:

| Primitive | QFlow connection | Main result |
|---|---|---|
| 2:1 transmission-gate mux | Selector behavior | Average delay of 26.64 ps at 20 fF; load sweep from 5 fF to 50 fF |
| 1-bit XNOR/equality primitive | Comparator/equality behavior | Average delay of 26.64 ps at 20 fF |

The mux load sweep showed delay increasing from 10.38 ps at 5 fF to 54.31 ps at 50 fF, while the estimated output-load switching energy increased from 8.10 fJ to 81.00 fJ under a 1.8 V supply.

These ngspice results provide transistor-level primitive support for selector and comparator behavior, while remaining distinct from full-chip SPICE or fabricated-silicon measurement.

## Main contribution restatement

The main contribution of this work is a claim-controlled, layered hardware evidence stack for QFlow decision kernels.

The contribution includes:

1. A hardware-oriented QFlow architecture decomposed into FDPE, SKAG, and Pareto selector kernels.
2. RTL/generic synthesis evaluation of kernel variants and optimization tradeoffs.
3. OpenROAD/SKY130 RTL-to-GDS physical implementation of SKAG-W1, FDPE-V3, and Pareto-C0.
4. Representative CMOS/ngspice primitive analysis for mux/selector and XNOR/comparator behavior.
5. A clear evidence boundary separating simulation, physical-design feasibility, primitive-level transistor simulation, and future fabricated-silicon validation.

## Evidence boundary

The conclusion should clearly restate what this work does not claim.

This work does not report:

- fabricated ASIC silicon,
- commercial signoff,
- full-chip tapeout,
- measured silicon timing,
- measured silicon power,
- full-chip transistor-level simulation,
- calibrated SKY130 extracted-layout SPICE simulation,
- or completed FPGA/cloud board validation.

Instead, the work reports a reproducible hardware feasibility stack built from RTL/generic synthesis, open-source SKY130/OpenROAD physical design, and representative ngspice primitive simulation.

## Future work

Future work should proceed in six directions.

### 1. FPGA/cloud validation

The FPGA/cloud validation path should be completed to connect the current RTL and physical-design evidence with real hardware execution. This includes finishing the cloud-FPGA deployment path, collecting latency/resource measurements, and comparing hardware execution against the existing reference model and software baselines.

### 2. Larger integrated OpenROAD subsystem

The current OpenROAD evidence implements individual decision kernels. A future step is to integrate FDPE, SKAG, and Pareto selector logic into a larger combined subsystem and evaluate the physical-design behavior of the integrated datapath.

### 3. Calibrated PDK-level transistor simulation

The ngspice primitive experiments currently use first-order Level-1 MOS models. Future work should repeat selected primitive experiments using calibrated SKY130 transistor models and, if possible, extracted parasitics from layout-level primitive cells.

### 4. Memory macro exploration for FDPE

The FDPE kernel relies on lookup-table structures. Future work can explore memory-macro or ROM-style implementations for lookup-heavy fidelity approximation, including OpenRAM or standard-cell ROM alternatives.

### 5. Post-layout power and timing refinement

The current physical-design results demonstrate feasibility and artifact generation. Future work should improve post-layout timing, power, and physical verification analysis using more detailed constraints, activity factors, and signoff-oriented checks.

### 6. Tapeout-oriented path

If resources become available, the long-term goal is to move from open-source physical-design feasibility toward a tapeout-oriented evaluation of selected QFlow kernels or a small integrated QFlow accelerator tile.

## Final paper-ready conclusion paragraph

This work presented QFlow as a layered hardware feasibility stack for quantum-inspired network decision acceleration. By decomposing the decision process into FDPE, SKAG, and Pareto selector kernels, the design was evaluated through RTL/generic synthesis, OpenROAD/SKY130 physical design, and representative CMOS/ngspice primitive simulation. Three selected kernels, SKAG-W1, FDPE-V3, and Pareto-C0, completed an RTL-to-GDS OpenROAD flow and produced final GDS/DEF/SPEF artifacts. In addition, mux and XNOR/equality primitives from the Pareto-C0 route-selection path were evaluated with ngspice to provide circuit-level support for selector and comparator behavior. These results demonstrate a reproducible hardware implementation path from decision-kernel design to physical-design feasibility and primitive-level CMOS analysis, while remaining distinct from fabricated-silicon measurement or commercial signoff.
