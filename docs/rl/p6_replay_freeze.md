# P6 Replay Freeze

The exact same-board replay is frozen at source checkpoint
`224929c385e2199d551b7c692b6673cd695c7daa`.

| Tier | Rows | IDs | Purpose |
|---|---:|---|---|
| A | 20 | 0–19 | Accepted P5 B6 shell-contract coverage |
| B | 64 | 1000–1063 | Held-out dynamic comparison |
| Combined | 84 | A then B | Common H0-H4 order |

Held-out seed: `26072026`

- Contract replay SHA-256: `e72411f9e44442cb94a580b25c11583eba6b7e5be729fec5adfea676075191d6`
- Held-out replay SHA-256: `a4892cb91153820c6b77dccda800c6e5452e24d7e0e19d6307f995f9578dfc07`
- Combined replay SHA-256: `83081e4eb165b887dfdd2c07bd467804f39b78e54e7a9026b4d96007091b07e7`
- Freeze JSON SHA-256: `9702780ea8d5d0cc914384183b530809ecd2dcea9f46955a9d65c68000178281`

The held-out replay has 16 rows each for scarcity, fidelity,
load/imbalance and mixed conditions. Its expected status distribution is
58 successful, 4 no-path and 2 invalid requests.

This checkpoint proves replay materialization, schema correctness, class
balance and byte identity only. Golden results, RTL comparison, ISE
implementation, UART capture and physical board outputs remain later gates.
