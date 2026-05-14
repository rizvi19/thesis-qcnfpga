# QFlow Claim-Evidence Matrix

## Purpose

This document maps each intended QFlow paper claim to the exact evidence file and safe wording. It prevents overclaiming and separates simulation, FPGA/cloud, OpenROAD physical-design, and CMOS/ngspice primitive evidence.

## Claim-evidence table

| Claim | Evidence source | Safe wording | Do not claim |
|---|---|---|---|
| QFlow core datapath has simulation/synthesis evidence | Part A core RTL/results folders and existing thesis evidence | The QFlow core datapath was validated through RTL simulation and synthesis evidence. | Do not claim fabricated silicon. |
| SKAG-W1 reduces generic synthesis cost compared with SKAG-W0 | `asic/skag_weight_kernel/results/skag_yosys_comparison.csv` | Replacing runtime multipliers with fixed shift-add scoring reduced generic Yosys cell count in the evaluated SKAG kernel. | Do not claim universal ASIC area reduction across all libraries. |
| FDPE variants show an area-accuracy tradeoff | `asic/fdpe_kernel/results/fdpe_yosys_comparison.csv` and FDPE error CSVs | LUT depth and interpolation change the area-accuracy balance of the FDPE approximation kernel. | Do not claim exact physical accuracy for all workloads. |
| SKAG-W1 is physically implementable in open-source SKY130/OpenROAD flow | `results/partC_vlsi/openroad_skag_w1/` | SKAG-W1 completed SKY130/OpenROAD synthesis, floorplan, placement, CTS, routing, RC extraction, IR-drop reporting, and final GDS/DEF/SPEF generation. | Do not claim fabrication or commercial signoff. |
| FDPE-V3 is physically implementable in open-source SKY130/OpenROAD flow | `results/partC_vlsi/openroad_fdpe_v3/` | FDPE-V3 completed the same RTL-to-GDS OpenROAD flow and supports physical feasibility of the LUT64 interpolation FDPE kernel. | Do not claim fabricated-silicon timing or power. |
| Pareto-C0 is physically implementable in open-source SKY130/OpenROAD flow | `results/partC_vlsi/openroad_pareto_c0/` | Pareto-C0 completed the RTL-to-GDS OpenROAD flow and supports physical feasibility of the route-candidate selector/comparator. | Do not claim full-chip signoff. |
| Part C covers the main QFlow kernel chain | `results/partC_vlsi/openroad_physical_summary.csv` | The completed OpenROAD kernels cover FDPE fidelity decay, SKAG edge scoring, and Pareto route selection. | Do not claim the entire QFlow system was taped out. |
| CMOS primitive behavior was studied at transistor level | `results/partD_cmos/pareto_cmp_primitive/` | A representative 2:1 transmission-gate mux from the Pareto-C0 selector path was evaluated with ngspice using a first-order MOS model. | Do not claim calibrated SKY130 transistor-level simulation or foundry signoff. |
| Mux delay and load-switching energy scale with load | `results/partD_cmos/pareto_cmp_primitive/load_sweep/tg_mux_load_sweep.csv` | The ngspice load sweep showed increasing delay and estimated output-load switching energy as load capacitance increased from 5 fF to 50 fF. | Do not claim full-chip power from this primitive sweep. |

## Recommended top-level paper claim

The safest top-level claim is:

> QFlow is evaluated through a layered hardware evidence stack: core RTL/synthesis evidence, open-source SKY130/OpenROAD physical design of three decision-kernel blocks, and representative ngspice-level CMOS primitive analysis for route-selection logic.

## Main limitation wording

This work does not report fabricated-silicon measurement or commercial signoff. The ASIC/VLSI results are open-source PDK/OpenROAD physical-design feasibility results, and the CMOS/ngspice results are representative primitive-level simulations.
