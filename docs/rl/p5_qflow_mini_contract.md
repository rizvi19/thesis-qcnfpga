# P5 QFlow-Mini Contract Freeze

## Authority, checkpoint and scope

This contract is authored for P5 Step 2 at source checkpoint
`2dba73ea36e6cd35b43cf3d06cbf6e774a6e429d` on branch
`rl-nexys3-adaptive`. It consumes the accepted P2 Ring-6 environment and the
accepted P4 learned controller. It authorizes contracts, schemas, contract
tests and deterministic contract evidence only.

Step 2 does not authorize RTL, a UCF, ISE activation, XST, NGDBuild, Map, PAR,
TRCE, BitGen, live board enumeration, UART access, board programming, EEPROM
access, staging, commit or push.

QFlow-Mini is a reduced Spartan-6 physical proof-of-concept. It is not the full
Artix-7 implementation. Full-design and QFlow-Mini results shall never share a
direct-comparison row.

## Topology and candidate representation

- Nodes are unsigned IDs 0 through 5.
- The directed-edge order is frozen as:

```text
0:(0,1)  1:(1,0)  2:(1,2)  3:(2,1)
4:(2,3)  5:(3,2)  6:(3,4)  7:(4,3)
8:(4,5)  9:(5,4) 10:(5,0) 11:(0,5)
```

- A valid request has distinct `src` and `dst` in 0..5.
- Four hardware candidate slots are reserved, as required by the P5 plan.
- Slot 0 is the simple clockwise Ring-6 path: repeatedly add one modulo 6.
- Slot 1 is the simple counterclockwise path: repeatedly subtract one modulo 6.
- Slots 2 and 3 are invalid/reserved in contract version 1. Their valid bits
  are zero and their payloads are ignored. This reconciles the P5 four-slot
  capacity with the P2 authority, which has exactly two simple Ring-6
  directions. No additional physical route is invented.
- A path is represented by `valid`, a three-bit hop count, and up to six
  three-bit node IDs. Unused node fields are zero.
- Candidate ordering is architectural and shall not depend on discovery order.

## Fixed-point adapter v1

The following rules apply only to new QFlow-Mini hardware/reference vectors.
They do not reinterpret earlier floating-point or Artix-7 evidence.

### Encodings

| Quantity | Encoding | Meaning |
|---|---|---|
| Fidelity, QBER | 16-bit UNORM16 | `real = code / 65535` |
| Key count | unsigned 16-bit | integer keys; logical capacity 16 in frozen traces |
| Key rate | unsigned UQ8.8 | `real = code / 256` |
| Edge/path weight | unsigned UQ16.16 | `real = code / 65536` |
| Infinite/invalid weight | `0xFFFFFFFF` | never treated as a finite maximum |
| Maximum finite weight | `0xFFFFFFFE` | saturation ceiling |
| Utilization objective | unsigned UQ16.16 | nonnegative ratio |
| Normalized objective | UNORM16 | 0..65535 |
| Alpha coefficient | unsigned U2.1 | three-bit numerator divided by 2 |
| Tchebycheff ratio | unsigned 2-bit | primitive positive ratio; common normalization omitted |

Real-to-code conversion uses clipping followed by round-to-nearest with exact
half cases rounded upward. Additions saturate. Multiplication retains a full
intermediate before the specified rescale. Division by zero never occurs in a
finite calculation; it produces invalid/infinite status. Comparisons are
unsigned and exact in the encoded domain.

### FDPE-mini meaning

FDPE-mini preserves the repository exponential-decay meaning:

```text
F = F_initial * exp(-x),  x = elapsed / tau
```

`x` is supplied as unsigned UQ4.12. The 256-entry table covers
`x_i = i/32`, `i=0..255`; each table word is
`round_half_up(exp(-x_i) * 65535)`. For `0 <= x < 8`, the high interval index
is `floor(32*x)` and the low seven UQ4.12 bits provide the 1/128 interpolation
fraction. Signed linear interpolation is rounded half up and clipped to
UNORM16. `x >= 8` yields zero. The interpolated exponential code is multiplied
by `F_initial`; the full product is shifted right by 16, matching the accepted
reference-model truncation boundary. `tau=0` is invalid and yields zero plus
error status. B2 must compare this exact path against generated vectors; no
board-fidelity claim exists in Step 2.

### SKAG-mini meaning

Each of the 12 directed edges uses one 64-bit logical entry:

```text
[63:48] key_count_u16
[47:32] fidelity_unorm16
[31:16] key_rate_uq8_8
[15:0]  qber_unorm16
```

A parallel 32-bit UQ16.16 weight preserves the accepted equation:

```text
w = alpha1/K + alpha2/F + alpha3/key_rate + alpha4*qber
```

