# P3 Step 7 Status: Frozen Held-Out Evaluation

## Required outcome

The selected seed-229 Q-table and policy, balance-weight-4 training contract and
three-decision dwell controller are frozen before any test trace is generated.
The four untouched test seeds are then evaluated exactly once per H2, H3 and
H4 controller using shared trace bytes.

## Evidence

`results/rl/p3_policy_freeze/` contains the immutable selected artifacts,
freeze record, test unlock and checksums. `results/rl/p3_heldout/` contains 12
per-trace controller rows, controller summaries, profile usage, the H4 action
timeline, test-trace hashes, access manifest and checksums.

## Next gate

Step 8 must calculate the predeclared paired statistics and decide the complete
utility gate. Step 7 does not authorize policy revision or P4.
