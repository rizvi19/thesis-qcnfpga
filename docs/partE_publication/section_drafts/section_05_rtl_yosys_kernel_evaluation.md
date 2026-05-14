# Section Draft: RTL and Generic Yosys Kernel Evaluation

## Section purpose

This section reports the RTL-level and generic Yosys synthesis evaluation of the selected QFlow decision kernels. The goal is to evaluate kernel-level area trends before moving to the OpenROAD/SKY130 physical-design flow.

The generic Yosys results are used to compare design alternatives, identify area/accuracy tradeoffs, and select representative optimized kernels for physical implementation.

## Evaluated kernel families

Three QFlow kernel families were evaluated:

1. FDPE: fidelity-decay prediction engine.
2. SKAG: state-keeping adjacency graph / edge-weight scoring kernel.
3. Pareto selector: route-candidate selector/comparator.

Together, these kernels represent the main QFlow decision pipeline:

FDPE fidelity decay -> SKAG edge scoring -> Pareto route selection.

## FDPE kernel variants

The FDPE kernel approximates stored-key fidelity decay using an exponential lookup structure. Multiple LUT/interpolation variants were evaluated to study the area-accuracy tradeoff.

The evaluated FDPE variants include:

- FDPE-V0: 256-entry LUT, floor-index lookup.
- FDPE-V1: 128-entry LUT, floor-index lookup.
- FDPE-V2: 128-entry LUT with linear interpolation.
- FDPE-V3: 64-entry LUT with linear interpolation.

The generic synthesis comparison showed that reducing LUT depth can reduce generic cell count, but interpolation increases logic cost. FDPE-V1 reduced generic cell count compared with FDPE-V0, while interpolation-based variants improved approximation behavior at higher generic logic cost.

## FDPE area-accuracy interpretation

The FDPE result should be interpreted as an area-accuracy tradeoff, not as a single universally best design.

Important interpretation:

- FDPE-V1 is smaller than FDPE-V0 but has worse approximation error.
- FDPE-V2 and FDPE-V3 use interpolation, improving approximation behavior but increasing synthesized logic.
- FDPE-V3 is selected for physical implementation because it represents a compact interpolated approximation structure and demonstrates the LUT/interpolation physical-design path.

## SKAG kernel variants

The SKAG edge-weight kernel computes route/edge scores using fidelity, key availability, arrival/load, and QBER-related terms.

Two SKAG variants were evaluated:

- SKAG-W0: baseline bucketized weighted-score model with runtime multiplier-style weighting.
- SKAG-W1: optimized fixed-alpha shift-add scoring model.

The SKAG-W1 variant replaces runtime multiplier-heavy scoring with fixed shift-add logic. This produced the strongest generic synthesis reduction among the evaluated kernels.

## SKAG result interpretation

The SKAG result supports the following safe claim:

Replacing runtime multiplier-based scoring with fixed shift-add scoring substantially reduced generic Yosys cell count for the evaluated SKAG edge-weight kernel.

This should not be overclaimed as a universal ASIC area reduction across all libraries or all possible routing-score formulations. It is a kernel-specific synthesis result under the evaluated RTL and generic Yosys setup.

## Pareto selector variants

The Pareto selector/comparator chooses between route candidates based on score and tie-break metrics.

Two Pareto selector variants were evaluated:

- Pareto-C0: full Pareto comparator with tie-break logic.
- Pareto-C1: score-first priority selector.

The Pareto selector results show that route-candidate comparison logic is compact relative to the larger FDPE and SKAG blocks. The C1 score-first variant provides modest generic cell reduction compared with C0, while C0 remains useful as the full comparator baseline.

## Combined kernel evidence

The combined generic synthesis evidence provides a kernel-level design-space view:

| Kernel family | Main design question | Main result |
|---|---|---|
| FDPE | LUT depth and interpolation tradeoff | Smaller LUTs reduce storage/logic, interpolation improves approximation but costs more logic |
| SKAG | Runtime multipliers vs fixed shift-add scoring | Fixed shift-add scoring strongly reduces generic synthesized cell count |
| Pareto selector | Full comparator vs score-first selector | Comparator/selector logic is compact; score-first selection gives modest reduction |

## Source files and generated evidence

The main result files for this section are:

- FDPE synthesis comparison: `asic/fdpe_kernel/results/fdpe_yosys_comparison.csv`
- FDPE LUT/error comparison: `asic/fdpe_kernel/results/fdpe_lut_error_modes_comparison.csv`
- SKAG synthesis comparison: `asic/skag_weight_kernel/results/skag_yosys_comparison.csv`
- Pareto synthesis comparison: `asic/pareto_cmp_kernel/results/pareto_yosys_comparison.csv`
- Combined kernel summary: `results/partC_vlsi/partC_kernel_evidence_summary.csv`
- Kernel area figure: `results/partC_vlsi/figures/kernel_area_comparison.png`
- FDPE area-accuracy figure: `results/partC_vlsi/figures/fdpe_area_accuracy_tradeoff.png`

## Safe wording

The correct claim is:

The QFlow kernels were evaluated using RTL simulation and generic Yosys synthesis to compare area and approximation tradeoffs across FDPE, SKAG, and Pareto selector variants.

Do not claim:

- fabricated silicon,
- commercial signoff,
- final post-layout ASIC area from generic Yosys only,
- universal area reduction across all libraries,
- or full-system chip implementation.

## Link to physical-design section

The generic Yosys results motivate the physical-design stage. Representative optimized kernels were then selected for SKY130/OpenROAD physical implementation:

- SKAG-W1 for edge-weight scoring.
- FDPE-V3 for interpolated fidelity-decay approximation.
- Pareto-C0 for full route-candidate selector/comparator behavior.

These selected kernels are reported in the following OpenROAD physical-design section.

## Paper-ready paragraph

Before physical implementation, the QFlow decision kernels were evaluated using RTL simulation and generic Yosys synthesis. The FDPE variants were used to study LUT-depth and interpolation tradeoffs for fidelity-decay approximation. The SKAG variants compared a multiplier-heavy baseline scoring model against a fixed-alpha shift-add implementation, showing the strongest generic synthesis reduction in the evaluated kernel set. The Pareto selector variants evaluated full comparator and score-first route-candidate selection logic, showing that the selection block remains compact relative to the larger FDPE and SKAG kernels. These generic synthesis results guided the selection of SKAG-W1, FDPE-V3, and Pareto-C0 for the subsequent SKY130/OpenROAD RTL-to-GDS physical-design evaluation.
