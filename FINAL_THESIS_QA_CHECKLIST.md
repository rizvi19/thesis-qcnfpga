# Final Thesis QA Checklist

## Scientific scope

- [x] The valid classical key-resource model is presented from the beginning.
- [x] No stored-classical-key quantum-fidelity-decay claim remains in the research model.
- [x] QFlow is consistently a route-candidate evaluator, not a complete graph router.
- [x] Candidate generation, KMS/SDN orchestration, policy enforcement, and route
  installation remain outside the accelerator.
- [x] Offline training and deterministic on-FPGA inference are distinguished.
- [x] No online FPGA Q-value update is claimed.
- [x] Measured, post-route, physical replay, RTL/software simulation, analytical, and
  supporting physical-design evidence are distinguished.
- [x] No CPU speedup, CPU/FPGA energy comparison, FPGA power, or commercial cost is invented.
- [x] No complete ASIC, fabricated silicon, tapeout, or full-chip signoff is claimed.
- [x] Route-quality neutrality and the non-support of RH5 remain visible.

## Notation and terminology

- [x] H0–H4 are explicitly defined as hardware evaluation configurations.
- [x] RH1–RH5 are exclusively research hypotheses.
- [x] Profiles use Pi_0–Pi_3 in rendered mathematical notation.
- [x] Route candidates use calligraphic R_i notation.
- [x] P0–P6 milestone wording is absent from the main research narrative.
- [x] The appendix contains one neutral note on repository P-label path prefixes.
- [x] Alpha/lambda meanings are qualified and included in the List of Symbols.
- [x] Nexys 3, Spartan-6, fixed-point, post-route, and route-candidate evaluation are
  consistently styled.

## Front matter and structure

- [x] Title, author, roll, department, university, supervisor, and August 2026 date verified.
- [x] Acknowledgement is professional and free of development-history narrative.
- [x] Certificate uses a conventional unsigned external-examiner line.
- [x] Declaration is a conventional academic declaration.
- [x] Abstract is approximately 369 words and contains the required scope/method/results.
- [x] Contents, List of Tables, List of Figures, abbreviations, and symbols render correctly.
- [x] Chapters are Introduction; Background and Literature Review; Methodology; Results and
  Discussion; and Conclusion and Future Work.
- [x] Claim ledger/defense script/project-repair appendix material was removed.

## Results and discussion

- [x] 420 records, 3,780 fields, zero mismatches, and five >100 MHz builds verified.
- [x] H4 102.020 MHz, 2.048 microseconds, and resource values verified.
- [x] All H4/H3 percentages recalculate to the source values.
- [x] Transition reduction is attributed to the complete policy-and-dwell controller.
- [x] p-values and confidence intervals are correctly interpreted as non-significant.
- [x] Practical Deployment Scenario confines latency to the kernel boundary.
- [x] Platform Selection and Cost Implications includes CPU/FPGA/ASIC roles and cost model.
- [x] Related-work comparison avoids invalid cross-function speedup claims.
- [x] VLSI areas are separate isolated-kernel values with correct square-micrometre units.

## References

- [x] 26 bibliography entries and 26 unique cited keys.
- [x] Every citation resolves to a bibliography entry.
- [x] Every bibliography entry is used in the thesis.
- [x] Author/title/venue/year/DOI metadata reconciled with the repository literature audit.
- [x] Recent representative records spot-checked on official publisher pages.

## LaTeX and PDF

- [x] XeLaTeX/BibTeX build exits successfully.
- [x] No fatal errors.
- [x] No undefined references or citations.
- [x] No missing files or glyphs.
- [x] No overfull boxes.
- [x] Final PDF is 68 A4 pages and opens with Poppler.
- [x] All 68 pages rendered successfully.
- [x] Contact-sheet inspection covers every page.
- [x] Larger-scale checks cover front matter, dense tables/figures, appendices, and references.
- [x] Page numbering, margins, headers, captions, and chapter starts follow the template.

## Submission artifacts

- [x] Complete revised LaTeX source present.
- [x] `document.pdf` present.
- [x] Submission-named PDF under `output/pdf/` present.
- [x] Revision summary present.
- [x] Numerical audit present.
- [x] Compile log present.
- [x] QA checklist present.
- [x] Git diff summary present.
- [x] Branch is `thesis-final-submission-polish`.

## Author-only administrative status

- [x] No unresolved prose placeholder remains.
- [x] External examiner information was not provided; the certificate therefore retains the
  institutional blank signature/name line without placeholder prose.
