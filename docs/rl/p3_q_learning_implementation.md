# P3 Tabular Q-Learning Implementation

## Scope

P3 Step 4 implements the frozen H4 learner mechanics without running a frozen
training trace. The implementation is an offline 256-state by four-action
tabular controller. It does not include DQN, neural inference, online FPGA
learning, RTL, synthesis or board work.

## Deterministic mechanics

- The Q-table contains 256 rows and four actions and initializes to zero.
- Trainer randomness uses explicit 32-bit xorshift with nonzero frozen seeds.
- Training traces can be ordered by unbiased xorshift32 Fisher-Yates shuffle.
- Epsilon is 1.0 at the first decision, reaches 0.05 at the last decision in
  the first `ceil(0.8 * T)` decisions and remains 0.05 afterward.
- Exploration is uniform over all four actions.
- Greedy ties during training are uniform over the maximizing actions using the
  same trainer RNG. Evaluation and deployment choose the smallest action ID.
- The update is `Q <- Q + 0.1 * (reward + 0.95 * bootstrap - Q)`.
- Terminal transitions use exactly zero bootstrap and no next-state ID.

## Step boundary

The unit audit uses only constants and synthetic micro-transitions. It records
zero training-trace, validation and test access. It does not execute the fixed
819,200-transition H4 budget. Controlled training orchestration and a training
smoke run are deferred to P3 Step 5.
