# QFlow Manual Figure Source Plan

## Purpose

This document defines the remaining manually drawn figures needed for the QFlow paper/thesis package.

The generated result figures already exist for OpenROAD layouts, area comparison, FDPE tradeoff, and CMOS mux sweep. The remaining figures are conceptual/vector diagrams.

## Manual figures to create

| Figure | Title | Content | Recommended tool | Output path |
|---|---|---|---|---|
| Fig. 1 | QFlow architecture and VLSI kernel mapping | Show QFlow request/network state input, FDPE, SKAG, Pareto selector, and selected route output | draw.io / TikZ | `results/partE_publication/figures/fig1_qflow_kernel_mapping.pdf` |
| Fig. 2 | FDPE-SKAG-Pareto decision-kernel chain | Show the kernel sequence: fidelity decay update -> edge scoring -> route-candidate selection | draw.io / TikZ | `results/partE_publication/figures/fig2_decision_kernel_chain.pdf` |
| Fig. 3 | SKAG-W0 vs SKAG-W1 optimization | Compare runtime multipliers in W0 against shift-add/fixed-alpha scoring in W1 | draw.io / TikZ | `results/partE_publication/figures/fig3_skag_w0_w1_optimization.pdf` |
| Fig. 4 | RTL-to-GDS OpenROAD flow | Show RTL -> synthesis -> floorplan -> placement -> CTS -> routing -> RC/IR -> final GDS/DEF/SPEF | draw.io / TikZ | `results/partE_publication/figures/fig4_openroad_flow.pdf` |

## Generated figures already available

- SKAG-W1 final layout/routing/IR images: `results/partC_vlsi/figures/skag_w1_*`
- FDPE-V3 final layout/routing/IR images: `results/partC_vlsi/figures/fdpe_v3_*`
- Pareto-C0 final layout/routing/IR images: `results/partC_vlsi/figures/pareto_c0_*`
- Kernel area comparison: `results/partC_vlsi/figures/kernel_area_comparison.png`
- FDPE area-accuracy tradeoff: `results/partC_vlsi/figures/fdpe_area_accuracy_tradeoff.png`
- CMOS TG mux waveform: `results/partD_cmos/pareto_cmp_primitive/tg_mux_2to1_waveform.png`
- CMOS delay/energy load-sweep plots: `results/partD_cmos/pareto_cmp_primitive/load_sweep/`

## Priority

Highest priority manual figure: Fig. 3 SKAG-W0 vs SKAG-W1 optimization.

Reason: this figure explains the strongest optimization result, where SKAG-W1 replaces runtime multiplier-based weighting with fixed shift-add scoring.
