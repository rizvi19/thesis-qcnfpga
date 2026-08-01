# Final Figure Placement and Source-SHA Report

## Release identity

- Repository: `https://github.com/rizvi19/thesis-qcnfpga`
- Final thesis-source branch: `thesis-final-submission-corrections`
- Exact thesis-source commit printed in Appendix A.1:
  `f5d665d083fc3ed7f3119a676acf5d236a3d5475`
- Primary FPGA/controller evidence: branch `rl-nexys3-adaptive`, commit
  `290b4ad75eef2af2b9da2f1f281a2b89416cfd24`
- Supporting VLSI evidence: branch `vlsi-kernel-study`, commit
  `0093ba288f26a1520e4318f207e13f52d38db5a8`
- Remote verification: `git push` succeeded and `git ls-remote --heads origin
  thesis-final-submission-corrections` returned
  `f5d665d083fc3ed7f3119a676acf5d236a3d5475` before the later packaging commit.
  The remote source commit contains `document.tex`, `metadata.tex`, all chapter and
  appendix files, `bibliography.bib`, figure sources/assets, build instructions,
  scripts, and supporting data tracked by that snapshot.

## Placement corrections

- **Figure 3.4 was moved to Section 3.11**, immediately after the H4 policy-ROM
  and dwell-inference discussion and before Section 3.12. Because LaTeX numbering
  remains fully automatic, moving it ahead of two later methodology figures changes
  its final number to **Figure 3.2**. Its caption, label
  `fig:training_deployment_flow`, visual content, and source PDF are unchanged.
- **Figure 3.5 was moved to Section 3.13**, immediately after Section 3.13.2's
  topology/phase explanation and before the registered-range table. Automatic source
  ordering changes its final number to **Figure 3.3**. Its caption, label
  `fig:ring6_environment`, panels, routes, phase timeline, and source PDF are
  unchanged.
- **Figure 4.5 was moved to Section 4.9**, after Table 4.6 and its explanatory
  paragraph and before Section 4.10. Automatic source ordering changes its final
  number to **Figure 4.2**. Its caption, label `fig:resource_utilization`, plotted
  values, axes, grayscale shading, and source PDF are unchanged.
- Figure 3.6 remains in Section 3.18. Its caption, labels, placement, evidence
  boundary, and author-provided photograph of the actual Nexys 3 Rev. B board were
  preserved without modification.
- The OpenROAD layout figure remains in Section 4.16 and is no longer visually
  adjacent to the FPGA resource chart. Automatic source ordering changes that
  layout figure from Figure 4.4 to Figure 4.5.

No figure content or caption was edited for this placement correction. No numerical
result, scientific statement, equation, table content, bibliography entry, or
hypothesis outcome was changed.

## Compilation and inspection

- Build sequence: XeLaTeX, BibTeX, XeLaTeX, XeLaTeX.
- Final PDF: 98 A4 pages.
- PDF SHA-256:
  `D12D759AF4E817A8D04A7B840B214A66CD33673B0205E89945F47AEC23CE7263`
- No undefined references, duplicate labels, overfull boxes, or rerun-required
  reference warnings remain in the final log.
- Visual inspection covered the table of contents, List of Figures, Section 3.11
  and the relocated deployment figure, Section 3.13 and the relocated Ring-6 figure,
  Section 3.18 and Figure 3.6, Section 4.9 and the relocated resource figure,
  Section 4.16 and the OpenROAD layout figure, Appendix A.1 and the printed SHA,
  and the affected page transitions.
- The printed SHA is fully visible on Appendix A.1 without clipping or overlap.
