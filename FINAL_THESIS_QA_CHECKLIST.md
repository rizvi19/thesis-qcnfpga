# Final Thesis QA Checklist

## Mathematical and semantic integrity

- [x] Equation 3.10 matches the executable reciprocal formula and defines every
  variable, unit, guard, floor, and saturation rule.
- [x] The software-training action is distinguished from the ratio-only physical
  deployment projection.
- [x] The thesis does not claim that the physical FPGA computes Equation 3.10 or
  deploys the profile alpha coefficients.
- [x] Upstream KMS/SDN eligibility is distinguished from FPGA validity-bit gating.
- [x] H0 is consistently defined as the feasible minimum-hop baseline.
- [x] Path-cost infinity and finite saturation are distinguished from the full-range
  utilization encoding.
- [x] Route quality is treated as a bounded abstract experimental input, not stored-key
  quantum coherence.
- [x] Supporting VLSI results are identified as isolated kernels, not an integrated
  QFlow ASIC.

## Numerical reproducibility

- [x] Row-level H2, H3, and H4 physical results were read from evidence commit
  `290b4ad75eef2af2b9da2f1f281a2b89416cfd24`.
- [x] The paired-row bootstrap is executable from
  `reproduce_physical_bootstrap.py`.
- [x] Sampling unit, 58-pair filter, 10,000 replicates, MT19937 RNG, seed 20260731,
  percentile method, and R-7 interpolation are declared.
- [x] Recomputed H4-H2 interval: [-25.120690, 226.620690] UNORM16 units.
- [x] Recomputed H4-H3 interval: [-242.281466, 77.534483] UNORM16 units.
- [x] Both intervals cross zero; route-quality superiority is not claimed.
- [x] Tables, figure, appendices, CSV data, and audit reports use the same values.

## Source and release

- [x] Branch: `thesis-final-submission-corrections`.
- [x] Exact source commit:
  `575a64b19a2a583a7e31e9092c05c9991c24cc76`.
- [x] The branch was pushed and independently resolved with `git ls-remote` and a
  subsequent fetch.
- [x] Root source, chapters, appendices, figures, bibliography, and build instructions
  were enumerated at that exact commit.
- [x] Appendix A contains the exact source commit.
- [x] `document.pdf` and the packaged PDF are identical 92-page A4 files.
- [x] Final PDF SHA-256:
  `2AD29C8FA49776CE55B7D1A6A4C9F708127411624AE358B75E16C0DBD14899CC`.

## Build and visual QA

- [x] XeLaTeX/BibTeX/XeLaTeX/XeLaTeX completed successfully.
- [x] All 41 bibliography records compiled.
- [x] No fatal error, undefined reference/citation/control sequence, missing glyph,
  multiply defined label, overfull box, or rerun request remains.
- [x] All fonts are embedded.
- [x] All 92 pages rendered; 88 are portrait and 4 are intentional landscape pages.
- [x] Every rendered page was visually inspected.
- [x] The abstract occupies exactly one page.
- [x] Sparse continuation pages in Methodology, Chapter 4, and Appendix A were removed.
- [x] No blank page, clipping, overlap, orphaned caption, or unreadable table remains.
