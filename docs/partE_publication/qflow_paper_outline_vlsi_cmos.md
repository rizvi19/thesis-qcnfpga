# QFlow VLSI/CMOS Paper Outline

## Working title

QFlow: A Layered FPGA-to-ASIC Evidence Stack for Quantum-Inspired Network Decision Acceleration

Alternative title:

QFlow: OpenROAD Physical Design and CMOS Primitive Evaluation of Quantum-Inspired Network Decision Kernels

## Core paper message

This paper presents QFlow as a layered hardware evidence stack for quantum-inspired network decision acceleration. The work combines core RTL/synthesis evidence, OpenROAD/SKY130 physical implementation of three decision kernels, and representative CMOS/ngspice primitive analysis for route-selection logic.

## Recommended paper structure

### 1. Introduction

Purpose:
- Introduce the need for fast hardware-assisted decision logic in quantum-inspired or QKD-style network control.
- Explain that software routing/control decisions can become a bottleneck.
- Present QFlow as a hardware-oriented decision pipeline.
- State the layered evidence approach: RTL, OpenROAD physical design, and CMOS primitive simulation.

Key safe claim:
QFlow is evaluated through a layered hardware evidence stack, not through fabricated silicon.

### 2. Background and Motivation

Purpose:
- Explain QKD/quantum-inspired networking context in simple terms.
- Explain why fidelity decay, key availability, QBER, and route selection matter.
- Explain why FPGA/ASIC/VLSI acceleration is relevant.

### 3. QFlow Architecture

Purpose:
- Present the main QFlow pipeline.
- Show FDPE, SKAG, and Pareto selector as decision kernels.
- Explain input/output behavior of each kernel.

Figures:
- Fig. 1: QFlow architecture and VLSI kernel mapping.
- Fig. 2: FDPE -> SKAG -> Pareto decision-kernel chain.

### 4. Kernel Optimization Methods

Purpose:
- Explain FDPE LUT/interpolation variants.
- Explain SKAG-W0 vs SKAG-W1 multiplier-removal idea.
- Explain Pareto-C0/C1 selector comparison.

Figures:
- Fig. 3: SKAG-W0 vs SKAG-W1 optimization diagram.

Tables:
- FDPE area-accuracy variants.
- SKAG W0/W1 synthesis comparison.
- Pareto selector synthesis comparison.

### 5. RTL and Generic Synthesis Evaluation

Purpose:
- Present Yosys/generic synthesis evidence.
- Show cell-count reductions and tradeoffs.
- Keep generic synthesis separate from physical-design results.

Important result examples:
- SKAG-W1 reduces generic Yosys cell count compared with SKAG-W0.
- FDPE variants show area-accuracy tradeoff.
- Pareto-C0/C1 selector variants show compact route-selection logic.

### 6. OpenROAD/SKY130 Physical Design

Purpose:
- Present RTL-to-GDS flow.
- Report physical implementation of SKAG-W1, FDPE-V3, and Pareto-C0.
- Show final area/utilization/artifacts.

Figures:
- Fig. 4: RTL-to-GDS OpenROAD flow.
- OpenROAD layout/routing/IR images for SKAG-W1, FDPE-V3, Pareto-C0.

Main table:
- OpenROAD physical-design summary table.

Safe wording:
The three kernels completed synthesis, floorplan, placement, CTS, routing, RC extraction, IR-drop reporting, and final GDS/DEF/SPEF generation in the open-source SKY130/OpenROAD flow.

Do not claim:
- fabricated silicon
- tapeout
- commercial signoff
- measured silicon power/timing

### 7. CMOS/ngspice Primitive Study

Purpose:
- Complement standard-cell OpenROAD evidence with transistor-level primitive analysis.
- Present 2:1 transmission-gate mux as a representative selector primitive from the Pareto-C0 route-selection path.
- Show single-run waveform and load sweep.

Figures:
- TG mux transient waveform.
- Delay vs load plot.
- Energy vs load plot.

Table:
- TG mux load sweep table.

Safe wording:
A representative 2:1 transmission-gate mux was evaluated with ngspice using a first-order MOS model. This is primitive-level evidence, not calibrated SKY130 signoff.

### 8. Discussion

Purpose:
- Explain what the evidence proves.
- Explain why the three-kernel OpenROAD result is stronger than simulation-only evidence.
- Discuss area/accuracy tradeoffs.
- Discuss why Part D is representative primitive evidence, not full-chip SPICE.

### 9. Limitations

Must include:
- No fabricated silicon measurement.
- No commercial signoff.
- OpenROAD/SKY130 results are physical-design feasibility evidence.
- ngspice primitive uses simple Level-1 MOS model.
- FPGA/cloud board validation is ongoing separately.
- Full-system tapeout is future work.

### 10. Conclusion

Purpose:
- Summarize layered evidence stack.
- Highlight three RTL-to-GDS decision kernels.
- Highlight representative CMOS primitive load-sweep evidence.
- State future work: FPGA/cloud completion, calibrated PDK-level transistor simulation, larger system integration, and possible ASIC tapeout path.

## Main contributions

1. A hardware-oriented QFlow decision pipeline with FDPE, SKAG, and Pareto selector kernels.
2. Kernel-level optimization evidence, including SKAG multiplier removal and FDPE LUT/interpolation tradeoff.
3. Open-source SKY130/OpenROAD RTL-to-GDS implementation of three major QFlow kernels.
4. Representative CMOS/ngspice primitive analysis for Pareto selector mux behavior.
5. A claim-controlled layered hardware evidence stack separating RTL, physical design, and transistor-level primitive evidence.

## Paper evidence hierarchy

Level 1: Algorithm/math/reference model evidence.
Level 2: RTL simulation and generic synthesis evidence.
Level 3: OpenROAD/SKY130 physical-design evidence.
Level 4: Representative CMOS/ngspice primitive evidence.
Level 5: Future fabricated-silicon or board measurement evidence.

## Current best top-level claim

QFlow demonstrates a layered hardware feasibility path for quantum-inspired network decision acceleration by combining RTL/synthesis evidence, OpenROAD/SKY130 physical design of three decision-kernel blocks, and ngspice-level CMOS primitive analysis for route-selection logic.
