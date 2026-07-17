# P3 Policy Freeze and Untouched Held-Out Evaluation

## Ordering invariant

Step 7 first copies and checksums the selected seed-229 Q-table, policy and v1
training configuration. It writes a freeze record that binds balance weight 4,
minimum dwell 3, the Step 6R selection, and the semantic policy/Q-table hashes.
Only after that record is verified does `test_unlock.json` authorize the four
predeclared test seeds. No post-unlock revision is allowed.

## Test access

The four test traces are generated once after unlock and reused across H2, H3
and H4, producing 12 controller-trace evaluations. The H4 deployed-action
timeline is also retained. No statistics, utility decision, ROM export, RTL,
synthesis or board work occurs in Step 7.

## Interpretation boundary

The held-out means are descriptive until Step 8 applies the frozen paired
bootstrap, exact paired permutation tests, effect sizes, Holm correction and
complete utility gate. Regardless of the test outcome, the policy, controller
and training configuration cannot be changed after this step.