Each term is evaluated from the encoded values as an exact nonnegative rational,
converted once to UQ16.16 using the adapter rounding rule, and then accumulated
with saturation. `K=0`, `F=0` or `key_rate=0` makes the edge infeasible and its
weight `0xFFFFFFFF`. Lower finite weight is better. B3 must prove exact encoded
weights or exact rankings from frozen vectors before an implementation claim.

## Candidate objectives and selection

A candidate is feasible only if every directed edge exists, has at least one
key, has positive key rate, and has fidelity code at least 58982 (the accepted
UNORM16 code for 0.90). A path must also be simple and respect its frozen slot.

For each feasible candidate:

1. `path_cost` is the saturating sum of finite edge weights.
2. `bottleneck_fidelity` is the minimum edge fidelity code.
3. `utilization_imbalance` is the maximum, over path edges, of
   `(consumed_in_last_16_steps + 1) / max(key_count,1)`, encoded UQ16.16.

The minimization vector is `(path_cost, 65535-bottleneck_fidelity,
utilization_imbalance)`. Each objective is normalized across feasible
candidates. If its maximum equals its minimum, normalized value is zero;
otherwise:

```text
norm = round_half_up((value-minimum)*65535 / ((maximum-minimum)+1))
```

The `+1` is one source-objective LSB and preserves the P2 normalization-epsilon
intent. The profile's primitive Tchebycheff ratios multiply the three normalized
codes. Division by their common sum is omitted because it cannot change route
ordering. Candidate score is the maximum of the three products; lower is better.

The deterministic ranking key is:

```text
(score, path_cost, hop_count, candidate_slot)
```

Thus the lowest slot wins a complete tie. Invalid slots never participate. If
no slot is feasible, the request completes with `NO_PATH`; no selected path or
finite score is asserted.

## H0-H4 policy shell

`POLICY_MODE` is compile-time and the external request/result shell is common:

| ID | Meaning | Profile behavior |
|---|---|---|
| H0 | feasible shortest-distance | profile 0; route policy may bypass score but keeps common candidates/results |
| H1 | fixed key-aware | profile 0; fixed key-aware selection inside the common evaluator boundary |
| H2 | existing fixed QFlow | always accepted action/profile 0 |
| H3 | frozen threshold/rule adaptive | P3 first-match state-bin rules |
| H4 | frozen learned adaptive | accepted P4 controller and policy-index ROM |

All modes expose policy ID, state ID, profile ID, selected path, score,
bottleneck fidelity, cycles and status. Controller-only differences must not
change topology, trace, numeric, handshake, clock, UCF or measurement semantics.

H4 consumes the P4 controller without retraining or reinterpretation: 256
states, four actions, policy ROM deployment, four exact 18-bit payloads,
three-decision minimum dwell and three-cycle valid-request controller latency.
`q_table.mem` remains audit-only; runtime argmax and Q-update remain absent.
No-path is sampled/reported without suppressing profile selection or dwell
advancement.

## Transaction and latency semantics

- One synchronous active-high reset dominates every control and clears
  observable validity/status.
- `ready` is high only while idle. A request is accepted on an edge only when
  `start && ready && input_valid`.
- `busy` is high from valid acceptance through the cycle before `done`.
- `done` is a one-cycle completion pulse. `route_valid` is a one-cycle pulse
  coincident with `done` only for a successful route.
- `start && ready && !input_valid` is rejected and completes one cycle later
  with `INVALID_REQUEST`, no route validity and no learned-controller state
  change.
- `start` while busy is not accepted; `stall` pulses for one cycle and the
  active transaction is unchanged.
- A valid request with no feasible path completes with `NO_PATH` and
  `route_valid=0`. H4 profile selection and dwell still complete and advance.
- Back-to-back accepted requests are allowed when `ready` returns high.
- The kernel latency counter is zeroed on the accepted edge N and records
  `N_done-N`. It counts synchronous datapath cycles only. UART serialization,
  host parsing and programming time are excluded.

## Resource fallbacks

Fallback order is frozen: policy ROM rather than Q-table; preserve all four
actions; reduce state count to 128/64 only after a reviewed fit failure;
serialize FDPE; reduce candidate count; reduce numeric widths last. Every
fallback needs a new contract/build tag, regenerated vectors, complete
revalidation and a separate result row. No fallback is active in Step 2.

## Claim firewall

Step 2 proves only that the P5 contract is internally consistent and anchored
to accepted files. It proves no RTL correctness, synthesis, placement/routing,
timing closure, Fmax, resource use, power, board behavior, UART behavior,
hardware route result, statistical superiority or online FPGA learning.
EEPROM access is absolutely prohibited throughout normal P5.
