# Final Thesis Revision Summary

## Submission identity

- Thesis: *QFlow: A Fixed-Point FPGA Accelerator for Adaptive Key-Resource-Aware
  Route-Candidate Evaluation in Trusted-Relay QKD Networks*
- Author: Shahriar Rizvi (Roll 2003104)
- Department: Computer Science & Engineering, RUET
- Submission branch: `thesis-final-submission-corrections`
- Exact thesis-source commit:
  `575a64b19a2a583a7e31e9092c05c9991c24cc76`

## Revision outcome

The final 92-page thesis now gives one consistent account of the software model,
fixed-point implementation, physical replay, and supporting VLSI work. It explicitly
separates the complete offline-training action—four alpha coefficients plus three
Tchebycheff ratios—from the physical H2-H4 ratio-only projection over supplied,
profile-independent path costs. Physical exactness is therefore claimed only for the
implemented projection.

Equation 3.10 retains the implementation-supported reciprocal form and now defines
units, infeasible denominators, fixed-point rounding, infinity, and finite saturation.
Eligibility is computed upstream and represented at the FPGA by a supplied validity
bit. H0 is consistently a feasible minimum-hop baseline. Path-cost and utilization
encodings no longer share an incorrect sentinel interpretation.

The physical row-level data were recovered from the primary evidence commit and a
deterministic paired bootstrap was added. Both 95% intervals cross zero, preserving the
neutral route-quality conclusion. The script, paired differences, summary CSV, seed,
RNG, resampling unit, replicate count, and percentile convention are now archived.

The Abstract fits one page and reports the system boundary, H0-H4, exactness, timing,
adaptive behavior, neutral statistics, and principal limitations. Sparse continuation
pages were removed without deleting technical substance. The supporting OpenROAD
results remain explicitly limited to isolated kernels.

## Final release

- Root PDF: `document.pdf`
- Packaged PDF: `output/pdf/QFlow_Thesis_VLSI_Integrated.pdf`
- Pages: 92 A4
- PDF SHA-256:
  `2AD29C8FA49776CE55B7D1A6A4C9F708127411624AE358B75E16C0DBD14899CC`
- Bibliography records: 41
- Undefined references/citations: 0
- Overfull boxes: 0
- Non-embedded fonts: 0
- Rendered and visually inspected pages: 92

Detailed handoff evidence is in
`FINAL_THESIS_SOURCE_AVAILABILITY_REPORT.md`,
`PROFILE_TRAINING_DEPLOYMENT_SEMANTICS_REPORT.md`,
`PHYSICAL_BOOTSTRAP_REPRODUCIBILITY_REPORT.md`,
`FINAL_MATHEMATICAL_CORRECTION_REPORT.md`,
`FINAL_THESIS_NUMERICAL_TRACEABILITY.md`, and
`FINAL_THESIS_COMPILE_LOG.txt`.
