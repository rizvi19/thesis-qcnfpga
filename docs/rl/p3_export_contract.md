# P3 Step 9 Frozen Export Contract

## Deployment artifacts

The frozen seed-229 policy is exported as 256 state-major hexadecimal profile
IDs with two useful bits per word. The policy ROM, not the Q-table, is the
deployed decision artifact.

The audit Q-table is exported as 1,024 state-major/action-minor signed 16-bit
two's-complement Q8.7 words. Round-half-away-from-zero quantization must remain
within half an LSB and the quantized argmax policy must match all 256 frozen
policy entries.

Each profile is an 18-bit payload stored in five hexadecimal digits. From MSB
to LSB it contains four three-bit alpha numerators with one implicit fractional
bit and three two-bit primitive Tchebycheff ratios. All four payloads must
roundtrip to the P2 codebook and retain the audited 72-bit total.

## Model and evidence freeze

The model card records intended use, training/selection history, held-out
metrics, statistical claim boundary, ROM formats and limitations. The complete
P3 evidence manifest records path, byte count and SHA-256 for every controlled
P3 file outside the self-referential exit directory.

The Step 9 exit decision is `PASS_PENDING_STEP_10_CHECKPOINT`. P4 authorization
becomes operational only after Step 10 verifies, commits and non-force pushes
the exact checkpoint.

## Scope firewall

Step 9 performs no learning, policy revision, new test access, RTL, synthesis,
board work, commit or push.
