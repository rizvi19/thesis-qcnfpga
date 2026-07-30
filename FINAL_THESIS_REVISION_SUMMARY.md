# Final Thesis Revision Summary

## Submission identity

- Thesis: *QFlow: A Fixed-Point FPGA Accelerator for Adaptive Key-Resource-Aware Route-Candidate Evaluation in Trusted-Relay QKD Networks*
- Author: Shahriar Rizvi (Roll 2003104)
- Department: Computer Science & Engineering, RUET
- Submission branch: `thesis-final-scientific-integrity-pass`
- Exact thesis-source commit: `2ac7209e2c621d41165e3eb5136f5d250ead8701`

## Revision outcome

The second pass expanded the thesis from 68 to 97 pages through substantive background,
methodology, interpretation, technical figures, and reproducibility appendices. No project
timeline, claim ledger, defense script, historical Artix-7/OMNeT++ result section, model-
correction narrative, or procedural filler was restored.

The central semantic correction is explicit: the completed H4 experiment uses minimum key
occupancy, a bounded bottleneck route-quality code, offered request load, and utilization
imbalance. No retrained/rebuilt/replayed replenishment controller was found, so the executed
route-quality feature was not renamed. The final classical network model is kept separate
from the registered synthetic/controller contract.

Chapter 2 now includes a trusted-relay routing example, numerical Tchebycheff scoring,
fixed-point arithmetic, and a broader verified literature synthesis. Chapter 3 now gives
the complete reward, thresholds, profiles, H0-H4 behavior, H3 rules, training/freeze method,
detailed RTL architecture, cycle operation, physical protocol, and statistical procedure.
Chapter 4 explains timing, resource capacity, status counts, adaptive-decision exclusions,
UNORM16 effects, related-work boundaries, and route-quality confidence intervals. Appendix E
adds worked controller and verification cases.

## Final QA

- PDF: `document.pdf`, 97 A4 pages
- PDF SHA-256: `58C23F007CACCA1E8DE97C3F5B61384AC49EAA5C79CA4F281DE1CA0E0DD007E4`
- Bibliography records: 41
- Undefined references/citations: 0
- Overfull boxes: 0
- Fatal/package warnings in final scan: 0
- Rendered and visually inspected pages: 97

Detailed evidence is in `SCIENTIFIC_SEMANTIC_CONSISTENCY_REPORT.md`,
`METHODOLOGY_COMPLETENESS_CHECKLIST.md`, `FINAL_NUMERICAL_TRACEABILITY.md`, and
`FINAL_THESIS_COMPILE_LOG.txt`.
