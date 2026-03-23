# Paper Figure Plan — QFlow

This file defines the final figure roadmap for the paper and thesis packaging layer.

The goals are:
1. keep the main paper visually strong and compact,
2. move extra but valuable evidence to appendix/thesis,
3. ensure every figure has one canonical data source and one generation script,
4. maintain a consistent visual style across all plots.

---

# Global figure policy

## Visual standard
- Export formats: PDF, SVG, PNG
- Prefer vector formats in LaTeX
- Use one consistent serif font family
- Use consistent axis label, tick, legend, and annotation sizes
- No default rainbow/jet colormaps
- Use subplot labels `(a)`, `(b)`, `(c)` where needed
- Keep captions interpretive, not merely descriptive
- Use consistent naming for policies across all figures:
  - Distance
  - Key-aware
  - Random
  - Software PMO-GA
  - GA proxy
- Use consistent naming for topologies:
  - Mesh-9
  - Mesh-16
  - Irregular12

## Main-paper figure count target
Target: 6 main-paper figures

## Appendix figure policy
Any figure that is useful but not essential for first-pass reading goes to appendix or thesis-only material.

---

# FIG01 — QFlow architecture and decision dataflow

## Role
This is the identity figure of the paper.  
It tells the reader what QFlow is before any metrics appear.

## Main message
QFlow is a hardware-native fidelity-aware routing accelerator architecture rather than only a software routing heuristic.

## Placement
- Section: Architecture
- Position: early in architecture section after system overview paragraph

## Main-paper status
- Main paper
- Mandatory

## Recommended panel structure
### (a) Top-level architecture
Show:
- input request/state interface
- FDPE block
- SKAG / memory-related block
- control/selection logic
- decision output

### (b) Decision dataflow / pipeline
Show:
- stages from input acquisition to route selection
- optional cycle/path annotation if clean

## Inputs needed
- block names from frozen RTL narrative
- architecture notes from thesis plan
- pipeline or per-stage logic summary

## Output files
- `results/paper/export/pdf/qflow_fig01_architecture_main.pdf`
- `results/paper/export/svg/qflow_fig01_architecture_main.svg`
- `results/paper/export/png/qflow_fig01_architecture_main.png`

## Source directory
- `results/paper/data/figures/fig01_architecture/`

## Generation path
This may be made using:
- draw.io / diagrams.net exported to SVG/PDF, or
- Figma, or
- TikZ if a later conversion is needed

## Styling notes
- Clean rectangular blocks
- left-to-right flow
- no overcrowding
- use subtle arrow and grouping hierarchy
- avoid tiny text

## Caption intent
Explain what the architecture contains and why it supports fast hardware routing decisions.

---

# FIG02 — Decision latency comparison across hardware and software baselines

## Role
This is the first hard quantitative proof that the hardware route-decision engine matters.

## Main message
QFlow achieves a strong hardware-side decision latency advantage relative to software-side routing evaluation flow.

## Placement
- Section: Implementation / Results
- Position: near hardware timing/resource presentation

## Main-paper status
- Main paper
- Mandatory

## Recommended chart type
- bar chart or log-scale bar chart

## X-axis
- routing methods / implementation modes

## Y-axis
- decision latency
- use explicit unit
- if mixed domains exist, label carefully

## Candidate compared items
- QFlow hardware decision path
- Software PMO-GA decision path
- Key-aware software decision path
- Distance baseline decision path
- optional: normalized version if absolute time comparison needs care

## Inputs needed
- measured or derived hardware latency summary
- software decision latency summary
- exact statement of measured vs estimated values

## Output files
- `results/paper/export/pdf/qflow_fig02_latency_main.pdf`
- `results/paper/export/svg/qflow_fig02_latency_main.svg`
- `results/paper/export/png/qflow_fig02_latency_main.png`

## Source directory
- `results/paper/data/figures/fig02_latency/`

## Generation script
- `results/paper/scripts/make_fig02_latency.py`

## Styling notes
- if using log scale, say so in caption
- visually distinguish measured vs estimated values
- avoid overstating comparability if measurement conditions differ

## Caption intent
State how latency was compared and what the figure demonstrates about the hardware decision engine.

---

# FIG03 — Blocking probability versus offered load

## Role
This is the central dynamic-load performance figure.

## Main message
Under increasing request load, structured routing policies behave more robustly than random routing, and the best policies preserve lower blocking more effectively.

## Placement
- Section: Dynamic-load Results
- Position: first major OMNeT++ results figure

## Main-paper status
- Main paper
- Mandatory

## Recommended panel structure
### (a) Mesh-16
### (b) Irregular12

## X-axis
- offered load / request rate / normalized load
- use exact metric from dataset

## Y-axis
- blocking probability

## Curves
- Distance
- Key-aware
- Random
- GA proxy

## Inputs needed
- `mesh16_blocking.csv`
- `irregular12_blocking.csv`

## Output files
- `results/paper/export/pdf/qflow_fig03_blocking_main.pdf`
- `results/paper/export/svg/qflow_fig03_blocking_main.svg`
- `results/paper/export/png/qflow_fig03_blocking_main.png`

## Source directory
- `results/paper/data/figures/fig03_blocking/`

## Generation script
- `results/paper/scripts/make_fig03_blocking.py`

## Styling notes
- keep same legend order in both panels
- share y-axis if possible
- use same load range if possible
- include confidence bands only if truly available and not cluttering

## Caption intent
Explain how blocking changes with increasing load and which routing trends matter most.

---

# FIG04 — End-to-end fidelity CDF under dynamic load

## Role
This complements blocking by showing route-quality behavior.

## Main message
The stronger routing policies do not just serve more requests; they also preserve better fidelity characteristics across accepted paths.

