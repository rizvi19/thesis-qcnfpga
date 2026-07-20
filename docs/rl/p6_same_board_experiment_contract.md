# P6 Same-Board H0-H4 Experiment Contract

## 1. Authority and phase boundary

This contract controls P6, the defense-mandatory same-board H0-H4 campaign.

- Source checkpoint: `e701dfa15d01938d85b281ab38bd07f6368d37e4`
- Branch: `rl-nexys3-adaptive`
- Physical target: Digilent Nexys3 Rev. B
- FPGA: Xilinx Spartan-6 `XC6SLX16-2-CSG324`
- Physical board clock: 100 MHz
- Physical clock period: 10 ns
- HDL boundary: Verilog-2001
- P5 remains frozen and is not overwritten.

P6 compares controller policies implemented under matched FPGA conditions. It
does not use FPGA-versus-Python timing as proof of algorithmic superiority.

## 2. Independent build matrix

| Build tag | Policy ID | Controller | Exact frozen behavior |
|---|---:|---|---|
| `n3_h0` | 0 | H0 feasible shortest-hop | Select feasible candidate with fewest hops, then lowest slot |
| `n3_h1` | 1 | H1 fixed key-aware | Common evaluator with cost-only lambda `(1,0,0)` |
| `n3_h2` | 2 | H2 fixed QFlow | Force frozen profile 0 |
| `n3_h3` | 3 | H3 rule adaptive | Frozen first-match threshold rules from P5 |
| `n3_h4` | 4 | H4 reinforcement-learned adaptive profile controller | Frozen policy ROM, profile ROM and three-decision dwell |

Each build synthesizes exactly one `POLICY_MODE`. H0-H4 are not inferred from
one combined synthesis report. Every build must have its own XST, NGDBuild,
Map, PAR, Trace and BitGen evidence.

H4 is trained offline and selects profiles online. Runtime Q-table argmax,
Q-value update and online FPGA learning are absent and must not be claimed.

## 3. Common-shell fairness invariants

The following items must be byte-identical or semantically identical across
H0-H4:

1. Ring-6 topology and directed-edge order.
2. Candidate slot capacity and candidate ordering.
3. Fixed-point widths and rounding/saturation rules.
4. Feasibility floor and no-path semantics.
5. Candidate score and deterministic tie-breaking arithmetic.
6. Reset, start, ready, busy, done and route-valid handshake.
7. Accepted-edge-to-done cycle counter.
8. External result schema.
9. Replay ordering and replay hash.
10. 100 MHz board clock and 10 ns UCF constraint.
11. Physical board, USB/JTAG path and programming method.
12. Output transport and parser.

The UCF shall be common across modes. Mode selection belongs in a compile-time
HDL parameter or mode-specific wrapper, not in physical pin constraints.

Any fallback that changes candidates, widths, arithmetic, replay, clock,
handshake or UCF requires a new contract version and a separate comparison
row.

## 4. Frozen controller details

### H0

H0 selects only among feasible candidates. Primary key: minimum hop count.
Secondary key: lowest candidate slot. It uses profile 0 for common output
compatibility. Its score field is reported according to the common result
shell but is not interpreted as its decision key.

### H1

H1 uses the common candidate evaluator with Tchebycheff ratio `(1,0,0)`.
This is the fixed key-aware cost-only baseline.

### H2

H2 always selects profile 0 and uses the common QFlow evaluator. It is the
fixed QFlow anchor.

### H3

H3 uses the frozen first-match rules:

1. key bin 0 -> profile 1;
2. else fidelity bin 0 or 1 -> profile 2;
3. else imbalance bin 2 or 3 -> profile 1;
4. else safe saturated-load state -> profile 3;
5. otherwise -> profile 0.

### H4

H4 uses:

- 256 encoded states;
- four actions/profiles;
- frozen policy index ROM;
- frozen four-entry profile ROM;
- minimum dwell of three accepted decisions;
- accepted P4 controller behavior;
- no retraining during P6;
- no runtime Q update.

The approved wording is **reinforcement-learned adaptive profile controller**.

## 5. Replay contract

P6 uses two replay tiers.

### Tier A: contract replay

- Exactly 20 deterministic P5 B6 contract cases, IDs 0 through 19.
- Source authority:
  `sim/spartan6/tb_p5_b6_measurement_shell.v`.
- Purpose: handshake, invalid request, no path, H3 rule coverage, H4 profile
  selection and dwell coverage.
- Each mode receives the same ordered 20 cases.

### Tier B: held-out dynamic replay

- Exactly 64 ordered rows.
- Seed: `26072026`.
- The seed is new at the P6 contract checkpoint.
- The final rows are materialized and hashed before the first H0 build.
- The learned policy, thresholds and profiles may not be tuned after the final
  replay hash is committed.
- All five modes receive the identical byte-exact replay.
- The sequence must exercise scarcity, fidelity, load, imbalance and mixed
  transitions.
