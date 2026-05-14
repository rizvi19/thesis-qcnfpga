# QFlow Paper Figure and Table Checklist

## Purpose

This document lists the planned paper/thesis figures and tables for the QFlow post-Part-A VLSI/CMOS extension. The goal is to convert the generated evidence into a clean publication package.

## Planned figures

| ID | Figure title | Source | Status | Purpose |
|---|---|---|---|---|
| Fig. 1 | QFlow architecture and VLSI kernel mapping | Manual block diagram / TikZ / draw.io | To create | Shows how FDPE, SKAG, and Pareto kernels fit inside QFlow |
| Fig. 2 | QFlow decision-kernel chain | Manual block diagram | To create | Shows FDPE fidelity decay -> SKAG edge scoring -> Pareto route selection |
| Fig. 3 | SKAG-W0 vs SKAG-W1 optimization | Manual datapath diagram | To create | Explains multiplier removal and shift-add scoring |
| Fig. 4 | OpenROAD RTL-to-GDS flow | Manual flow diagram | To create | Shows synthesis, floorplan, placement, CTS, routing, finish |
| Fig. 5 | SKAG-W1 final physical layout | `results/partC_vlsi/figures/skag_w1_final_all.webp` and routing/IR images | Available | Shows physical implementation evidence for edge scoring |
| Fig. 6 | FDPE-V3 final physical layout | `results/partC_vlsi/figures/fdpe_v3_final_all.webp` and routing/IR images | Available | Shows physical implementation evidence for fidelity approximation |
| Fig. 7 | Pareto-C0 final physical layout | `results/partC_vlsi/figures/pareto_c0_final_all.webp` and routing/IR images | Available | Shows physical implementation evidence for route selection |
| Fig. 8 | Part C generic-cell area comparison | `results/partC_vlsi/figures/kernel_area_comparison.png` | Available | Compares FDPE, SKAG, and Pareto kernel cell counts |
| Fig. 9 | FDPE area-accuracy tradeoff | `results/partC_vlsi/figures/fdpe_area_accuracy_tradeoff.png` | Available | Shows LUT/interpolation area-accuracy tradeoff |
| Fig. 10 | CMOS TG mux waveform | `results/partD_cmos/pareto_cmp_primitive/tg_mux_2to1_waveform.png` | Available | Shows transistor-level mux response |
| Fig. 11 | CMOS TG mux delay vs load | `results/partD_cmos/pareto_cmp_primitive/load_sweep/tg_mux_delay_vs_load.png` | Available | Shows delay scaling with capacitance |
| Fig. 12 | CMOS TG mux energy vs load | `results/partD_cmos/pareto_cmp_primitive/load_sweep/tg_mux_energy_vs_load.png` | Available | Shows 0.5CV^2 energy scaling with capacitance |

## Planned tables

| ID | Table title | Source | Status | Purpose |
|---|---|---|---|---|
| Table 1 | FDPE kernel area-accuracy variants | `asic/fdpe_kernel/results/fdpe_yosys_comparison.csv` and error CSVs | Available | Summarizes FDPE V0/V1/V2/V3 tradeoff |
| Table 2 | SKAG generic synthesis comparison | `asic/skag_weight_kernel/results/skag_yosys_comparison.csv` | Available | Shows SKAG-W0 to SKAG-W1 area reduction |
| Table 3 | Pareto selector synthesis comparison | `asic/pareto_cmp_kernel/results/pareto_yosys_comparison.csv` | Available | Shows Pareto-C0/C1 selector cost comparison |
| Table 4 | Combined Part C kernel evidence | `results/partC_vlsi/partC_kernel_evidence_summary.csv` | Available | Summarizes all generic kernel variants |
| Table 5 | OpenROAD physical-design summary | `results/partC_vlsi/openroad_physical_summary.csv` | Available | Shows SKAG-W1, FDPE-V3, Pareto-C0 final area/utilization/artifacts |
| Table 6 | CMOS TG mux single-load summary | `results/partD_cmos/pareto_cmp_primitive/tg_mux_2to1_summary.csv` | Available | Summarizes 20 fF transistor-level mux result |
| Table 7 | CMOS TG mux load sweep | `results/partD_cmos/pareto_cmp_primitive/load_sweep/tg_mux_load_sweep.csv` | Available | Shows delay and energy scaling from 5 fF to 50 fF |
| Table 8 | Claim-evidence boundary table | `docs/partE_publication/qflow_claim_evidence_matrix.md` | Available | Prevents overclaiming and links claims to evidence |

## Recommended main paper figure set

For the main paper, use a concise figure set:

1. QFlow architecture and kernel mapping
2. SKAG-W0 vs SKAG-W1 optimization
3. OpenROAD physical implementation views for SKAG-W1, FDPE-V3, and Pareto-C0
4. Kernel area comparison
5. FDPE area-accuracy tradeoff
6. CMOS TG mux load-sweep result

## Recommended main paper table set

For the main paper, use:

1. Combined Part C kernel evidence table
2. OpenROAD physical-design summary table
3. CMOS TG mux load-sweep table
4. Claim/evidence/limitation boundary table

## Remaining figure work

The remaining manual figures are:

- QFlow architecture and VLSI kernel mapping
- FDPE -> SKAG -> Pareto decision-kernel chain
- SKAG-W0 vs SKAG-W1 optimization diagram
- RTL-to-GDS OpenROAD flow diagram

These should be created as clean vector-style diagrams for thesis/paper use.
