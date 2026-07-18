# P4 RTL Contract Freeze

## Authority and scope

This contract consumes the frozen P3 checkpoint
`cdfeda3f5f2fca586546ef6e362ac451512d75bc`. It authorizes deterministic
learned-policy inference only. It does not authorize retraining, Q-table
argmax deployment, online Q updates, QFlow-Mini datapath work, synthesis or
board programming during Step 2.

## State encoder boundary

The four Python observations are clipped to `[0,1]`. The RTL boundary uses a
uniform unsigned normalized 16-bit representation (UNORM16): code `0` denotes
`0.0`, code `65535` denotes `1.0`, and reference vectors use clip followed by
round-half-up of `value * 65535`.

| Feature | Python thresholds | UNORM16 threshold codes |
| --- | --- | --- |
| Minimum key occupancy | 0.25, 0.50, 0.75 | 16384, 32768, 49151 |
| Bottleneck fidelity | 0.90, 0.93, 0.96 | 58982, 60948, 62914 |
| Offered request load | 0.25, 0.50, 0.75 | 16384, 32768, 49151 |
| Utilization imbalance | 0.125, 0.25, 0.50 | 8192, 16384, 32768 |

An encoded value equal to a threshold code enters the higher bin. Required RTL
edge vectors use `threshold_code-1`, `threshold_code`, and
`threshold_code+1`. Values separated by less than one UNORM16 LSB may quantize
to the same code; no arbitrary-real-precision equivalence is claimed.

The packed state is:

```text
state_id[7:6] = minimum-key-occupancy bin
state_id[5:4] = bottleneck-fidelity bin
state_id[3:2] = offered-request-load bin
state_id[1:0] = utilization-imbalance bin
```

This is exactly the radix-4 equation used by P2/P3. There are 256 valid states.

## ROM contracts

`policy_rom.mem` is the deployed learned artifact: 256 state-major entries,
one hexadecimal digit per line and two useful action bits. The action mapping
is 0 Balanced, 1 scarcity protection, 2 fidelity protection and 3 low latency.

`profile_rom.mem` contains four action-major entries. Each selected profile is
an 18-bit output; the entire ROM stores 72 useful bits. Fields from MSB to LSB
are four three-bit U2.1 alpha numerators followed by three two-bit primitive
Tchebycheff ratios.

`q_table.mem` is a 1,024-word signed Q8.7 audit artifact. It is not deployed in
the defense P4 controller. Therefore `rl_argmax.v` and `q_update.v` remain out
of scope.

## Frozen dwell semantics

The first valid decision after reset accepts its proposed action immediately
and establishes dwell count 1. A different proposal may be accepted only when
the current action has served at least three accepted decisions. There is no
pending-action register: the action proposed on the eligible decision is the
one accepted. Reset clears current-action validity and dwell history.

Hardware may saturate the internal dwell count at 3. This is output-timeline
equivalent to the Python controller, whose count can grow above 3, because only
the predicate `count >= 3` affects action selection.

Every accepted valid decision advances dwell, including a decision later
reported as no-path. Invalid requests and starts while busy do not advance it.

## Handshake

Reset is synchronous active-high and dominates all other controls. A request is
accepted only on `start && ready`. For a valid request accepted on edge N,
`done` and `output_valid` pulse after edge N+3. The three registered stages are
state encoding, policy read, and profile read/applied-action completion.

A request with `input_valid=0` is rejected without state change and reports
`done=1`, `invalid_state=1`, `output_valid=0` after edge N+1. `start` while busy
is not accepted and pulses `stall`; the active transaction is unchanged.

`no_path_in` is sampled with a valid accepted request and returned as status
with `done`. It does not suppress learned profile selection or dwell advancement.

## Frozen module ports

`rl_state_encoder` has `clk`, `rst`, `en` and the four 16-bit UNORM feature
inputs; it returns one-cycle `valid` and eight-bit `state_id`.

`rl_policy_rom` has `clk`, `rst`, `en` and eight-bit `state_id`; it returns
one-cycle `valid` and two-bit `proposed_action`.

`rl_profile_rom` has `clk`, `rst`, `en` and two-bit `selected_action`; it
returns one-cycle `valid` and the selected 18-bit `profile_payload`.

`rl_controller` exposes the four feature inputs plus `clk`, `rst`, `start`,
`input_valid` and `no_path_in`. Its outputs are `ready`, `busy`, `done`,
`output_valid`, `invalid_state`, `stall`, `no_path_out`, eight-bit `state_id`,
two-bit `proposed_action`, two-bit `selected_action`, 18-bit
`profile_payload`, `switched`, and two-bit saturated `dwell_count_sat`.

## ISE boundary

All future RTL uses synthesizable Verilog-2001 compatible with Xilinx ISE 14.7
for `xc6slx16-2-csg324`. No SystemVerilog-only construct or vendor-specific
primitive is required by this contract.
