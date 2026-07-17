# P2 Status: Profile Codebook and RL Environment

## Outcome

P2 implementation and verification are complete. The formal exit gate is
`PASS`; the guarded checkpoint commit and push remain pending Step 10. P3 is
not authorized before that checkpoint is reviewed.

## Frozen design

- Four actions: Balanced, Scarcity protection, Fidelity protection and
  Low-latency.
- Four state features with four bins each, producing 256 state IDs.
- Deterministic 512-step traces with 8 train, 4 validation and 4 test seeds.
- Decomposed reward with success, blocking, fidelity, balance, hop and profile
  switch components.
- Offline tabular Q-learning remains the P3 plan; no training occurred in P2.

## Verified results

- The forced-Balanced adapter is canonical-JSON byte-identical to H2 hash
  `e4a393bc349f064ab7709e75fe6093210cf05f6f842fee33d4cc5b0adbcdaf3f`.
- The manual trace completes 8 of 8 transitions, and all 16 frozen traces
  complete 8,192 forced-Balanced transitions deterministically.
- All profile alphas have exact one-fractional-bit encodings; all Tchebycheff
  weights equal primitive integer ratios.
- Integer-ratio scoring matches floating scoring in all 24 audited decisions.
- The four-profile coefficient payload is 72 bits and needs no generic
  profile-coefficient multiplier.
- The final Step 9 run contains 26 passing legacy tests and 72 passing P2 tests.

## Evidence boundary

P2 evidence is Python/reference-model evidence. It does not claim learned-policy
performance, RTL implementation, synthesis, timing, board measurements or
online FPGA learning. Those claims require later controlled phases.
