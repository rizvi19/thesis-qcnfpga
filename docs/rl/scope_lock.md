# QFlow-RL Scope Lock

## 1. Document control

| Field | Frozen value |
|---|---|
| Project | QFlow-RL: Reinforcement-Learned Adaptive Weight Controller |
| Physical target | Digilent Nexys 3, Spartan-6 XC6SLX16-2-CSG324 |
| Repository | `rizvi19/thesis-qcnfpga` |
| Verified base branch | `main` |
| Verified base commit | `54a2d57b4d425d30627a5ca3bba2cd369e6d73ab` |
| Development branch | `rl-nexys3-adaptive` |
| Scope-lock date | 2026-07-17 |
| Primary method | Offline tabular Q-learning with online FPGA profile selection |
| Initial action space | Four discrete coefficient profiles |
| Initial topology | Ring-6 |
| Priority | Defense-mandatory P0 work before journal extensions |

This document freezes the active development scope. Earlier full-QFlow,
Artix-7, OMNeT++, VLSI and cloud-FPGA artifacts remain preserved evidence,
but they are not all part of the new Nexys 3 implementation.

## 2. Primary hypothesis

A compact reinforcement-learned controller will select a discrete,
hardware-efficient coefficient profile from the current QKD network state.

Each profile controls:

- SKAG coefficients `alpha1`, `alpha2`, `alpha3`, and `alpha4`;
- Tchebycheff weights `lambda_TCH1`, `lambda_TCH2`, and `lambda_TCH3`.

The controller must improve adaptation over fixed coefficients while
preserving fixed-point correctness, bounded latency, reproducibility and
resource feasibility on the Nexys 3.

## 3. Terminology lock

| Symbol | Meaning | May RL change it? |
|---|---|---|
| `alpha_fiber` | Physical fiber-attenuation coefficient | No |
| `lambda_ij(t)` | Effective key-generation rate of link `(i,j)` | No; it is observed state |
| `alpha1..alpha4` | SKAG scarcity, fidelity, replenishment and QBER penalties | Yes, through profile selection |
| `lambda_TCH1..3` | Tchebycheff multi-objective weights | Yes, through profile selection |

Training occurs offline for the defense implementation. The FPGA performs
online state encoding and profile selection. The permitted description is
"reinforcement-learned adaptive profile selection."

The phrase "online learning on FPGA" is prohibited unless an on-chip
temporal-difference update datapath is implemented and measured.


## 4. Frozen earlier evidence

These values are preserved from the approved execution plan. Each value
must remain in its correct evidence layer.

| Evidence item | Frozen value or boundary |
|---|---|
| Full QFlow RTL | FDPE, SKAG, PMO-GA family and integrated `qflow_top` exist |
| Artix-7 timing | Post-synthesis WNS `+0.033 ns`; Fmax `101.885 MHz` |
| Artix-7 resources | 2991 LUT, 1128 FF, 16 BRAM and 5 DSP |
| Full-design latency | 85 cycles, or 850 ns with a 10 ns clock |
| OOC post-route | WNS `+0.039 ns`; Fmax `100.392 MHz`; supporting evidence only |
| OMNeT++ | Distance, key-aware, random and GA-Tchebycheff-proxy results exist |
| GA proxy | Does not universally dominate key-aware routing |
| Nexys 3 bring-up | USB `1443:0007`; serial `210182697240`; JTAG ID `44002093`; SW0-to-LD0 passed |
| AWS | F1/F2 branches are archived; no defense-time cloud execution |
| VLSI | Shift-add SKAG reduced generic cells from 5343 to 503 |

Usage restrictions:

1. Full Artix-7 results must remain in the full-design evidence table.
2. Reduced Nexys 3 results must remain in the QFlow-Mini board table.
3. Artix-7 and Nexys 3 results must not be mixed as directly comparable
   implementations.
4. The OOC result must not be described as physical board signoff.
5. Existing OMNeT++ traces may be reused, but fixed, rule-based and learned
   policy results must use identical traces and seeds.
