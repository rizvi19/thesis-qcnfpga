# Section Draft: QFlow Architecture

## Section purpose

This section describes the QFlow hardware architecture and explains how the main decision kernels are organized into a layered network-decision pipeline.

The purpose of this section is to make the reader understand the complete datapath before the paper presents the RTL/Yosys, OpenROAD, and CMOS/ngspice results.

## Architectural motivation

Quantum-inspired or QKD-style network control requires repeated decisions about route quality, stored-key condition, link reliability, and candidate selection. A software-only decision path can become slow when the network state changes frequently or when many candidate routes must be evaluated.

QFlow addresses this by organizing the decision logic into hardware-oriented kernels. Each kernel performs a specific part of the network-decision process, allowing the overall system to be mapped into RTL, FPGA, and ASIC/VLSI implementation paths.

## Top-level QFlow pipeline

The QFlow decision pipeline is organized around three main kernel families:

1. FDPE: Fidelity Decay Prediction Engine.
2. SKAG: State-Keeping Adjacency Graph / edge-weight scoring kernel.
3. Pareto selector: route-candidate selector/comparator.

The high-level decision chain is:

```text
network/request state -> FDPE fidelity update -> SKAG edge scoring -> Pareto route selection -> selected route decision
```

## Input information

QFlow consumes network-state and request-related information. Important inputs include:

- initial or stored-key fidelity,
- elapsed storage or decay-related index,
- key availability or key count,
- link arrival/load condition,
- QBER or quality-related penalty,
- route candidate metrics,
- hop count or path-length-related tie-break information.

These inputs are not treated as isolated software variables. Instead, they are organized as hardware-visible signals that feed the decision kernels.

## FDPE kernel

FDPE estimates stored-key fidelity degradation. In the QFlow architecture, FDPE provides an updated fidelity value that can be used by the downstream scoring and route-selection logic.

The FDPE kernel is implemented using lookup-table-based exponential approximation. Different FDPE variants trade off LUT depth, interpolation cost, and approximation error.

Architectural role:

- Input: initial fidelity and decay index.
- Output: updated stored-key fidelity estimate.
- Function: approximate exponential fidelity decay in hardware-friendly form.

## SKAG kernel

SKAG maintains and evaluates edge/link state for the network-decision process. It combines multiple link-quality terms into an edge-weight or score representation.

The evaluated SKAG variants compare a baseline weighted-score implementation against an optimized fixed-alpha shift-add implementation. The optimized W1 version reduces multiplier-heavy runtime weighting and makes the scoring logic more hardware-friendly.

Architectural role:

- Input: fidelity estimate, key availability, arrival/load state, QBER or quality penalty.
- Output: edge score or weighted penalty score.
- Function: convert link-state metrics into hardware-comparable route-scoring values.

## Pareto selector kernel

The Pareto selector compares route candidates and selects the preferred candidate based on score and tie-break metrics. In the evaluated architecture, Pareto-C0 acts as a full comparator/selector baseline for route-candidate selection.

Architectural role:

- Input: candidate route metrics and tie-break fields.
- Output: selected candidate decision, tie indication, and dominance/selection signals.
- Function: choose between competing route candidates using comparator and selector logic.

## Hardware evidence mapping

The architecture is evaluated through a layered hardware evidence stack:

| Architecture block | RTL/Yosys evidence | OpenROAD physical evidence | CMOS/ngspice primitive support |
|---|---|---|---|
| FDPE fidelity update | FDPE V0/V1/V2/V3 variants | FDPE-V3 RTL-to-GDS | Not directly modeled at transistor level in this phase |
| SKAG edge scoring | SKAG-W0/W1 variants | SKAG-W1 RTL-to-GDS | Not directly modeled at transistor level in this phase |
| Pareto route selector | Pareto-C0/C1 variants | Pareto-C0 RTL-to-GDS | TG mux and XNOR/equality primitives |

## Why these kernels were selected for physical design

The physical-design stage focuses on representative kernels that cover the main QFlow decision path:

- FDPE-V3 was selected to represent the lookup/interpolation fidelity-decay path.
- SKAG-W1 was selected to represent the optimized edge-scoring path.
- Pareto-C0 was selected to represent full route-candidate selection and comparison.

This selection gives coverage across approximation, scoring, and selection logic instead of only implementing one isolated block.

## Architecture-to-results connection

The rest of the paper follows the architecture layers:

1. RTL/Yosys evaluation compares kernel variants.
2. OpenROAD physical design implements representative selected kernels.
3. CMOS/ngspice primitive study examines selector/comparator primitives connected to Pareto-C0.

This organization creates a clear path from architectural design to hardware evidence.

## Figure references

Recommended figures for this section:

- QFlow architecture and VLSI kernel mapping.
- FDPE -> SKAG -> Pareto decision-kernel chain.
- Hardware evidence stack diagram.

## Safe wording

The correct claim is:

QFlow organizes quantum-inspired network decision logic into hardware-oriented kernels for fidelity update, edge scoring, and route-candidate selection.

Do not claim:

- complete fabricated QFlow chip,
- full-system commercial signoff,
- full-chip transistor-level simulation,
- or completed FPGA/cloud validation from this section alone.

## Paper-ready paragraph

QFlow is organized as a hardware-oriented decision pipeline for quantum-inspired network control. The architecture decomposes the decision process into three kernel families: FDPE for stored-key fidelity decay estimation, SKAG for edge-weight scoring from link-state metrics, and a Pareto selector for route-candidate comparison and final selection. This decomposition allows each decision function to be evaluated as an RTL kernel, optimized through generic synthesis experiments, and mapped into physical-design or circuit-level evidence. In the implemented evidence stack, FDPE-V3, SKAG-W1, and Pareto-C0 represent the fidelity-update, edge-scoring, and route-selection stages of the architecture.
