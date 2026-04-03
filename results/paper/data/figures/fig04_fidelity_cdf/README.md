# FIG04 Source Pack — Fidelity Distribution Under Load

This folder is the canonical source pack for Figure 4.

Figure goal:
- show route-quality behavior under a representative high-load operating point
- complement blocking results without duplicating them
- compare Mesh-16 and Irregular-12 in a publication-ready layout

Current data limitation:
- the refined OMNeT CSVs do not contain per-request fidelity samples
- therefore this figure uses the ECDF of run-level mean bottleneck fidelity across seeds

Main-paper panels:
- (a) Mesh-16
- (b) Irregular-12

Representative load:
- rate = 40 requests/s

Expected outputs:
- results/paper/export/pdf/qflow_fig04_fidelity_cdf_main.pdf
- results/paper/export/svg/qflow_fig04_fidelity_cdf_main.svg
- results/paper/export/png/qflow_fig04_fidelity_cdf_main.png
