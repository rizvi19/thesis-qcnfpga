# P3 Controlled Revision: Balance-Weighted Training and Minimum Dwell

## Trigger and diagnosis

The raw Step 6 result was safe but not cleanly superior. Seed 43 was the only
candidate below the 0.25 switch ceiling; its reward was below H2 and H3, and
its balance utility was more than 0.05 below H3. Test access remained zero.

Two related deficiencies were identified. First, the v0 reward's switch term
depends on the previous profile even though the 256-state observation omits
that history. Second, balance had insufficient influence on learned action
selection relative to the predeclared balance-degradation gate.

## Single controlled revision

The one permitted revision freezes a single v1 controller configuration before
the complete revised eight-seed matrix:

- training targets use balance weight 4.0; every other reward term is unchanged;
- reported validation and later held-out reward remains the original v0 reward;
- inference applies a deterministic three-decision minimum-dwell guard;
- all eight original trainer seeds receive the same 200-epoch budget;
- selection remains eligibility first and then the frozen lexicographic rank.

This is one combined reward/controller revision addressing the two observed
validation failures. No additional revision is allowed.

## Boundary

The original Step 6 evidence remains intact. The revised run accesses training
and validation traces only. It does not open the test partition, freeze the
final policy, export ROMs, implement RTL, synthesize, use the board, commit or
push. A validation pass authorizes Step 7 policy/controller freeze and exactly
one untouched held-out evaluation; it does not establish test superiority.
