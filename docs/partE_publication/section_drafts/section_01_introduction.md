# Section Draft: Introduction

## Section purpose

This section introduces the motivation, problem, research gap, proposed QFlow approach, and main contributions of the paper.

The introduction should position QFlow as a layered hardware feasibility study for quantum-inspired network decision acceleration. It should not overclaim fabricated silicon or full commercial ASIC signoff.

## Motivation

Quantum-inspired and QKD-style network control requires repeated decisions over link quality, stored-key condition, route availability, and candidate path selection. These decisions may involve fidelity decay, key availability, QBER-related penalties, load or arrival state, and multi-metric route comparison.

In a software-only control path, repeated evaluation of these metrics can become a bottleneck, especially when network state changes frequently or many route candidates must be evaluated. A hardware-oriented decision pipeline can reduce decision latency and provide a path toward FPGA or ASIC acceleration.

## Problem statement

The central problem addressed in this work is how to map a quantum-inspired network decision process into hardware-relevant kernels and evaluate those kernels across multiple hardware evidence layers.

The challenge is not only to write RTL. A strong hardware research contribution should also show how the design behaves under synthesis, how selected kernels can move toward physical implementation, and how representative low-level primitives behave at transistor level.

## Research gap

Many network-control and quantum-inspired routing studies focus on algorithmic or software-level evaluation. However, a practical hardware-oriented path requires evidence beyond algorithmic simulation. It needs a bridge from decision logic to RTL, synthesis, physical design, and representative circuit-level behavior.

This work addresses that gap by presenting QFlow as a layered evidence stack rather than only a software routing method or only an isolated RTL block.

## Proposed approach

QFlow decomposes the network decision process into three hardware-oriented kernel families:

1. FDPE: Fidelity Decay Prediction Engine for stored-key fidelity update.
2. SKAG: State-Keeping Adjacency Graph / edge-weight scoring kernel for link-state scoring.
3. Pareto selector: route-candidate selector/comparator for final candidate selection.

The paper evaluates these kernels through a layered hardware evidence stack:

1. RTL and generic Yosys synthesis evaluation.
2. SKY130/OpenROAD physical-design implementation of selected kernels.
3. Representative CMOS/ngspice primitive analysis for selector and comparator behavior.

## Main contribution

The main contribution of this work is not a fabricated chip. Instead, the contribution is a reproducible hardware feasibility stack for QFlow decision kernels.

The work shows how the QFlow decision pipeline can be decomposed, optimized, synthesized, physically implemented at the kernel level, and supported by representative transistor-level primitive analysis.

## Specific contributions

This paper makes the following contributions:

1. It proposes a hardware-oriented QFlow decision pipeline organized around FDPE, SKAG, and Pareto selector kernels.
2. It evaluates FDPE LUT/interpolation variants to study fidelity-decay approximation area-accuracy tradeoffs.
3. It optimizes SKAG edge scoring by replacing multiplier-heavy runtime weighting with fixed-alpha shift-add scoring.
4. It evaluates Pareto selector variants for compact route-candidate comparison and selection.
5. It implements three representative QFlow kernels through the SKY130/OpenROAD RTL-to-GDS flow: SKAG-W1, FDPE-V3, and Pareto-C0.
6. It provides representative CMOS/ngspice primitive evidence for Pareto-C0 selector/comparator behavior using a 2:1 transmission-gate mux and a 1-bit XNOR/equality primitive.
7. It defines a claim-controlled evidence hierarchy that separates RTL synthesis, physical-design feasibility, and transistor-level primitive simulation from fabricated-silicon measurement.

## Evidence summary

The completed OpenROAD physical-design evidence includes:

| Kernel | Role | Physical-design status |
|---|---|---|
| SKAG-W1 | Edge-weight scoring | RTL-to-GDS complete |
| FDPE-V3 | Fidelity-decay approximation | RTL-to-GDS complete |
| Pareto-C0 | Route-candidate selector/comparator | RTL-to-GDS complete |

The completed CMOS/ngspice primitive evidence includes:

| Primitive | QFlow connection | Evidence |
|---|---|---|
| 2:1 transmission-gate mux | Selector behavior | single-load simulation and load sweep |
| 1-bit XNOR/equality primitive | Comparator/equality behavior | single-load transient simulation |

## Safe positioning

This work should be positioned as a hardware feasibility and implementation-evidence study.

The paper should not claim:

- fabricated ASIC silicon,
- commercial signoff,
- full-chip transistor-level simulation,
- full-chip tapeout,
- measured silicon power,
- or completed FPGA/cloud board validation.

The paper can safely claim:

QFlow is evaluated through a layered hardware evidence stack that includes RTL/generic synthesis, open-source SKY130/OpenROAD physical design of three representative decision kernels, and representative ngspice-level CMOS primitive analysis for route-selection logic.

## Suggested final introduction paragraph

This paper presents QFlow, a layered hardware evidence stack for quantum-inspired network decision acceleration. QFlow decomposes the decision process into fidelity-decay prediction, edge-weight scoring, and Pareto-style route-candidate selection kernels. The work evaluates these kernels across RTL/generic synthesis, open-source SKY130/OpenROAD physical design, and representative CMOS/ngspice primitive simulation. Three selected kernels, SKAG-W1, FDPE-V3, and Pareto-C0, complete an RTL-to-GDS OpenROAD flow, while mux and XNOR/equality primitives provide transistor-level support for selector/comparator behavior in the route-selection path. The result is a reproducible hardware feasibility study that bridges algorithmic decision logic, physical design, and circuit-level primitive evidence while remaining distinct from fabricated-silicon measurement or commercial ASIC signoff.
