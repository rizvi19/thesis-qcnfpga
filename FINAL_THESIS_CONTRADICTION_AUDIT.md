# Final Thesis Contradiction Audit

## Result

The corrected LaTeX source was searched across all chapters and appendices for the
terms required by the submission brief. No unresolved scientific contradiction was
found in the checked categories.

## Checked decisions

| Topic | Final consistent statement |
|---|---|
| H0 | Feasible minimum-hop baseline; valid candidate with the fewest hops, slot tie-break |
| Equation 3.10 | Reciprocal K, Q, and R terms plus direct QBER term, matching software |
| Eligibility | Upstream KMS/SDN computes route eligibility; FPGA gates supplied validity |
| Training action | Four alpha coefficients construct cost; three ratios weight objectives |
| Physical action | Ratio-only projection over supplied, profile-independent path cost |
| Physical exactness | Proves agreement with the ratio-only reference contract only |
| Path-cost UQ16.16 | `0xFFFFFFFF` infinity; finite max `0xFFFFFFFE = 2^16 - 2^-15` |
| Utilization UQ16.16 | Full unsigned range; `0xFFFFFFFF = 2^16 - 2^-16`, not infinity |
| Pi1 | Strongest deployed arithmetic emphasis is utilization |
| Pi2 | Strongest deployed arithmetic emphasis is route-quality deficit |
| Pi3 | Strongest deployed arithmetic emphasis is supplied path cost, not FPGA cycles |
| Bootstrap | 10,000 paired-row percentile replicates, seed 20260731, R-7 quantiles |
| Route quality | Both recomputed intervals cross zero; superiority is not established |
| FPGA/ASIC | Five physical FPGA builds; VLSI results remain isolated kernels, not an ASIC |

## Search terms

The source search covered: `shortest distance`, `shortest-distance`, `minimum hop`,
`path cost`, `distance`, `alpha`, `route quality`, `fidelity`, `replenishment`, `key
rate`, `hard eligibility`, `valid candidate`, `profile semantics`, `low latency`,
`UQ16.16`, `0xFFFFFFFF`, `infinity`, `audit`, `revision`, `bootstrap`, `thesis
commit`, `branch`, and FPGA/ASIC statements.

Legitimate uses of “distance” remain for fibre/path distance or timing-edge
distance, not as H0's selection field. “Audit” remains only in external artifact
paths or security audit logging. “Fidelity” remains where it is an artifact field,
registered profile name, or cited quantum-network concept; the thesis explicitly
distinguishes these from classical stored-key coherence.

## Preserved headline evidence

The pass preserves five H0--H4 implementations, all above 100 MHz, 420 physical
records, 3,780 checked fields, zero mismatches, H4 at 102.020 MHz and approximately
2.048 microseconds, 44 versus 24 H3/H4 transitions, p-values 0.2188 and 0.4531,
RH1--RH4 supported, RH5 not supported, and the absence of measured CPU speedup,
calibrated FPGA power, integrated ASIC, or live KMS/SDN claims.

Compilation and page-render checks are recorded separately in
`FINAL_THESIS_COMPILE_LOG.txt` and `FINAL_THESIS_QA_CHECKLIST.md`.
