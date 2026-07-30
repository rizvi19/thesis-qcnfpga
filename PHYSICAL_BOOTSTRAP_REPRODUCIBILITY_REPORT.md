# Physical Bootstrap Reproducibility Report

## Inputs

The row-level physical results are available at evidence commit
`290b4ad75eef2af2b9da2f1f281a2b89416cfd24`:

- H2: `results/nexys3/p6_step6_h2_physical/board_results.csv`
- H3: `results/nexys3/p6_step7_h3_physical/board_results.csv`
- H4: `results/nexys3/p6_step8_h4_physical/board_results.csv`

Their SHA-256 values are written into `data/physical_bootstrap_recomputed.csv`.

## Declared method

- Comparisons: H4-H2 and H4-H3.
- Sampling unit: one jointly successful held-out replay row.
- Held-out IDs: 1000 through 1063 inclusive.
- Pair count: 58 for each comparison after requiring status 0 in both modes.
- Difference: H4 route-quality code minus baseline route-quality code, in UNORM16
  units.
- Bootstrap: paired nonparametric row resampling with replacement.
- Replicates: 10,000.
- RNG: Python `random.Random`, MT19937.
- Seed: 20260731, reinitialized to the same value for each planned comparison.
- Interval: percentile 95% interval using the 2.5th and 97.5th quantiles with linear
  interpolation at `p * (B - 1)` (R-7 convention).
- Sign test: exact two-sided binomial test over nonzero differences; ties excluded.
- Effect: paired mean difference divided by the sample standard deviation of the
  row-level paired differences.

No seed or method was chosen in response to an outcome.

## Recomputed results

| Comparison | Pairs | Mean | 95% bootstrap CI | Sign p | dz | Path changes |
|---|---:|---:|---:|---:|---:|---:|
| H4-H2 | 58 | 86.465517 | [-25.120690, 226.620690] | 0.218750 | 0.176084 | 6 |
| H4-H3 | 58 | -78.051724 | [-242.281466, 77.534483] | 0.453125 | -0.126716 | 7 |

Both intervals cross zero. The scientific conclusion is unchanged: the physical
comparisons do not establish route-quality superiority for H4.

## Preserved executable and outputs

- `reproduce_physical_bootstrap.py`
- `data/physical_paired_differences.csv`
- `data/physical_bootstrap_recomputed.csv`

Run from the repository root with:

```powershell
python reproduce_physical_bootstrap.py
```

The script reads the immutable CSV blobs directly with `git show`, verifies that
each comparison has 58 eligible pairs, reproduces means, intervals, sign tests,
paired effects, and path-change counts, and records source hashes and all method
parameters in its summary output.

## Thesis updates

Chapter 3 now declares the complete resampling procedure. Chapter 4 Table 4.8 and
Figure 4.3, Appendix C, the numerical traceability file, and the discussion use the
recomputed endpoints. The exact sign-test p-values, effect sizes, means, pair counts,
and qualitative conclusion are preserved.
