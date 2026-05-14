# Section Draft: Background and Related Work

## Section purpose

This section provides the technical background needed to understand QFlow and positions the work relative to network decision acceleration, quantum-inspired network control, FPGA/ASIC design, open-source physical design, and CMOS-level primitive analysis.

This draft is citation-neutral. Real citations should be inserted later from the literature review and related-work matrix.

## Quantum-inspired network decision context

Quantum-inspired and QKD-style network control requires decisions that depend on changing link and path conditions. A routing decision may need to consider stored-key quality, link reliability, candidate path cost, available key material, and quality degradation over time.

In this setting, the routing or control plane is not only choosing a shortest path. It may need to evaluate whether a path has sufficient key availability, whether the stored key remains usable, whether link quality is acceptable, and whether one candidate route dominates another under multiple metrics.

QFlow is motivated by this type of repeated multi-metric decision process.

## Fidelity decay and stored-key quality

Stored quantum-key or quantum-inspired link quality can degrade over time. In QFlow, this behavior is represented through a fidelity-decay prediction kernel. The goal is not to simulate a full quantum device, but to provide a hardware-friendly approximation of the quality degradation term used by the network decision logic.

The FDPE kernel approximates this decay using lookup-table-based exponential approximation. This allows the fidelity update to be represented as digital hardware rather than as an expensive runtime mathematical function.

## QBER and link-quality penalties

QBER, or quantum bit error rate, is commonly used as an indicator of link quality in quantum communication contexts. A higher error rate generally indicates lower link reliability. In a routing decision, QBER-like quality terms can be represented as penalties that affect edge or route preference.

In QFlow, QBER-related penalties are combined with other link-state metrics inside the edge-scoring process.

## Multi-metric route-candidate selection

Network routing decisions often involve more than one metric. A candidate route may have better fidelity but worse key availability, or a lower score but worse hop count. Because of this, the selection logic needs a comparator/selector mechanism that can compare route candidates using score and tie-break fields.

The Pareto selector kernel represents this route-candidate comparison stage. It is designed to compare candidates and select the preferred route according to the chosen scoring and tie-break policy.

## Hardware acceleration motivation

Software-based control logic is flexible, but repeated route-state evaluation can become expensive when decisions are frequent or when many candidate paths are evaluated. Hardware acceleration is attractive because recurring decision operations can be represented as dedicated datapaths.

For QFlow, the key hardware opportunity is to decompose the decision process into kernels:

- fidelity update,
- edge scoring,
- candidate comparison,
- and candidate selection.

This decomposition makes the design suitable for RTL implementation, FPGA experimentation, and ASIC/VLSI-style physical-design exploration.

## FPGA-to-ASIC evidence path

A hardware research project is stronger when it does not stop at algorithmic simulation. A layered hardware evidence path can include:

1. reference model or mathematical validation,
2. RTL implementation and simulation,
3. generic synthesis evaluation,
4. FPGA or cloud-FPGA validation,
5. standard-cell physical design,
6. and selected transistor-level primitive analysis.

QFlow follows this layered evidence approach. The current VLSI/CMOS extension focuses especially on generic Yosys synthesis, SKY130/OpenROAD physical design, and representative ngspice primitive simulation.

## Open-source physical design and OpenROAD

Open-source EDA tools allow researchers to move beyond RTL and generic synthesis toward reproducible physical-design evidence. OpenROAD-flow-scripts and the SKY130 platform make it possible to generate physical-design artifacts such as GDS, DEF, SPEF, routed layouts, and physical reports.

In QFlow, OpenROAD is used to test whether selected kernels can be taken through a complete RTL-to-GDS style flow. This does not prove commercial signoff or fabricated-silicon behavior, but it provides stronger implementation evidence than simulation-only evaluation.

## CMOS/ngspice primitive analysis

Standard-cell physical design shows that the RTL can be mapped into a physical implementation flow, but it does not directly explain transistor-level primitive behavior. For that reason, QFlow also includes a small CMOS/ngspice primitive study.

The selected primitives are connected to the Pareto-C0 selector/comparator path:

- a 2:1 transmission-gate mux for selector behavior,
- and a 1-bit XNOR/equality primitive for comparator/equality behavior.

These simulations are representative primitive-level studies. They are not full-chip transistor-level simulations and should not be interpreted as fabricated-silicon measurements.

## Positioning of this work

The main positioning of QFlow is as a layered hardware feasibility study. It is not only a routing algorithm, not only an FPGA project, and not a fabricated ASIC. Instead, it connects network decision logic to multiple hardware evidence layers.

The work is positioned around three questions:

1. Can the QFlow decision process be decomposed into hardware-oriented kernels?
2. Can the kernels be optimized and evaluated through RTL/generic synthesis?
3. Can representative kernels and primitives be pushed further into physical-design and transistor-level evidence?

## Related-work categories to cite later

Real citations should be inserted under these categories:

1. Quantum key distribution and quantum-network routing.
2. Fidelity decay, QBER, and quantum link-quality metrics.
3. FPGA acceleration for routing, control-plane, or network-decision workloads.
4. ASIC/VLSI acceleration of graph, routing, or optimization kernels.
5. OpenROAD/SKY130 open-source physical-design research.
6. CMOS primitive analysis using SPICE/ngspice.

## Safe wording

The correct framing is:

QFlow builds a hardware evidence path for quantum-inspired network decision kernels using RTL/generic synthesis, SKY130/OpenROAD physical design, and representative ngspice primitive simulation.

Do not claim:

- complete quantum-device simulation,
- fabricated ASIC implementation,
- commercial signoff,
- full-chip transistor-level simulation,
- or completed cloud-FPGA validation from this section alone.

## Paper-ready paragraph

Quantum-inspired and QKD-style network control requires repeated decisions over link quality, key availability, fidelity degradation, and candidate route preference. These decisions naturally involve recurring operations such as fidelity update, edge scoring, and multi-metric candidate comparison. QFlow targets this decision process by decomposing it into hardware-oriented kernels that can be evaluated across a layered evidence stack. The background motivation is therefore not only algorithmic routing, but also the implementation path from decision logic to RTL synthesis, open-source physical design, and representative CMOS primitive behavior. This positioning allows QFlow to bridge network-decision modeling with practical FPGA/ASIC-oriented hardware evaluation while maintaining clear boundaries between feasibility evidence and fabricated-silicon measurement.
