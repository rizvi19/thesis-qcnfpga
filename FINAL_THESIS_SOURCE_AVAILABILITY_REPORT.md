# Final Thesis Source Availability Report

## Verified source snapshot

- Repository: `https://github.com/rizvi19/thesis-qcnfpga`
- Branch: `thesis-final-submission-corrections`
- Exact thesis-source commit: `575a64b19a2a583a7e31e9092c05c9991c24cc76`
- Commit URL: `https://github.com/rizvi19/thesis-qcnfpga/commit/575a64b19a2a583a7e31e9092c05c9991c24cc76`
- Source-tree URL: `https://github.com/rizvi19/thesis-qcnfpga/tree/575a64b19a2a583a7e31e9092c05c9991c24cc76`

The source commit was pushed before the release PDF was compiled. `git ls-remote`
returned the same commit for the named branch, a subsequent fetch resolved the
remote-tracking branch to the same identifier, and `git cat-file` verified that the
object is available locally as a commit obtained from the remote.

## Required source components verified in the commit tree

The following submission components were enumerated with `git ls-tree -r` at the
exact commit above:

- root build source: `document.tex`, `metadata.tex`, and `qflowthesis.sty`;
- all chapter sources under `chapters/`;
- all appendix sources under `appendices/`;
- the bibliography database `bibliography.bib`;
- thesis figure assets under `figures/`, including the routed VLSI images; and
- build and package instructions in `README_FIRST.md`.

The reproducible physical-statistics additions are also present at that commit:

- `reproduce_physical_bootstrap.py`;
- `data/physical_bootstrap_recomputed.csv`; and
- `data/physical_paired_differences.csv`.

## Release procedure

Appendix A receives the exact source identifier through the
`FinalThesisSourceCommit` LaTeX macro during the release build. The later packaging
commit contains compiled artifacts and final QA reports. This separation is
intentional: the identifier printed in the thesis points to an immutable source
tree that does not need to contain its own generated PDF.
