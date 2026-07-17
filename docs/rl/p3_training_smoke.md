# P3 Deterministic Training Smoke

## Purpose

P3 Step 5 exercises the real Ring-6 environment, frozen four-action profile
codebook and deterministic tabular learner before the expensive candidate
matrix is authorized. The smoke uses the train partition only.

## Frozen smoke budget

- Environment seeds: all eight frozen training seeds.
- Trainer RNG seeds: 17 and 29.
- Epochs per candidate: two.
- Transitions per candidate: 8,192.
- Fraction of the full per-candidate budget: 1%.

The evidence records learning curves, action counts, state coverage, Q-value
bounds and hashes of the in-memory Q-table and extracted policy. The same
trainer seed must reproduce byte-identical evidence, while the second frozen
trainer seed must produce a distinct learned Q-table.

## Evidence boundary

This is not the full H4 experiment and cannot support performance or
convergence claims. Validation and test access remain zero. No candidate is
selected, no policy is frozen, no ROM is exported and no RTL, synthesis or
board work is performed.
