# Final Thesis QA Checklist

## Focused reward correction

- [x] Successful evaluation reward uses balance coefficient 1.
- [x] Successful training reward uses balance coefficient 4.
- [x] Both blocked rules remain `-4 - 0.25 sigma_t`.
- [x] The Q-learning update uses `r_t^{train}`.
- [x] Validation, held-out testing, Table 4.1, and final comparisons use
  `r_t^{eval}`.
- [x] 4.6771 is identified as an evaluation-scale mean.
- [x] Table 4.1 says **Mean balance utility**.
- [x] Larger balance utility is explained as lower post-decision imbalance.
- [x] The three Table 4.1 result rows are numerically unchanged.

## Certificate

- [x] Supervisor and External Examiner columns are visually balanced.
- [x] External examiner Name, Designation, Institution, and Date remain blank.
- [x] No examiner identity or assignment placeholder was invented.
- [x] Supervisor name, title, department, institution, and address remain correct.
- [x] No overlap or awkward certificate line break is present.

## Source and release

- [x] Branch: `thesis-final-submission-corrections`.
- [x] Exact source commit:
  `6d3bee97349cbd4b14e4213fb3ea2ad7b0a2a744`.
- [x] `git ls-remote` matched the local source SHA after push.
- [x] A subsequent fetch and object-resolution check succeeded.
- [x] Required source, bibliography, figure, script, data, and build files exist in
  that commit.
- [x] Appendix A contains the exact source SHA.
- [x] Installed PDF copies are identical 92-page A4 files.
- [x] Final PDF SHA-256:
  `DC19B2F404EF81C0C30A2207978A3B873984C73BBBEB815C595EDD174261327F`.

## Build and visual QA

- [x] XeLaTeX/BibTeX/XeLaTeX stabilization and PDF conversion completed.
- [x] All 41 bibliography records compiled.
- [x] No fatal error, undefined reference/citation/control sequence, duplicate label,
  missing glyph, overfull box, or rerun request remains.
- [x] All fonts are embedded.
- [x] All 92 final pages rendered and were reviewed in contact sheets.
- [x] Detailed review covered the certificate, Section 3.12, Table 3.7, Table 4.1,
  Section 4.3, Appendix A, Appendix C.7, and Appendix E.3.
- [x] No blank page, clipping, overlap, orphaned caption, unreadable equation, or
  table overflow remains.
