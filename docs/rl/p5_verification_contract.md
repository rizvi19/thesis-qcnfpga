# P5 Verification Contract

## Ladder and stop gates

Verification is monotonic. A later rung cannot repair a failed earlier rung by
weakening the contract.

1. **Step 2 contract gate:** schema/contract tests and source-anchor hashes.
2. **Host reference gate:** deterministic fixed-point unit vectors for FDPE,
   SKAG, candidate scoring, ties, invalid/no-path and H0-H4 shell behavior.
3. **RTL unit gate:** plain Verilog-2001 units match every applicable vector.
4. **Integrated simulation gate:** cycle-accurate handshake, H4 handoff, UART
   record bytes and latency counter match the reference.
5. **ISE implementation gate:** exact tagged sources pass XST, NGDBuild, Map,
   PAR, TRCE and BitGen; reports and bitstream hash are retained.
6. **B1-B6 board gate:** authorized volatile programming and captured physical
   evidence match the same vectors.
7. **P6 comparison gate:** independently built H0-H4 bitstreams replay the same
   ordered vectors and traces.

Step 2 executes rung 1 only.

## Required vector categories

- reset dominance and output clearing;
- valid, invalid, stalled and back-to-back transaction timelines;
- all 12 directed links and Ring-6 wraparound;
- clockwise/counterclockwise path generation for all 30 ordered endpoint pairs;
- reserved candidate slots 2 and 3 always invalid;
- FDPE endpoints, every LUT interval boundary, interpolation cases, `x>=8`,
  zero tau and multiplication truncation;
- SKAG zero K/F/rate, finite terms, half-round cases and every saturation path;
- fidelity exactly one code below, at and above 58982;
- one/two/no feasible candidates;
- equal-objective normalization, nonzero ranges and score-product maxima;
- complete ties plus score, cost, hop and slot tie-break levels;
- H0-H4 common result fields;
- exact P4 state/action/profile/dwell handoff for H4;
- UART valid lines and parser rejection cases;
- latency counter off-by-one boundaries.

## Exactness and tolerances

Topology, path IDs, status, state, profile, handshake, cycles, UART bytes,
SKAG integer weights and candidate scores require exact equality. FDPE encoded
output requires exact equality to the P5 fixed-point reference; a separate
comparison to real `exp(-x)` may report approximation error but cannot replace
encoded equality. Any future tolerance must be predeclared in a versioned
vector generator before results are observed.

## H4 regression anchors

H4 must continue to use the accepted P4 state encoder, policy ROM, profile ROM
and dwell/handshake behavior. Policy/profile artifacts and the P4 contract are
hash-anchored by Step 2. Runtime Q-table argmax, Q-update and online learning
remain prohibited.

## Evidence levels and allowed language

| Evidence | Allowed statement |
|---|---|
| Contract test | contract/schema consistency only |
| Python/reference | expected software/fixed-point behavior |
| RTL simulation | simulated RTL agreement |
| XST | synthesis result/estimate only |
| post-PAR/TRCE | implemented timing for exact build |
| physical capture | measured/observed Nexys3 behavior |

Never promote an XST estimate to timing closure or board Fmax. Never combine
UART/host time with kernel cycles. Never infer a physical result from a
bitstream-generation success.

## Failure handling

Preserve failed logs. A repair identifies the exact cause, changes only the
reviewed files, reruns all affected lower rungs and retains the original
contract. A semantic change requires a new schema/contract version and explicit
human review. No unexplained mismatch is acceptable.

## Absolute safety rule

No verification rung in normal P5 reads, writes, erases, repairs or diagnoses
the Digilent USB/JTAG EEPROM. Repeated raw Cypress mode is a separate recovery
workflow and is not authorized by this contract.
