# P2 Forced-Balanced Regression Gate

## Gate interpretation

The P2 exit criterion that a forced-fixed environment reproduces H2 is checked
at the shared deterministic computation boundary. Action `0` resolves to the
frozen Balanced profile, and the profile adapter must produce canonical JSON
that is byte-identical to the legacy H2 result. Balanced route selection must
also preserve the legacy first Pareto route on the canonical H2 run.

The trace-driven Ring-6 environment has a different workload and key-capacity
model from the legacy stochastic H2 experiment. Therefore this gate does not
claim that their complete dynamic trajectories are byte-identical. Such a
claim would compare different experiment contracts.

## Action clamp

The environment regression runner exposes no policy choice. It supplies action
`0` at every transition and rejects any internal escape from action `0` or the
`balanced` profile. It replays the eight-step manual trace and all 16 frozen
train, validation and test traces through terminal completion. Repeated evidence
generation must be byte-identical.

## Edge coverage

The regression tests cover:

- exact canonical H2 hash and JSON equivalence;
- canonical H2 route-selection parity;
- one feasible clockwise or counter-clockwise route;
- deterministic tie-breaking when both routes are equal;
- blocking caused independently by empty keys, low fidelity or zero key rate;
- fidelity exactly at the feasibility floor;
- invalid actions and malformed traces without state advancement;
- reset, terminal-state and reward-decomposition behavior; and
- forced-Balanced replay over every frozen partition trace.

This is regression evidence only. No Q-learning, policy optimization, board
measurement or adaptive-performance claim is part of Step 7.