6. The GA proxy must not be described as universally superior.
7. The VLSI result motivates dyadic coefficient profiles but does not
   authorize new pre-defense VLSI work.
8. Every frozen value must be mapped to its original report before final
   thesis or journal submission.


## 5. Verified baseline at the branch point

The base commit was tested before creating `rl-nexys3-adaptive`.

### 5.1 Environment

- Python executable:
  `/home/shahriar-rizvi/miniconda3/envs/vlsi/bin/python`
- Python version: `3.13.0`
- NumPy version: `2.4.4`

### 5.2 Unit-test result

- Command: `python reference_model.py --test`
- Result: 26 of 26 tests passed
- Exit code: 0
- Observed test-suite runtime: 0.632 seconds
- Environment-log SHA-256:
  `01ac3ef9033d04e68ecd1aa82793af354fe9869db38a96e53dd17253e3d24bd0`
- Unit-test-log SHA-256:
  `d1b66267ada62760411033b6d1d935ec03ed2442fdb8c37473dbd233e00de98c`

The 0.632-second value is software test-suite runtime. It is not routing
latency and must not be used as an FPGA acceleration result.

### 5.3 Deterministic Ring-6 result

Two executions of `python reference_model.py` produced byte-identical logs.

| Metric | Baseline result |
|---|---:|
| Pareto-front entries reported | 64 |
| Convergence steps | 11 |
| Selected path | `[0, 5, 4, 3]` |
| Software objective labelled latency | 5.460344 |
| Bottleneck fidelity | 0.928396 |
| Balance objective | 0.000000 |
| Run 1 exit code | 0 |
| Run 2 exit code | 0 |
| SHA-256 of both logs | `3d11ca4c315224eb09c2dec27d7472d699aec9080c0930fef166722ac646b90a` |

The software value labelled latency is an algorithmic objective. It is not
FPGA execution time.

## 6. Known baseline issues

The following issues are preserved instead of being silently hidden:

1. `README_STEP1_PHASE0.md` and the root `Makefile` reference
   `audit_reference_model.py` and `init_repo_structure.py`, but these files
   are absent from the verified `main` commit.
2. The Ring-6 output reports 64 Pareto entries containing many duplicate
   paths and objective tuples.
3. The balance objective is zero for all displayed Ring-6 solutions.
4. The base commit message is "in middle of making fig and table," although
   its working tree is clean and all 26 verified Python tests pass.

These are traceability and model-quality issues. They require investigation,
but they do not erase the reproducible baseline.


## 7. Defense-mandatory scope

The following work is mandatory before the defense package is considered
complete:

1. Freeze the fair-comparison and measurement contract.
2. Implement the following controllers using a common external shell:
   - H0: feasible shortest-distance routing;
   - H1: fixed key-aware routing;
   - H2: existing fixed-coefficient QFlow;
   - H3: threshold/rule-adaptive QFlow;
   - H4: tabular QFlow-RL.
3. Define and validate four initial coefficient profiles.
4. Freeze the state, action, transition and decomposed reward definitions.
5. Reproduce H2 when the balanced action is forced.
6. Train with separated training, validation and test traces.
7. Evaluate H4 against H2 and H3 on identical held-out traces and seeds.
8. Export the learned policy and profiles to FPGA-compatible memory files.
9. Implement the state encoder, policy ROM, profile ROM and controller RTL.
10. Integrate a reduced QFlow-Mini common datapath for Spartan-6.
11. Execute H0-H4 on the same Nexys 3 using identical replay vectors.
12. Preserve simulation, synthesis, timing, resource, bitstream and UART
    evidence.
13. Update thesis claims, defense slides and the response sheet.

The same-board comparison must use common:

- input vectors and request traces;
- candidate paths;
- fixed-point formats;
- reset, start, done and result protocol;
- clock constraint;
- UCF constraints;
- kernel-latency definition;
- resource-reporting method;
- power-estimation or measurement method.

## 8. Non-blocking and archived scope

The following work must not delay the defense path:

