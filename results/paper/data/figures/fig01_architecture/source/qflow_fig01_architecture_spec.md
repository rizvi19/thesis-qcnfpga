# QFlow FIG01 Drawing Spec

## Purpose
This figure defines the paper-level visual identity of QFlow.

## Source of naming
Use the frozen implementation-aligned names:
- qflow_top_tc5
- fdpe_tc5
- skag_mem_tc4

Paper-facing labels should remain:
- FDPE
- SKAG / Memory Block
- Selection Logic
- Route Decision Output

## Panel structure
### Panel (a): Top-level Architecture
Left-to-right flow:
1. Request Input
2. Network State Input
3. FDPE
4. SKAG / Memory Block
5. Selection Logic
6. Route Decision Output

Optional:
- Control / Sequencing block shown as a dashed-control influence block

### Panel (b): Decision Pipeline / Dataflow
Stages:
- S1 Input Capture
- S2 State / Metric Preparation
- S3 Scoring / Candidate Evaluation
- S4 Selection
- S5 Output Commit

## What the figure should communicate
- QFlow is a hardware-native routing accelerator
- The architecture is structured and realizable
- The decision path is compact enough to support low-latency operation

## What the figure should avoid
- excessive RTL detail
- undefined acronyms
- implying unsupported features
- visual clutter from too many sub-blocks

## Export guidance
Preferred final exports:
- SVG for vector-first paper integration
- PDF for IEEE-safe figure import
- PNG only as backup

## Review checklist
- [ ] Names match manuscript terminology
- [ ] Panel labels are present
- [ ] Text remains readable at two-column paper width
- [ ] Arrows are aligned cleanly
- [ ] No overlapping objects
- [ ] Exported SVG/PDF opens cleanly
