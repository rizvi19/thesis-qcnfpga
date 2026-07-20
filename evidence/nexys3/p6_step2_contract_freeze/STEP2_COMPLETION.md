# P6 Step 2 — Same-Board Experiment Contract Freeze

## Status

- Source branch: `rl-nexys3-adaptive`
- Source checkpoint: `e701dfa15d01938d85b281ab38bd07f6368d37e4`
- Contract version: 1
- Independent modes frozen: H0, H1, H2, H3, H4
- Build tags frozen: `n3_h0`, `n3_h1`, `n3_h2`, `n3_h3`, `n3_h4`
- Physical board clock: 100 MHz
- Physical clock period: 10 ns
- P5 contract replay: 20 ordered cases
- P6 held-out dynamic replay: 64 rows
- Held-out seed: `26072026`
- Board result schema: exact pass
- Authority hashes: 11/11 pass
- Contract validator: pass
- FPGA programming: none
- ISE build: none
- UART access: none
- EEPROM access: none

## Frozen board result fields

`test_id,policy_id,state_id,profile_id,selected_path,score,bottleneck_fidelity,cycles,status`

## Next gate

P6 Step 3 must materialize and hash the exact replay, generate golden results,
and validate the physical result transport before any H0-H4 implementation
campaign begins.
