# P5 Step 6 / B4 Candidate Evaluator

This bounded hardware block evaluates the two valid frozen Ring-6 candidate slots. Upstream path/edge logic supplies a feasibility bit and the three objective values for each candidate. B4 performs the frozen range normalization, profile-weighted minimax score and deterministic ranking `(score, path_cost, hop_count, slot)`.

The implementation uses one 49-by-33-bit iterative unsigned divider, shared across all nonzero objective ranges. With no feasible candidate it asserts `no_path` and suppresses `route_valid`. With one feasible candidate all normalized objectives and its score are zero.

Board self-test signature: display `B410`; LD0 heartbeat; LD1 pass; LD2 fail; LD3 completion. The center button restarts the test. The input constraint at B8 intentionally has no internal `PULLDOWN`, matching the Step-3 board repair.