- No-path and invalid-request rows remain visible but are separated from
  successful-route utility statistics.

The final replay file and its SHA-256 are a Step 3 gate. No H0-H4 synthesis is
authorized until that gate passes.

## 6. Result-record contract

The parsed `board_results.csv` fields are frozen in this exact order:

```text
test_id,policy_id,state_id,profile_id,selected_path,score,bottleneck_fidelity,cycles,status
```

For Ring-6, `selected_path` is the selected architectural candidate slot. The
path node sequence is derived from `(src,dst,selected_path)` in the replay
manifest and must not be guessed from display behavior.

Raw transport lines use:

```text
QF6R,1,test_id,policy_id,state_id,profile_id,selected_path,score,bottleneck_fidelity,cycles,status
```

Rules:

- decimal unsigned fields unless a later transport specification explicitly
  freezes hexadecimal;
- one CRLF-terminated record per completed request;
- status 0 = OK, 1 = NO_PATH, 2 = INVALID_REQUEST;
- raw logs are immutable evidence;
- parsing must be deterministic and byte-reproducible;
- a planned or simulated transport is not physical UART evidence.

## 7. Measurement definitions

- `kernel_cycles = N_done - N_accept`.
- `N_accept` is the synchronous edge accepting `start && ready && input_valid`.
- UART serialization, host parsing, JTAG programming and human time are
  excluded.
- Physical-board kernel latency:
  `board_kernel_latency_ns = kernel_cycles * 10`.
- Physical-board decisions/s:
  `100000000 / kernel_cycles`, when continuous issue is meaningful.
- Achieved post-PAR Fmax is reported as implementation capacity, not as the
  actual board clock.
- UART/host elapsed time may be reported separately and must be labelled
  transport time.
- Any nondeterministic kernel-cycle variation for the same replay row is a
  failure requiring investigation.

## 8. Independent implementation evidence

Each mode must preserve:

- build tag and policy ID;
- source commit and source hashes;
- replay SHA-256;
- common UCF SHA-256;
- XST log/report;
- NGDBuild log/report;
- Map log/report;
- PAR log/report;
- Trace timing report;
- BitGen log/report;
- exact bitstream size and SHA-256;
- clean USB/Adept/JTAG identity;
- programming log containing `Programming succeeded.`;
- raw board output;
- parsed `board_results.csv`;
- golden comparison;
- physical observation;
- failure history.

Required implementation metrics include slices, LUTs where available, FFs,
BRAMs, DSPs, minimum period, achieved Fmax and timing errors.

Controller-only incremental cost is calculated only after all independent
builds exist.

## 9. Correctness gates

For every mandatory replay row:

1. policy ID must equal the compiled mode;
2. state ID must match the golden state encoder;
3. H2 profile must be 0;
4. H3 profile must match frozen rules;
5. H4 selected profile and dwell behavior must match the frozen controller;
6. status must match;
7. successful selected path must match;
8. score and bottleneck fidelity must match the fixed-point golden result;
9. kernel cycles must be valid and deterministic;
10. no missing or duplicate test IDs are allowed.

The exact-vector requirement is 100% for mandatory rows. Failures are retained,
not silently removed.

## 10. Power and energy boundary

Power/energy is included only when one consistent method can be used for all
five builds.

- Tool-estimated power remains labelled estimated.
- Activity assumptions and tool version must be identical.
- Energy per decision is derived only from the reported power and the physical
  100 MHz kernel latency.
- Missing power evidence is labelled omitted; it is never invented.

## 11. Statistical boundary

The H0-H4 board rows are paired by replay order and test ID.

The final analysis must report at least:

- exact-match counts;
- success/no-path counts;
- profile-use counts for H3/H4;
- path-selection counts;
- cycle distributions;
- paired quality deltas on successful comparable rows;
- 95% confidence intervals when sample support is adequate;
- effect size and an appropriate paired test when valid.

Non-significant, tied or negative H4 results remain visible.

## 12. Claim firewall

Allowed after the complete P6 exit gate:

- H0-H4 were implemented independently on the same Nexys3 shell.
- H4 performs online state-to-profile selection from an offline-learned policy.
- Resource, timing, correctness and quality trade-offs are compared fairly.

Forbidden:

- online Q-learning on FPGA;
- full Artix-7 QFlow deployment on Nexys3;
- universal H4 superiority;
- FPGA-versus-Python speed as algorithm superiority;
- measured physical UART evidence without a raw capture;
- measured power when only an estimate exists;
- guaranteed Q1 acceptance.

## 13. Step 2 exit gate

Step 2 passes when:

- this human-readable contract exists;
- the machine-readable JSON contract validates;
- result/build/replay schemas validate;
- authority hashes are preserved;
- the branch is unchanged;
- the contract commit is pushed normally;
- no FPGA, UART or EEPROM operation occurred.

Step 2 does not authorize synthesis or board programming. Step 3 must freeze
the exact replay and prove the physical result transport before H0 begins.
