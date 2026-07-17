# P3 Test-Partition Lock

## Locked partition

The four final held-out Ring-6 traces are seeds 2003, 2111, 2203 and 2309. At
the P3 Step 2 freeze, their access count is zero. They must not be evaluated,
summarized, plotted or used for model selection while H3 rules, H4 training,
reward, state, hyperparameters or candidate selection remain changeable.

## Unlock conditions

The test runner may be authorized only after all of the following exist:

1. every predeclared training run is complete;
2. one candidate is selected using training and validation data only;
3. `training_config.yaml` has a frozen checksum;
4. the selected Q-table and derived policy have frozen checksums; and
5. the selection record is written before any test evaluation.

The unlock record will be
`results/rl/p3_policy_freeze/test_unlock.json`. It must identify the exact Git
state and input checksums and record a pre-evaluation test access count of zero.

## After unlock

The test partition is evaluated once for H2, H3 and the frozen H4 policy on
identical traces. A poor test result cannot trigger retraining, reselection or a
reward/state change. It is reported as the honest held-out result. Additional
journal robustness traces, if later created, receive new identifiers and do not
retroactively alter this defense test.