## Placement
- Section: Dynamic-load Results
- Position: immediately after blocking figure

## Main-paper status
- Main paper
- Mandatory

## Recommended panel structure
### (a) Mesh-16
### (b) Irregular12

## X-axis
- end-to-end path fidelity

## Y-axis
- cumulative probability

## Curves
- Distance
- Key-aware
- Random
- GA proxy

## Inputs needed
- `mesh16_fidelity_cdf.csv`
- `irregular12_fidelity_cdf.csv`

## Output files
- `results/paper/export/pdf/qflow_fig04_fidelity_cdf_main.pdf`
- `results/paper/export/svg/qflow_fig04_fidelity_cdf_main.svg`
- `results/paper/export/png/qflow_fig04_fidelity_cdf_main.png`

## Source directory
- `results/paper/data/figures/fig04_fidelity_cdf/`

## Generation script
- `results/paper/scripts/make_fig04_fidelity_cdf.py`

## Styling notes
- keep legend ordering identical to blocking figure
- choose axis ranges carefully so separation is visible
- do not over-smooth raw CDFs artificially

## Caption intent
Explain what the fidelity distributions say about route quality under load.

---

# FIG05 — Per-link utilization heatmap for load-spreading comparison

## Role
This is the most visually persuasive figure for “tradeoff-aware separation”.

## Main message
The GA-style policy spreads load differently and often more evenly than a simpler deterministic policy, revealing structurally different routing behavior.

## Placement
- Section: Dynamic-load Results / Discussion
- Position: after blocking and fidelity figures

## Main-paper status
- Main paper
- Mandatory

## Recommended panel structure
### (a) Mesh-16 Key-aware
### (b) Mesh-16 GA proxy

## Alternative if needed
If the paper benefits from one more panel:
### (c) Difference heatmap

Only add this if it remains clear and not visually busy.

## Inputs needed
- `mesh16_keyaware_link_usage.csv`
- `mesh16_ga_proxy_link_usage.csv`

## Output files
- `results/paper/export/pdf/qflow_fig05_heatmap_main.pdf`
- `results/paper/export/svg/qflow_fig05_heatmap_main.svg`
- `results/paper/export/png/qflow_fig05_heatmap_main.png`

## Source directory
- `results/paper/data/figures/fig05_heatmap/`

## Generation script
- `results/paper/scripts/make_fig05_heatmap.py`

## Styling notes
- identical graph layout in both panels
- identical color scale in both panels
- identical edge ordering if matrix-style display is used
- no misleading auto-rescaling per panel

## Caption intent
State clearly that the figure demonstrates routing-structure differences and load-spreading behavior, not necessarily universal superiority on every metric.

---

# FIG06 — Scalability trend across topology sizes

## Role
This protects the paper from looking too narrow.

## Main message
The routing framework maintains meaningful behavior across multiple topology sizes or structural classes.

## Placement
- Section: Dynamic-load Results / Generalization
- Position: toward the end of results section

## Main-paper status
- Main paper
- Mandatory

## Recommended chart type
- line chart

## X-axis
- topology size / node count / topology category

## Y-axis
Choose one main y-metric only for clarity:
- blocking at a representative load, or
- average fidelity, or
- routing score, or
- runtime/latency if this is the real intended scaling message

## Inputs needed
- `scalability_summary.csv`

## Output files
- `results/paper/export/pdf/qflow_fig06_scalability_main.pdf`
- `results/paper/export/svg/qflow_fig06_scalability_main.svg`
- `results/paper/export/png/qflow_fig06_scalability_main.png`

## Source directory
- `results/paper/data/figures/fig06_scalability/`

## Generation script
- `results/paper/scripts/make_fig06_scalability.py`

## Styling notes
- keep this figure simple
- do not overload with too many policy curves if it hurts readability
- use topology labels that match the text exactly

## Caption intent
Explain what kind of scaling trend is being claimed and what limitations remain.

---

# Appendix / Thesis-only figure plan

These figures are valuable but should not crowd the main paper unless required.

---

# APPFIG01 — Blocking probability versus load for Mesh-9

## Role
Extra support for topology consistency

## Status
- Appendix
- Secondary

## Inputs
- `mesh9_blocking.csv`

## Notes
Use same style as FIG03.

---

# APPFIG02 — Fidelity CDF for Mesh-9

## Role
Extra support for topology consistency

## Status
- Appendix
- Secondary

## Inputs
- `mesh9_fidelity_cdf.csv`

## Notes
Use same style as FIG04.

---

# APPFIG03 — Timing-closure evolution from tc3 to tc5

## Role
Shows engineering maturation and improvement

## Status
- Appendix / thesis
- Secondary

## Inputs
- tc3 summary
- tc4 summary
- tc5 summary
- optional OOC summary

## Notes
Very useful for thesis and reviewer backup, but not mandatory in the main paper.

---

# APPFIG04 — Hardware versus Python verification scatter/residual plot

## Role
Shows end-to-end agreement and residual behavior

## Status
- Appendix / thesis
- Secondary

## Inputs
- `hw_vs_python_samples.csv`

## Notes
Useful if verification accuracy discussion needs visual support.

---

# Figure build order

1. FIG01 — Architecture
2. FIG02 — Latency
3. FIG03 — Blocking vs Load
4. FIG04 — Fidelity CDF
5. FIG05 — Heatmap
6. FIG06 — Scalability
7. Appendix figures only after main-paper figures are frozen

---

# Definition of done for each figure

A figure is complete only when all of the following are true:
- canonical input files copied into its source directory
- generation script exists and runs
- PDF, SVG, and PNG exports are generated
- title/caption intent is written
- axis labels and units are finalized
- legend names match paper terminology
- placement in main paper or appendix is confirmed
- asset register status is updated from `planned` to `ready` or `done`

