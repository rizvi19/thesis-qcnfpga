# Paper Table Plan — QFlow

This file defines the final table roadmap for the paper and thesis packaging layer.

The goals are:
1. keep the main paper tables compact and reviewer-friendly,
2. use tables for credibility-critical summaries,
3. prevent repetition of information already obvious from figures,
4. separate measured, estimated, and inferred quantities clearly.

---

# Global table policy

## Visual standard
- Prefer LaTeX table export for manuscript integration
- Keep headers short but precise
- Put units in headers
- Use consistent decimal precision
- Bold only the most important values
- Use footnotes when mixing measured and estimated values
- Avoid extremely wide tables in the main paper

## Main-paper table count target
Target: 3 main tables

## Appendix table policy
Any broad literature matrix, ablation expansion, or detailed run-level statistics can move to appendix or thesis.

---

# TAB01 — Resource utilization and timing summary

## Role
This is the primary hardware credibility table.

## Main message
QFlow is not just conceptual; it is implemented and timing-validated on the target FPGA class.

## Placement
- Section: Implementation Results
- Position: near FIG02 latency figure

## Main-paper status
- Main paper
- Mandatory

## Suggested columns
- Design / Variant
- LUTs
- FFs
- BRAM
- DSP
- WNS (ns)
- WHS (ns) if available
- Fmax (MHz)
- Status / Note

## Suggested rows
- tc5 top-level post-synthesis
- OOC post-route
- optional prior timing snapshot only if needed for context
- optional submodule line only if it strengthens clarity and does not clutter

## Inputs needed
- `results/phase9h/...summary.json`
- `results/phase9h_ooc/...summary.json`

## Output files
- `results/paper/export/tex/qflow_tab01_resources_timing_main.tex`
- `results/paper/export/png/qflow_tab01_resources_timing_main.png`
- `results/paper/data/tables/tab01_resources_timing/tab01_resources_timing.csv`

## Source directory
- `results/paper/data/tables/tab01_resources_timing/`

## Generation script
- `results/paper/scripts/make_tab01_resources_timing.py`

## Styling notes
- if some rows are measured and others are estimated, label them explicitly
- do not mix incomparable synthesis conditions without a note
- keep only the rows that directly support the paper claim

## Caption intent
Summarize the implementation cost and timing closure status that support the hardware-realizable claim.

---

# TAB02 — Approximation and verification error summary

## Role
This is the correctness assurance table.

## Main message
The routing hardware approximation and implementation remain acceptably aligned with the reference model.

## Placement
- Section: Verification / Accuracy
- Position: after the verification narrative

## Main-paper status
- Main paper
- Mandatory

## Suggested columns
- Metric
- Quantity / Scope
- Mean Error
- Max Error
- RMSE or mismatch rate
- Notes

## Candidate rows
- LUT approximation error
- fixed-point deviation
- hardware vs Python route-score mismatch
- hardware vs Python route-choice agreement
- optional per-block residual summary

## Inputs needed
- `approx_error_summary.csv`
- `hw_vs_python_check.csv`

## Output files
- `results/paper/export/tex/qflow_tab02_verification_error_main.tex`
- `results/paper/export/png/qflow_tab02_verification_error_main.png`
- `results/paper/data/tables/tab02_verification_error/tab02_verification_error.csv`

## Source directory
- `results/paper/data/tables/tab02_verification_error/`

## Generation script
- `results/paper/scripts/make_tab02_verification_error.py`

## Styling notes
- do not bury the main agreement metric
- separate model approximation error from full decision mismatch
- if agreement is percentage-based, keep two decimal places

## Caption intent
Explain the degree to which the hardware implementation tracks the reference model and where approximation enters.

---

# TAB03 — Condensed baseline comparison summary

## Role
This is the reviewer-facing interpretation table.

## Main message
Each routing policy has a different strength, and QFlow-relevant routing behavior should be interpreted through balanced tradeoffs rather than a false universal-winner narrative.

## Placement
- Section: Results Discussion / Summary
- Position: near the end of the results section

## Main-paper status
- Main paper
- Mandatory

## Suggested columns
- Policy
- Decision Cost
- Blocking Trend
- Fidelity Trend
- Load Balancing
- Interpretive Summary

## Suggested rows
- Distance
- Key-aware
- Random
- Software PMO-GA
- GA proxy

## Inputs needed
- `static_baseline_summary.csv`
- `dynamic_baseline_summary.csv`

## Output files
- `results/paper/export/tex/qflow_tab03_baseline_summary_main.tex`
- `results/paper/export/png/qflow_tab03_baseline_summary_main.png`
- `results/paper/data/tables/tab03_baseline_summary/tab03_baseline_summary.csv`

## Source directory
- `results/paper/data/tables/tab03_baseline_summary/`

## Generation script
- `results/paper/scripts/make_tab03_baseline_summary.py`

## Styling notes
- this table is partly interpretive, so wording matters
- avoid exaggerated labels like “best overall” unless strictly proven
- strong wording is acceptable if it is qualified and supported

## Caption intent
Provide a compact qualitative-plus-quantitative reading guide to the baseline comparison results.

---

# TABA1 — Related-work positioning table

## Role
This table makes the novelty argument easy to scan.

## Main message
QFlow occupies a distinct position by combining fidelity-aware routing logic with a hardware-native accelerator framing.

## Placement
- Section: Related Work
- Position: near end of related-work section

## Main-paper status
- Optional
- Usually appendix if space is tight
- Strong candidate for thesis main body

## Suggested columns
- Work
- Routing Focus
- Fidelity-aware
- Hardware-native
- FPGA validated
- Dynamic network evaluation
- Notes

## Inputs needed
- `related_work_positioning.csv`

## Output files
- `results/paper/export/tex/qflow_taba1_related_work_positioning.tex`
- `results/paper/export/png/qflow_taba1_related_work_positioning.png`
- `results/paper/data/tables/tabA_related_work_positioning/tabA_related_work_positioning.csv`

## Source directory
- `results/paper/data/tables/tabA_related_work_positioning/`

## Styling notes
- do not overload with too many papers in the main paper
- keep thesis version larger if needed
- use concise, factual comparison markers

## Caption intent
Show where QFlow sits relative to prior routing and FPGA-oriented studies.

---

# Possible appendix tables

These are not mandatory now, but may be useful later:
- extended OMNeT run summary table
- topology-wise metric breakdown table
- timing-closure progression table
- per-block verification residual table
- full literature matrix table for thesis

---

# Table build order

1. TAB01 — Resource utilization and timing
2. TAB02 — Approximation and verification error
3. TAB03 — Baseline comparison summary
4. TABA1 only after the related-work section is finalized

---

# Definition of done for each table

A table is complete only when all of the following are true:
- canonical input files copied into its source directory
- generation script exists and runs
- LaTeX export is generated
- CSV backing file is generated
- caption intent is written
- units and decimal precision are finalized
- estimated vs measured values are labeled where needed
- placement in main paper or appendix is confirmed
- asset register status is updated from `planned` to `ready` or `done`

