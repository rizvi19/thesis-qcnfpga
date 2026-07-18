# P4 Step 2 Status

Step 2 freezes the controller's state representation, state-ID packing,
policy/profile ROM contracts, dwell behavior, handshake, exceptional behavior,
golden-vector schema and claim firewall.

The authoritative machine-readable sources are
`rl/config/p4_rtl_contract_v1.json` and
`sim/rl/p4_golden_vector_schema.json`. Completion requires the controlled local
installer to run the new contract test together with applicable P2/P3 tests,
produce `results/rl/p4_contract`, and leave only the reviewed Step 2 scope
untracked. No RTL module is created in Step 2.
