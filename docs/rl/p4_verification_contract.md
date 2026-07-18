# P4 Verification Contract

## Required ladder

Verification proceeds from frozen Python state/policy/profile behavior to
exported memories, RTL units, integrated controller simulation and finally ISE
synthesis. Step 2 freezes schemas and executable contract tests; it does not
claim RTL or synthesis completion.

## Exact comparisons

- Every state ID 0 through 255 must map to the exact exported action.
- Every action 0 through 3 must map to the exact 18-bit profile payload.
- All twelve encoded threshold edges require below, equal and above cases.
- Equality must enter the higher bin.
- Reset, valid request, invalid request, busy stall, no-path status and
  back-to-back transaction timelines must match cycle-for-cycle.
- Dwell timelines must match the frozen Python controller for minimum dwell 3.
- No unexplained state, action, payload, handshake or status mismatch is allowed.

## Golden-vector schema

`sim/rl/p4_golden_vector_schema.json` is the machine-readable column and
category authority. Later steps generate CSV vectors using only those columns.
Each case contains its input cycle and every expected observable output.

The exhaustive state-to-profile gate is not satisfied by a checksum alone. It
must contain 256 explicit state cases and exact policy/profile comparisons.

## Exceptional behavior

An invalid request completes with invalid status but does not update dwell.
Starts while busy are rejected and reported as stalls. No-path is a status
result, not an early terminal condition and not a reason to suppress profile
selection.

## Evidence and claims

Step 2 tests must preserve the P3 policy and export hashes. Generated evidence
is stored under `results/rl/p4_contract`. This phase cannot claim RTL
completion, synthesis, timing closure, resource use, measured power, board
deployment, online learning or formal statistical superiority.
