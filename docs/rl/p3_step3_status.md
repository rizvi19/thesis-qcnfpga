# P3 Step 3 Status: H2/H3 Baselines

## Exit requirements

- H2 is forced to action 0 for every state.
- H3 is deterministic, implements the frozen priority rules and can emit all
  four profiles.
- Train and validation traces are replayed identically for H2 and H3.
- Test seeds are rejected by the baseline evaluator.
- Per-seed metrics and aggregate profile usage are deterministic and
  checksummed.
- P2 anchors and the P3 Step 2 contract remain unchanged.
- No H4 training, RTL, synthesis, board access, commit or push occurs.

Passing this step authorizes deterministic Q-learning implementation and unit
testing. It does not authorize full H4 training or test-partition evaluation.

## Recorded baseline observation

On the validation partition, H2 and H3 both have zero blocking. H3 has slightly
higher mean total reward, successful fidelity and balance utility than H2, but
also more hops and a switch rate near 0.282. That switching exceeds the 0.25
ceiling predeclared for an eligible H4 policy. The H3 result is retained without
post-result rule tuning; it is an honest, comparatively strong but
switch-intensive non-learning baseline that H4 must address.
