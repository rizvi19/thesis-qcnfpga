# P3 Full H4 Training and Validation Selection

## Controlled matrix

P3 Step 6 trains eight independent tabular Q-learning candidates using trainer
seeds 17, 29, 43, 71, 113, 167, 229 and 283. Every candidate runs the frozen
200 epochs over all eight train traces, totaling 819,200 transitions per
candidate and 6,553,600 training transitions overall.

Only the final epoch-200 policy is eligible. Each fixed policy is evaluated on
the four validation traces. The test partition remains locked and is not read.

## Frozen eligibility and ranking

A candidate must use at least two profiles, allocate at least 1% to its
second-most-used profile, remain within the 0.005 absolute blocking margin and
have validation switch rate no greater than 0.25. Eligible candidates are
ranked by validation reward, blocking, fidelity, switch rate and trainer seed
in the predeclared order.

If no candidate is eligible, the result is `REVISION_REQUIRED`. A provisional
safety-first candidate is recorded for diagnosis, but no policy is frozen and
the test partition remains locked. The single permitted controlled revision
must receive a new configuration version and checksum.
