# Part C VLSI Paper Figure Plan

## Purpose

This document lists the planned paper/thesis figures for the QFlow Part C VLSI extension.

The goal is to show the complete evidence path:

1. QFlow architecture context
2. Kernel-level optimization
3. Physical-design implementation
4. Quantitative results

## Planned figures

| Figure | Working title | Type | Source | Purpose |
|---|---|---|---|---|
| Fig. 1 | QFlow architecture and VLSI kernel mapping | Block diagram | Manual/TikZ/draw.io | Shows where FDPE, SKAG, and Pareto kernels fit inside QFlow |
| Fig. 2 | Part C kernel pipeline | Block diagram | Manual/TikZ/draw.io | Shows FDPE → SKAG → Pareto route-selection datapath |
| Fig. 3 | SKAG-W0 vs SKAG-W1 datapath optimization | Circuit/datapath diagram | Manual/TikZ/draw.io | Explains multiplier-to-shift-add optimization |
| Fig. 4 | RTL-to-GDS OpenROAD physical-design flow | Flow diagram | Manual/TikZ/draw.io | Shows synthesis, floorplan, placement, CTS, routing, finish |
| Fig. 5 | SKAG-W1 final SKY130 layout views | Physical layout figure | OpenROAD final_all/final_routing/final_ir_drop images | Demonstrates final physical-design artifacts |
| Fig. 6 | Kernel generic-cell area comparison | Bar chart | partC_kernel_evidence_summary.csv | Shows FDPE, SKAG, and Pareto area comparison |
| Fig. 7 | FDPE area-accuracy tradeoff | Bar/line chart | FDPE Yosys + error CSVs | Shows LUT/interpolation tradeoff |

## Current available OpenROAD images

The SKAG-W1 OpenROAD run generated the following images:

- results/partC_vlsi/openroad_skag_w1/reports/final_all.webp
- results/partC_vlsi/openroad_skag_w1/reports/final_clocks.webp
- results/partC_vlsi/openroad_skag_w1/reports/final_ir_drop.webp
- results/partC_vlsi/openroad_skag_w1/reports/final_placement.webp
- results/partC_vlsi/openroad_skag_w1/reports/final_routing.webp

Recommended paper usage:

- Use final_all.webp as the main layout view.
- Use final_routing.webp as the routing view.
- Use final_ir_drop.webp only if discussing IR-drop.
- Keep final_clocks.webp and final_placement.webp for thesis or supplementary evidence.

## Figures still to generate

- SKAG-W0 vs SKAG-W1 datapath diagram
- RTL-to-GDS flow diagram
- area comparison bar chart
- FDPE area-accuracy tradeoff chart

## Important wording boundary

These figures should be described as open-source SKY130/OpenROAD physical-design evidence.

Do not describe them as fabricated silicon or commercial signoff.
