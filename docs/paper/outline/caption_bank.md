# Caption Bank — QFlow Paper

This file stores working and final captions for all paper figures and tables.
Use it as the single caption-development location before moving text into LaTeX.

---

# Caption writing policy

## Rules
- The first sentence should say what is shown.
- The second sentence should say what the reader should learn.
- Do not oversell beyond the claim-evidence map.
- Keep terminology consistent with:
  - Distance
  - Key-aware
  - Random
  - Software PMO-GA
  - GA proxy
- Distinguish measured, post-synthesis, OOC post-route, estimated, and proxy results carefully.
- Avoid universal claims unless strictly proven.

## Caption status tags
- DRAFT
- REVISED
- FINAL

---

# FIG01 — QFlow architecture and decision dataflow
**Status:** REVISED

## Short caption
QFlow architecture and decision dataflow.

## Draft caption v1
**Figure 1.** QFlow architecture and decision dataflow. The figure shows the hardware-native routing pipeline, including the fidelity-/state-related processing blocks, selection logic, and final route-decision output path. This architecture framing highlights that QFlow is implemented as a routing accelerator core rather than only as a software policy.

## Draft caption v2
**Figure 1.** Top-level QFlow architecture and route-decision dataflow. Inputs describing the current request and network state are processed through the core scoring and selection path to produce a routing decision in hardware. The diagram summarizes the structure that enables low-latency fidelity-aware decision making.

## Caption intent notes
- Must define QFlow visually before quantitative plots appear.
- Must support the “hardware-native accelerator” identity.
- Do not introduce unexplained acronyms in the caption if not already defined in nearby text.

---

# FIG02 — Decision latency comparison
**Status:** DRAFT

## Short caption
Decision latency comparison across hardware and software baselines.

## Draft caption v1
**Figure 2.** Decision latency comparison across hardware and software routing modes. The QFlow hardware decision path achieves sub-microsecond latency and is substantially faster than the evaluated software baselines, supporting the use of an FPGA-based routing accelerator for time-sensitive routing decisions. The hardware bar is derived from cycle count at 100 MHz using the GA selection path, whereas the software bars report measured median runtime.

## Caption intent notes
- Must be careful about mixed measured/estimated values.
- Should emphasize latency advantage without implying unfair equivalence.

---

# FIG03 — Blocking probability versus offered load
**Status:** DRAFT

## Short caption
Blocking probability versus offered load for the main dynamic-load topologies.

## Draft caption v1
**Figure 3.** Blocking probability versus offered load for (a) Mesh-16 and (b) Irregular12. As load increases, structured routing policies remain more robust than random routing, while the strongest policies preserve lower blocking over a wider operating range. The figure summarizes the main dynamic-load stress behavior used in the paper.

## Caption intent notes
- Avoid saying one policy is universally best unless fully supported.
- Keep interpretation aligned with actual curves.

---

# FIG04 — End-to-end fidelity CDF under load
**Status:** DRAFT

## Short caption
End-to-end fidelity CDF under dynamic load.

## Draft caption v1
**Figure 4.** End-to-end fidelity CDF under dynamic load for (a) Mesh-16 and (b) Irregular12. The distributions show how routing policy affects the quality of accepted paths, complementing the blocking analysis with a route-fidelity perspective. Better-separated curves indicate materially different routing behavior under congestion.

## Caption intent notes
- Must connect quality view to blocking view.
- Do not overclaim if curve separation is moderate.

---

# FIG05 — Per-link utilization heatmap
**Status:** DRAFT

## Short caption
Per-link utilization heatmap for load-spreading comparison.

## Draft caption v1
**Figure 5.** Per-link utilization heatmaps for Mesh-16 under (a) Key-aware routing and (b) the GA proxy policy. Using a shared visual scale, the figure highlights differences in how traffic is distributed across network links, helping explain tradeoff-aware routing behavior beyond headline blocking metrics.

## Caption intent notes
- Shared scale must be true in the final plot.
- Good place to discuss balancing behavior, not universal superiority.

---

# FIG06 — Scalability trend
**Status:** DRAFT

## Short caption
Scalability trend across topology sizes.

## Draft caption v1
**Figure 6.** Scalability trend across the evaluated topology set. The figure summarizes how the selected routing metric changes with topology size or structure, providing a compact view of whether the observed behavior remains meaningful beyond a single network instance.

## Caption intent notes
- Keep the chosen metric explicit in final version.
- Good figure for answering reviewer generalization concerns.

---

# TAB01 — Resource utilization and timing summary
**Status:** DRAFT

## Short caption
Resource utilization and timing summary for the finalized QFlow implementation.

## Draft caption v1
**Table 1.** Resource utilization and timing summary for the finalized QFlow implementation. The table reports the implementation cost and timing-closure status of the selected design points, including the final tc5 top-level result and the OOC post-route result used to support the 100 MHz-class claim.

## Caption intent notes
- Label measurement context carefully.
- Do not imply full board deployment.

---

# TAB02 — Approximation and verification error summary
**Status:** DRAFT

## Short caption
Approximation and verification error summary.

## Draft caption v1
**Table 2.** Approximation and verification error summary. The table separates local approximation effects from end-to-end agreement with the reference model, clarifying how closely the hardware implementation tracks the software ground truth.

## Caption intent notes
- Should make correctness story very clear.
- Avoid mixing unrelated metrics without labels.

---

# TAB03 — Baseline comparison summary
**Status:** DRAFT

## Short caption
Condensed comparison of routing baselines.

## Draft caption v1
**Table 3.** Condensed comparison of the routing baselines used in the study. The summary emphasizes that routing quality should be interpreted through tradeoffs among blocking, fidelity behavior, decision cost, and load spreading rather than through a single oversimplified winner label.

## Caption intent notes
- Strong reviewer-facing summary table.
- Wording must remain honest and balanced.

---

# TABA1 — Related-work positioning
**Status:** DRAFT

## Short caption
Positioning of QFlow relative to prior routing and FPGA-oriented studies.

## Draft caption v1
**Table A1.** Positioning of QFlow relative to prior routing and FPGA-oriented studies. The comparison highlights the distinct combination of fidelity-aware routing focus, hardware-native framing, FPGA validation, and dynamic network evaluation targeted by this work.

## Caption intent notes
- Thesis version can be larger than conference version.
- Keep entries factual and concise.

