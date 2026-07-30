# QFlow RUET Thesis — Final Submission Package

This directory contains the final B.Sc. thesis source and compiled PDF. The document
uses the supplied RUET CSE thesis template, with A4 geometry, Times-family body text,
12-point type, 1.5-line spacing, Roman-numbered front matter, and the required chapter
structure.

## Compile locally

1. Use `document.tex` as the main file.
2. Compile with XeLaTeX and BibTeX:
   - `xelatex document.tex`
   - `bibtex document`
   - `xelatex document.tex`
   - `xelatex document.tex`
3. The final PDF is `document.pdf`; a submission-named copy is stored under
   `output/pdf/`.

For Overleaf, upload the complete source package, select `document.tex` as the main
document, and choose XeLaTeX as the compiler. Overleaf runs the required bibliography
passes automatically.

## Thesis identity

- Title: *QFlow: A Fixed-Point FPGA Accelerator for Adaptive Key-Resource-Aware
  Route-Candidate Evaluation in Trusted-Relay QKD Networks*
- Author: Shahriar Rizvi
- Roll: 2003104
- Supervisor: Dr. Md. Nazrul Islam Mondal
- Submission: August 2026

The external examiner field is presented as a conventional signature-and-name line on
the certificate page, with no fill-in instruction in the printed document.

## Reproducibility boundary

The learned controller is trained offline and deployed on the FPGA as deterministic
policy-ROM inference with minimum-dwell control. The principal physical evidence is a
same-board campaign of 420 records across hardware configurations H0--H4, comprising
3,780 checked fields with zero physical/reference mismatch. Each implementation exceeds
100 MHz after place and route. Supporting VLSI results concern isolated kernels and are
reported separately from the integrated FPGA system.

Appendix A records the exact evidence branches, commits, source artifacts, tool versions,
and build commands. Appendix D states the experimental scope and the limits of the
claims.
