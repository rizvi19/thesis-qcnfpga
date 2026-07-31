# Final Micro-Corrections Report

## Outcome

The focused final correction pass is complete. Training and evaluation rewards now
use separate notation throughout every requested location:

- `r_t^{train}` is the executed reward used by the offline Q-learning target;
- `r_t^{eval}` is the common reward used for validation, held-out testing, Table 4.1,
  and final controller comparisons;
- the Q-learning update explicitly uses `r_t^{train}`; and
- 4.6771 is explicitly identified as a mean of `r_t^{eval}`, not a training-target
  mean.

The successful training reward uses balance coefficient 4. The successful evaluation
reward uses balance coefficient 1. Both blocked rules retain the executed value
`-4 - 0.25 sigma_t`; no alternative blocked value was invented.

Table 4.1 now labels the metric as **Mean balance utility**. Its discussion states
that larger balance utility means lower post-decision imbalance under the defined
utility and that the learned controller had the highest reported mean balance utility
over the four held-out software traces.

## Source scope

Only these thesis-source files changed:

- `chapters/3_methodology.tex`;
- `chapters/4_performance_result.tex`;
- `chapters/vi_symbols.tex`;
- `appendices/c_additional_results.tex`; and
- `appendices/e_worked_contract_cases.tex`.

No result value, figure, citation, experimental claim, or scientific conclusion was
changed. The three Table 4.1 rows were compared against the parent commit and remain
numerically identical.

## Certificate

The certificate source required no edit. The rendered page retains balanced
Supervisor and External Examiner columns, sufficient signature space, and blank
examiner Name, Designation, Institution, and Date fields. It contains no invented
examiner identity or placeholder assignment text. The supervisor remains Dr. Md.
Nazrul Islam Mondal, Professor, Department of Computer Science & Engineering, RUET,
Rajshahi-6204, Bangladesh.

## Source and remote verification

- Branch: `thesis-final-submission-corrections`
- Exact source commit: `6d3bee97349cbd4b14e4213fb3ea2ad7b0a2a744`
- Repository: `https://github.com/rizvi19/thesis-qcnfpga`
- Remote result: `git ls-remote` returned the exact same SHA for the branch; a
  subsequent fetch and `git cat-file` resolved it as a commit.

The source tree contains the root thesis file, chapters, appendices, bibliography,
figures, bootstrap-reproduction script, required data, and build instructions.
Appendix A embeds this source SHA, not the later packaging commit.

## Build and inspection

- Final PDF: 92 A4 pages
- SHA-256: `DC19B2F404EF81C0C30A2207978A3B873984C73BBBEB815C595EDD174261327F`
- Undefined references/citations: 0
- Duplicate labels: 0
- Missing figures: 0
- Overfull boxes: 0
- Rerun warnings: 0
- Embedded fonts: all

All 92 final pages were rendered and reviewed in contact sheets. Detailed page-level
inspection covered the certificate, Section 3.12, Table 3.7, Table 4.1, Section 4.3,
Appendix A, Appendix C.7, and Appendix E.3. No clipping, overlap, missing glyph,
unreadable equation, or table overflow was found.
