# P1 Literature Audit and Comparison Protocol

## 1. Purpose

This protocol repairs QFlow's literature and comparison claims before new RL or
Spartan-6 RTL work begins. It preserves the original workbook as immutable input
and requires every paper, number and resulting claim to be traceable to a valid
comparison class and a primary or official source.

## 2. Controlled input

- Source: `literature/p1/source/QFlow_Literature_Review_Matrix_original.xlsx`
- SHA-256: `45f7f4f544897998f5f869a4d2904fd3755eae9a440903fa016a6969c6b97df1`
- Extracted audit records: 50
- The source workbook is never edited or overwritten.

## 3. Comparison classes

| Class | Scope | Permitted conclusion |
|---|---|---|
| A | H0-H4 on the same Nexys 3 shell | Direct hardware/controller comparison |
| B | Identical algorithm, arithmetic and vectors on CPU and FPGA | Platform acceleration only |
| C | Algorithms evaluated on identical topology, traces and seeds | Network/algorithm utility |
| D | Published FPGA routing, GA, RL or QKD components | Normalized component context only |

Published software QKD-routing work is not a raw speed baseline for QFlow
hardware. Published FPGA component work is not a direct QKD-routing competitor
unless it implements the same routing function and workload.

## 4. Required paper fields

Every retained record must have verified identity, implementation/platform,
evidence layer, comparison class, direct URL or DOI, verification scope, and a
disposition. Quantitative results must be separated from qualitative author
claims and from QFlow inferences.

Platform vocabulary: FPGA measured; FPGA synthesis only; CPU software;
simulation; emulation; physical testbed; survey/review; algorithmic/theoretical;
mixed; unclear.

Evidence vocabulary: measured hardware; synthesized hardware; software runtime;
network simulation; analytical result; physical network testbed; survey synthesis;
metadata only.

Latency vocabulary: explicitly measured; explicitly simulated; reported without
clear scope; not reported; not applicable; unverified. Software implementation
does not imply millisecond latency.

## 5. Source rules

Technical verification uses the publisher page, DOI record, official preprint,
standards body, institutional report, or the paper itself. Search-result snippets,
secondary summaries and generated text are discovery aids only. No value is
retained as measured unless the primary source explicitly reports its definition,
unit and evaluation context.

## 6. Search families

1. `QKD network routing FPGA hardware accelerator`
2. `quantum key distribution routing hardware dataplane`
3. `QKD routing reinforcement learning FPGA`
4. `FPGA shortest path routing accelerator`
5. `FPGA genetic algorithm multi objective routing`
6. `FPGA Q-learning reinforcement learning architecture`
7. `FPGA quantum key distribution reconciliation post processing`
8. `SDN QKD routing testbed latency`

Record exact queries, database/publisher, date, filters, result counts and
exclusions in `literature/p1/audit/search_log.csv`.

## 7. Inclusion criteria

- Direct QKD routing, resource allocation, recovery or key-aware path selection.
- Quantum-network routing where fidelity/decoherence state is relevant.
- FPGA routing, GA or RL work that gives component-level hardware context.
- FPGA/SoC QKD subsystems that clarify the implemented protocol layer.
- Foundational algorithms explicitly used by QFlow.
- Verifiable identity through a primary or official source.

## 8. Exclusion codes

| Code | Reason |
|---|---|
| E1 | Outside routing/QKD/FPGA/optimization scope |
| E2 | Secondary-only source when a primary source is required |
| E3 | Duplicate or superseded version |
| E4 | Identity, venue or year cannot be verified |
| E5 | No relevant method, metric or architectural context |
| E6 | Claimed value cannot be found in the primary source |
| E7 | Paper is inaccessible; retain only metadata and mark verification limited |

## 9. Claim controls

- No `first ever`, `all papers`, `zero papers`, `1000x`, or similar universal
  statement without a completed reproducible systematic search.
- No inferred latency.
- No algorithm-superiority claim from unrelated hardware/software timings.
- No estimated power labelled measured.
- No Nexys 3 QFlow-Mini value mixed with the full Artix-7 design.
- Negative and statistically insignificant results remain visible.

## 10. P1 exit gate

- All retained rows have A-D classification and source status.
- Unsupported or inferred quantitative claims are removed or clearly held.
- H0-H4 same-board contract remains unchanged unless source evidence requires a
  documented correction.
- Search and exclusion records are reproducible.
- Corrected workbook, claim register, protocol, defense response and validation
  report are committed and pushed on `rl-nexys3-adaptive`.
- The working tree is clean after push.