- AWS F1/F2 deployment, AFI creation or cloud spending;
- tiny DQN or another deep-RL architecture;
- on-chip Q-table or temporal-difference update;
- new QP-TSN development beyond preserving existing evidence;
- new VLSI, OpenROAD or CMOS experiments;
- broad topology-generalization experiments;
- journal-scale ablations not required to validate the defense claim.

These items may begin only after phases P0-P7 are reproducible and green.

Existing AWS, QP-TSN and VLSI evidence must remain preserved. Marking them
non-blocking does not mean deleting them.


## 9. Comparison and claim boundaries

### 9.1 Allowed comparisons and claims

1. H0-H4 may be compared directly when they use the same board, external
   shell, fixed-point formats, candidate paths, replay vectors, clock
   constraint and measurement definitions.
2. CPU and FPGA may be compared only for the same algorithm, arithmetic and
   input vectors. The conclusion is then platform acceleration, not
   algorithm superiority.
3. Network utility may be compared using identical traces, topology and
   random seeds.
4. Published FPGA routing, GA, RL and QKD implementations may be reported as
   normalized component-level hardware context.
5. QFlow-RL may be described as automatically selecting a learned
   coefficient profile from the current discretized QKD state.
6. Full Artix-7 and reduced Nexys 3 results may be shown as separate evidence
   layers with explicit labels.

### 9.2 Forbidden comparisons and claims

The following statements or practices are prohibited:

- claiming algorithm superiority because FPGA execution is faster than
  Python or software from another paper;
- mixing full Artix-7 results and reduced Nexys 3 results in one direct
  comparison row;
- describing QFlow-Mini as a full deployment of the Artix-7 implementation;
- claiming online FPGA learning when the FPGA performs only policy lookup;
- claiming "first ever";
- claiming universal superiority from the current GA proxy;
- presenting UART or host-communication time as kernel latency;
- presenting software objective latency as FPGA execution latency;
- hiding failed seeds, degraded metrics or negative results;
- using different input traces, widths or candidate sets across H0-H4;
- calling estimated power measured power;
- claiming board timing from a synthesis or OOC report without post-PAR
  evidence.

Until the literature audit is complete, the permitted novelty wording is:

> No directly comparable same-board QKD-routing implementation was
> identified in the current search.

This wording must be updated if the systematic literature audit finds a
direct counterpart.


## 10. Initial bounded adaptive architecture

| Element | Initial defense value |
|---|---|
| State features | Minimum key occupancy, fidelity, offered load and utilization imbalance |
| State bins | `4 x 4 x 4 x 4 = 256` states |
| Initial actions | Four coefficient profiles |
| Optional expansion | Eight actions only if four are insufficient |
| Initial Q-value format | Signed 16-bit fixed point |
| Preferred deployment | Policy-index ROM |
| Coefficients | Dyadic values suitable for shift/add hardware |
| Training | Offline, seeded and reproducible |
| FPGA behavior | Online state-to-profile selection |
| Initial topology | Ring-6 |
| Initial candidate paths | Four |
| Fidelity format | Q0.16 |
| Weight format | Q16.16 where feasible |

If timing or resources fail, reductions must follow this order:

1. use policy-index ROM instead of a full Q-table;
2. retain only four actions;
3. reduce to 128 or 64 states;
4. serialize FDPE processing;
5. reduce the candidate-path count;
6. narrow numeric widths and repeat fixed-point error validation.

No mathematical or measurement change may be made silently.


## 11. Run identification and traceability

Every experiment uses `YYYYMMDD_policy_topology_seed_buildtag`.

The run manifest records the run ID, timestamp, Git SHA and branch, policy,
topology, trace checksum, seeds, fixed-point formats, clock constraint, tool
versions, board serial, bitstream checksum, outputs and pass/fail decision.

Kernel latency is recorded separately from UART and host latency. Generated
build directories are never copied between evidence layers.

## 12. P0 exit condition

P0 requires an isolated branch, verified baseline evidence, scope lock,
H0-H4 benchmark contract, run-manifest template, planned directories, an
intentional commit and a published remote branch.

Until those conditions pass, RL training, DQN work and new FPGA datapath
implementation do not begin.

<!-- P0_SCOPE_LOCK_FINAL -->
