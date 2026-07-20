# P6 Golden-versus-RTL Full Replay Comparison

## Scope

The frozen 84-row replay was executed for all five policy modes, producing
420 result rows in the independent fixed-point golden model and 420 rows in
Icarus Verilog RTL simulation.

Reset boundaries are explicit and deterministic:

- before test 0: Tier A contract start;
- before test 5: P5 H3 contract group;
- before test 10: P5 H4 dwell contract group;
- before test 1000: Tier B held-out start.

These boundaries reproduce the accepted P5 contract grouping while keeping
the 64-row held-out sequence independent.

## Verdict

- Golden rows: 420/420
- RTL rows: 420/420
- Exact field matches: 420/420
- P5 cycle-model regression: 100/100
- Result fields compared:
  `test_id,policy_id,state_id,profile_id,selected_path,score,bottleneck_fidelity,cycles,status`

## Identities

- Golden CSV SHA-256: `6df3c4052a52e662ffb07ad4ee0403e706feabcf2fdb59dd34d909b980fe6ae2`
- RTL CSV SHA-256: `6df3c4052a52e662ffb07ad4ee0403e706feabcf2fdb59dd34d909b980fe6ae2`
- Summary CSV SHA-256: `79a89222b77c594ff307e815ec4cdec17fd5ef01d7c88898b9e3c5c340d28095`
- Generated testbench SHA-256: `8e03e361f2da491139d29434117ac01f449be98336c8df7122fe6fb1dddcdcab`

## Claim boundary

This is golden-model and RTL-simulation evidence. It is not physical
Nexys3 output, physical UART capture, an ISE implementation report or a
programmed-board result. Those remain later P6 gates.
