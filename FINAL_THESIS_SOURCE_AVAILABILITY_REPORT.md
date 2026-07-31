# Final Thesis Source Availability Report

## Verified source snapshot

- Repository: `https://github.com/rizvi19/thesis-qcnfpga`
- Branch: `thesis-final-submission-corrections`
- Exact thesis-source commit: `6d3bee97349cbd4b14e4213fb3ea2ad7b0a2a744`
- Commit URL: `https://github.com/rizvi19/thesis-qcnfpga/commit/6d3bee97349cbd4b14e4213fb3ea2ad7b0a2a744`
- Source-tree URL: `https://github.com/rizvi19/thesis-qcnfpga/tree/6d3bee97349cbd4b14e4213fb3ea2ad7b0a2a744`

The source commit was pushed before the release PDF was compiled. `git ls-remote`
returned the same SHA for the named branch. A subsequent fetch and `git cat-file`
resolved the fetched object as a commit. Remote verification therefore succeeded.

## Required source components verified

The exact commit contains:

- `document.tex`, `metadata.tex`, and `qflowthesis.sty`;
- chapter sources under `chapters/`;
- appendix sources under `appendices/`;
- `bibliography.bib`;
- thesis figure assets under `figures/`;
- `reproduce_physical_bootstrap.py`;
- `data/physical_bootstrap_recomputed.csv`;
- `data/physical_paired_differences.csv`; and
- build/package instructions in `README_FIRST.md`.

## Release procedure

Appendix A receives the exact source identifier through the
`FinalThesisSourceCommit` macro during the release build. The later packaging commit
contains compiled artifacts and final reports. The SHA printed in the thesis therefore
identifies the immutable source snapshot rather than the artifact-only commit.
