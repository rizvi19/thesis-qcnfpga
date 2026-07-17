# P3 Step 6 Status: Full Training and Validation Selection

## Outcome

The full eight-candidate matrix completed. Trainer seed 43 is the sole eligible
candidate and therefore passes the frozen validation selection gate. It has
zero validation blocking, uses all four profiles, assigns 30.66% to its
second-most-used profile and has validation switch rate 0.2221, below the 0.25
ceiling. The candidate is selected but not yet policy-frozen.

The other seven candidates are retained as evidence; each failed only the
switch-rate ceiling. No controlled revision was invoked.

## Evidence boundary

This step may claim full offline H4 training and validation-only model
selection. It cannot claim held-out performance, policy freeze, ROM export,
RTL, synthesis, timing or Nexys 3 board behavior.
