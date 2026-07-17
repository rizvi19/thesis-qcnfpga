# P2 MDP Contract

## Scope

The defense controller is a bounded tabular MDP. It selects one of the four
P2 coefficient profiles; it does not learn a route directly and does not alter
physical fiber attenuation or the effective key-generation model.

The machine-readable source of truth is `rl/config/mdp_v0.yaml`. It uses the
JSON-compatible subset of YAML so it can be validated with the Python standard
library without adding a PyYAML dependency.

## State

Four features are quantized into four bins each, producing exactly 256 states:

1. minimum normalized key occupancy;
2. bottleneck fidelity;
3. normalized offered request load; and
4. link-utilization imbalance.

The bin order is fixed and state IDs use radix-4 encoding. Equality at a bin
threshold enters the higher bin. Inputs outside the documented physical or
normalized range are clipped; non-finite values are rejected.

For the defense Ring-6 environment, each link has a 16-key logical capacity,
offered load is normalized to four requests per control window, and utilization
uses a 16-step sliding consumption window. These constants make the feature
calculation reproducible and map naturally to small counters in later RTL.

## Action

Actions 0 through 3 map exactly to Balanced, Scarcity protection, Fidelity
protection and Low-latency in `profile_codebook_v0.json`. Expanding beyond four
actions is prohibited during P2.

## Transition order

The environment observes the state, selects a profile, attempts routing,
consumes one key on every selected link after success, applies the next trace
arrival/fidelity update, advances the trace and then observes the next state.

A no-path event is a blocked step but is not automatically terminal. An
episode terminates only when the final trace record has been advanced.

## Reward

Every reward component is logged separately:

- success: `+4`;
- blocking: `-4`;
- normalized fidelity utility: up to `+2`;
- balance utility: up to `+1`;
- hop cost: `-0.25` per selected edge; and
- profile switch cost: `-0.25`.

The nominal one-step range is `[-4.25, 6.75]`. A blocked step receives only
the blocking term and, when applicable, the switch term.

## Trace separation

Training, validation and test seeds are frozen and pairwise disjoint before P3
begins. Each trace has 512 decisions on Ring-6. Sensitivity fixtures from Step
4 are not training, validation or test traces.

## Deployment boundary

P3 may train tabular Q-learning offline. The defense deployment must use a
frozen Q table or policy ROM. DQN is excluded from P2 and from the defense
critical path.
