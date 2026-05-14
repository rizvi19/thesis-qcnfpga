# QFlow LaTeX Assembly Plan

## Purpose

This document maps the completed Markdown section drafts, figures, tables, and evidence files into a final LaTeX manuscript structure.

The goal is to prepare the QFlow VLSI/CMOS extension for paper/thesis writing without losing claim control.

## Target manuscript structure

| Manuscript part | Source draft | Notes |
|---|---|---|
| Abstract | To write after full assembly | Should summarize layered hardware evidence stack |
| 1. Introduction | `section_01_introduction.md` | Compress into 4–6 paragraphs |
| 2. Background and Related Work | `section_02_background_related_work.md` | Needs real citations |
| 3. QFlow Architecture | `section_03_qflow_architecture.md` | Include architecture figure |
| 4. Kernel Optimization Methods | `section_04_kernel_optimization_methods.md` | Explain FDPE/SKAG/Pareto variants |
| 5. RTL/Yosys Kernel Evaluation | `section_05_rtl_yosys_kernel_evaluation.md` | Include generic synthesis tables/plots |
| 6. OpenROAD/SKY130 Physical Design | `section_06_openroad_physical_design.md` | Include physical summary and layout figures |
| 7. CMOS/ngspice Primitive Study | `section_07_cmos_ngspice_primitive_study.md` | Include mux/XNOR primitive results |
| 8. Discussion and Limitations | `section_08_discussion_limitations.md` | Must preserve safe boundaries |
| 9. Conclusion and Future Work | `section_09_conclusion_future_work.md` | Summarize contributions and future work |

## Recommended figure placement

| Figure | Placement | Source | Status |
|---|---|---|---|
| Fig. 1 QFlow architecture and kernel mapping | Section 3 | manual figure needed | pending |
| Fig. 2 FDPE-SKAG-Pareto decision chain | Section 3 | manual figure needed | pending |
| Fig. 3 SKAG-W0 vs SKAG-W1 optimization | Section 4 | manual figure needed | pending |
| Fig. 4 FDPE area-accuracy tradeoff | Section 5 | `results/partC_vlsi/figures/fdpe_area_accuracy_tradeoff.png` | available |
| Fig. 5 Kernel area comparison | Section 5 | `results/partC_vlsi/figures/kernel_area_comparison.png` | available |
| Fig. 6 OpenROAD flow | Section 6 | manual figure needed | pending |
| Fig. 7 OpenROAD final layouts | Section 6 | SKAG/FDPE/Pareto final layout images | available |
| Fig. 8 TG mux waveform | Section 7 | `results/partD_cmos/pareto_cmp_primitive/tg_mux_2to1_waveform.png` | available |
| Fig. 9 TG mux load sweep | Section 7 | delay and energy plots | available |
| Fig. 10 XNOR/equality waveform | Section 7 | `results/partD_cmos/pareto_cmp_primitive/xnor_eq1/xnor_eq1_waveform.png` | available |

## Recommended table placement

| Table | Placement | Source | Status |
|---|---|---|---|
| Table 1 FDPE variants | Section 5 | FDPE Yosys/error CSVs | available |
| Table 2 SKAG W0/W1 comparison | Section 5 | `asic/skag_weight_kernel/results/skag_yosys_comparison.csv` | available |
| Table 3 Pareto selector comparison | Section 5 | `asic/pareto_cmp_kernel/results/pareto_yosys_comparison.csv` | available |
| Table 4 Combined kernel evidence | Section 5 | `results/partC_vlsi/partC_kernel_evidence_summary.csv` | available |
| Table 5 OpenROAD physical summary | Section 6 | `results/partC_vlsi/openroad_physical_summary.csv` | available |
| Table 6 CMOS mux load sweep | Section 7 | `results/partD_cmos/pareto_cmp_primitive/load_sweep/tg_mux_load_sweep.csv` | available |
| Table 7 CMOS primitive summary | Section 7 | mux and XNOR summary CSVs | available |
| Table 8 Claim-evidence boundary | Section 8 or Appendix | `qflow_claim_evidence_matrix.md` | available |

## Manual figures still required

1. QFlow architecture and VLSI kernel mapping.
2. FDPE -> SKAG -> Pareto decision-kernel chain.
3. SKAG-W0 vs SKAG-W1 optimization diagram.
4. RTL-to-GDS OpenROAD flow diagram.

## Citation work remaining

Real citations must be inserted for:

1. QKD and quantum-network routing.
2. Fidelity decay / quantum link quality / QBER.
3. FPGA or hardware acceleration for network decision/routing workloads.
4. ASIC/VLSI or graph/routing accelerator literature.
5. OpenROAD and SKY130 open-source physical-design flow.
6. SPICE/ngspice or CMOS primitive analysis background.

## Claim-control checklist

Before final manuscript submission, every claim must be checked against:

`docs/partE_publication/qflow_claim_evidence_matrix.md`

The manuscript may claim:

- RTL/generic synthesis evidence.
- OpenROAD/SKY130 physical-design feasibility.
- final GDS/DEF/SPEF generation for selected kernels.
- representative ngspice primitive evidence.

The manuscript must not claim:

- fabricated ASIC silicon.
- full-chip tapeout.
- commercial signoff.
- measured silicon timing or power.
- full-chip transistor-level simulation.
- completed FPGA/cloud validation unless Part B is finished later.

## Recommended assembly order

1. Create manual conceptual figures.
2. Convert Section 03 to Section 08 into LaTeX first.
3. Insert tables from CSV sources.
4. Insert generated result figures.
5. Draft abstract after all sections are assembled.
6. Insert real citations.
7. Compress and polish for target journal/page limit.
8. Run final claim-evidence check.

## Immediate next step

Create the first manual figure: QFlow architecture and VLSI kernel mapping.
