# P3 Step 2 Status: Experiment Contract Freeze

## Outcome

The P3 experiment contract is frozen before H3 implementation or H4 training.
The controller matrix, tabular Q-learning equation and hyperparameters,
trainer RNG seeds, H3 priority rules, model-selection rule, metrics,
statistical procedure, safety margins, oscillation limit, one-revision policy
and test-partition lock are all predeclared.

## Boundaries

- No H3/H4 result is claimed.
- No training or test-partition access has occurred.
- No RTL, synthesis or board work is authorized.
- No DQN, eight-action training or on-chip learning is authorized.
- The working branch remains `rl-nexys3-adaptive` on the completed P2 base.

## Step 2 exit evidence

`results/rl/p3_contract/contract_validation.json` verifies the P2 anchors,
partition identity and separation, H3 rule coverage, training budget, fixed
statistics and test lock. `results/rl/p3_contract/SHA256SUMS` freezes all Step 2
contract artifacts. Passing Step 2 authorizes baseline/trainer implementation,
not training and not P4.
