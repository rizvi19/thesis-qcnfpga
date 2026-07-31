# Final Thesis Revision Summary

## Submission identity

- Thesis: *QFlow: A Fixed-Point FPGA Accelerator for Adaptive Key-Resource-Aware
  Route-Candidate Evaluation in Trusted-Relay QKD Networks*
- Author: Shahriar Rizvi (Roll 2003104)
- Department: Computer Science & Engineering, RUET
- Submission branch: `thesis-final-submission-corrections`
- Exact thesis-source commit:
  `6d3bee97349cbd4b14e4213fb3ea2ad7b0a2a744`

## Final micro-correction

The thesis now explicitly separates the reward that shaped the offline Q-values from
the reward used to compare completed controllers. `r_t^{train}` uses the executed
successful balance coefficient 4 and appears in the Q-learning update. `r_t^{eval}`
uses balance coefficient 1 and appears in validation, held-out testing, Table 4.1,
and the reported results. Both blocked rules retain the executed value
`-4 - 0.25 sigma_t`. The reported 4.6771 is identified as an evaluation-scale mean.

Table 4.1 now labels its fifth metric **Mean balance utility**, explains that larger
values mean lower post-decision imbalance, and retains every original number. The
same terminology is propagated through Section 3.12, Table 3.7, Section 4.3,
Appendix C.7, Appendix E.3, and the List of Symbols.

The official certificate structure was preserved. The external examiner fields remain
blank, and no speculative identity or placeholder was added.

## Final release

- Root PDF: `document.pdf`
- Packaged PDFs:
  - `output/pdf/QFlow_Thesis_VLSI_Integrated.pdf`
  - `output/pdf/QFlow_Thesis_Final_Submission.pdf`
- Pages: 92 A4
- PDF SHA-256:
  `DC19B2F404EF81C0C30A2207978A3B873984C73BBBEB815C595EDD174261327F`
- Bibliography records: 41
- Undefined references/citations: 0
- Overfull boxes: 0
- Non-embedded fonts: 0
- Rendered and visually reviewed pages: 92

Detailed evidence is in `FINAL_MICRO_CORRECTIONS_REPORT.md`,
`FINAL_THESIS_SOURCE_AVAILABILITY_REPORT.md`,
`FINAL_THESIS_COMPILE_LOG.txt`, and `FINAL_THESIS_QA_CHECKLIST.md`.
