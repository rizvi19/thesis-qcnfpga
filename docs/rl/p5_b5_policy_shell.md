# P5 Step 7 / B5 H0-H4 Policy Shell

The B5 shell provides one compile-time `POLICY_MODE` boundary over the common
Ring-6 candidate representation and B4 evaluator.

- H0 selects the feasible candidate with the fewest hops, then the lowest slot.
- H1 uses the common B4 evaluator with cost-only lambda `(1,0,0)`.
- H2 forces frozen profile 0.
- H3 implements the P3 first-match rules exactly:
  key bin 0 -> profile 1; fidelity bin 0/1 -> profile 2;
  imbalance bin 2/3 -> profile 1; safe saturated-load case -> profile 3;
  otherwise profile 0.
- H4 instantiates the accepted P4 state encoder, policy ROM, profile ROM and
  three-decision dwell controller without retraining or on-chip Q update.

All modes expose policy ID, state ID, profile ID, route status, selected slot,
score and bottleneck fidelity. The `cycles` field is present but marked invalid
in B5; P5 Step 8/B6 replaces it with the accepted-edge-to-done kernel counter.
UART serialization is outside the kernel latency boundary.
