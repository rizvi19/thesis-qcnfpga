# P2 Deterministic Ring-6 Environment

## Purpose

This environment implements the frozen P2 transition order without starting
Q-learning. An action selects one of the four coefficient profiles; route
selection remains a QFlow path decision using normalized Tchebycheff scoring.

## Deterministic traces

The trace generator uses an explicit 32-bit xorshift recurrence rather than a
library random-number generator. Therefore the trace byte stream is independent
of NumPy and Python random-module versions. Every frozen train, validation and
test seed has a canonical SHA-256 entry in the environment evidence manifest.

The eight-record manual trace is intentionally small enough to inspect. It
cycles through scarcity, fidelity, low-latency, mixed and nominal conditions
and replays actions 0, 1, 2 and 3 twice.

## Atomic step order

For each trace record, the environment:

1. encodes the current 256-state observation;
2. validates and applies the selected profile action;
3. enumerates both simple Ring-6 directions;
4. filters paths with empty key pools or fidelity below `0.90`;
5. selects a feasible route or records a blocked request;
6. consumes one key from every selected directed link;
7. updates the 16-step consumption history and calculates reward components;
8. applies exogenous arrivals, fidelity, key-rate and QBER updates;
9. advances the trace index; and
10. encodes the next state unless the episode is complete.

The selected-path update is atomic. Key consumption occurs before arrivals,
which is verified by an explicit one-key test.

## Evidence boundary

Generated traces and the manual replay are deterministic software evidence.
They are not training results, board measurements or claims that H4 improves
network utility. P3 may begin only after the full P2 exit gate is complete.
