# Final Thesis Revision Summary

## Submission identity

- Thesis: *QFlow: A Fixed-Point FPGA Accelerator for Adaptive Key-Resource-Aware Route-Candidate Evaluation in Trusted-Relay QKD Networks*
- Author: Shahriar Rizvi (Roll 2003104)
- Supervisor: Dr. Md. Nazrul Islam Mondal, Professor
- Department: Computer Science & Engineering, RUET
- Submission date: August 2026
- Submission branch: `thesis-final-submission-polish`
- Submission commit: reported in the final handoff (a commit cannot self-identify inside
  its own tracked contents)

## Files and sections revised

The revision covers the complete manuscript rather than isolated proofreading. The main
changes are in `metadata.tex`, `document.tex`, `qflowthesis.sty`, `bibliography.bib`, all
front-matter files, Chapters 1–5, Appendices A–D, and `README_FIRST.md`.

- Front matter: verified the title-page identity, rewrote the acknowledgement, certificate,
  declaration, and 369-word abstract, and rebuilt the abbreviation and symbol lists.
- Chapter 1: reorganized motivation, research gap, system boundary, problem statement,
  objectives, questions, neutral hypotheses, contributions, practical significance, and
  RUET-required broader considerations.
- Chapter 2: presented the valid classical key-resource model directly, strengthened the
  FPGA/fixed-point/RL background, and rebuilt the literature review around function and
  evidence classes.
- Chapter 3: specified the candidate-evaluation contract, equations, fixed-point codebook,
  offline training and deterministic policy-ROM deployment, H0–H4 configuration table,
  verification methodology, same-board replay, statistical analysis, and supporting VLSI
  method.
- Chapter 4: rebuilt Results and Discussion around software, RTL, post-route, physical
  replay, exactness, timing, resources, controller behavior, route-quality statistics,
  practical deployment, platform selection and cost, VLSI evidence, threats to validity,
  research-question answers, and RH1–RH5 outcomes.
- Chapter 5: synthesized the findings, contributions, limitations, prioritized future work,
  and closing statement without turning the chapter into an execution plan.
- Appendices: replaced the claim-ledger material with a reproducibility register,
  fixed-point/state/protocol contract, complete additional results, and experimental-scope
  notes.

## Notation and terminology

- H0–H4 now mean only hardware evaluation configurations.
- RH1–RH5 now mean only research hypotheses.
- Scoring profiles are consistently `Pi_0`–`Pi_3` in rendered mathematical notation.
- Route candidates are consistently represented by `R_i` in rendered calligraphic notation.
- Repository P0–P6 prefixes appear only where source paths require them and in one appendix
  note explaining that they are repository milestone labels, not experimental variables.
- Fibre attenuation, link key-generation rate, scoring coefficients, and Tchebycheff weights
  use distinct qualified alpha/lambda notation and appear in the List of Symbols.
- “Nexys 3,” “Spartan-6,” “fixed-point,” “post-route,” and “route-candidate evaluation” are
  standardized throughout.

## Scientific presentation

The main chapters no longer read as a correction history, claim-control report, defense
script, or milestone chronology. The thesis presents the valid system directly: QFlow is a
deterministic fixed-point evaluator for externally generated route candidates, with fixed,
rule-adaptive, and offline-learned profile selection. Candidate generation, topology/KMS/SDN
management, security-policy enforcement, and route installation remain control-plane tasks.

Neutral findings remain explicit. Configuration H4 is physically deployable and exhibits
distinct trace-specific adaptive behavior, while the available paired physical results do
not establish route-quality superiority. The supporting OpenROAD evidence concerns isolated
kernels and is not presented as a complete ASIC.

## Added discussion

- “Practical Deployment Scenario” now traces the KMS/SDN-to-QFlow-to-installation sequence
  and confines 2.048 microseconds to the tested FPGA kernel boundary.
- “Platform Selection and Cost Implications” distinguishes CPU, FPGA, and ASIC roles,
  includes the conceptual total-cost and break-even equations, and makes no invented price,
  energy, or speedup claim.
- The state-of-the-art table compares function, platform, evidence type, scale, physical
  implementation, board evidence, fixed-point exactness, and direct comparability. It avoids
  cross-function speedup ratios.

## Numerical and reference verification

Every headline value was checked against version-controlled CSV, JSON, implementation-log,
or physical-design artifacts on evidence commits `290b4ad75eef2af2b9da2f1f281a2b89416cfd24`
and `0093ba288f26a1520e4318f207e13f52d38db5a8`. The value-by-value mapping is in
`FINAL_THESIS_NUMERICAL_AUDIT.md`.

All 26 bibliography records are cited, all 26 citation keys resolve, and no cited key is
missing from `bibliography.bib`. Bibliographic metadata was reconciled with the repository
literature audit and spot-checked against official publisher pages.

## Typesetting and PDF inspection

The final XeLaTeX/BibTeX build produces a 68-page A4 PDF. The log contains no fatal error,
undefined reference, undefined citation, missing character, or overfull box. All 68 pages
were rasterized and inspected in contact sheets; the cover, certificate, abstract, contents,
lists, chapter starts, dense tables, figures, references, and appendices were also checked at
larger scale.

## Author-only fields

No unresolved prose placeholder remains. The external examiner area intentionally uses the
RUET-style blank signature/name line because examiner information was not supplied; it
contains no “to be assigned” or “to be confirmed” instruction.
