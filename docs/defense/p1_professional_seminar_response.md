# QFlow-RL P1 Professional Seminar Response

**Topic:** Fair state-of-the-art comparison, hardware evidence, and adaptive-routing scope  
**Project:** QFlow-RL on Nexys 3  
**Branch:** `rl-nexys3-adaptive`  
**Prepared:** 17 July 2026  
**Evidence state:** P1 literature audit complete; corrected workbook controlled; Nexys 3 H0–H4 results not yet claimed

## Formal response to the seminar panel

Thank you for identifying the weakness in the earlier comparison. The earlier presentation mixed three different effects: route-quality differences between algorithms, implementation-platform acceleration, and architectural efficiency. That made the comparison difficult to interpret and allowed heterogeneous software and hardware results to appear as if they were direct competitors.

The comparison has now been repaired. We separate the evidence into four classes. Class A is a direct same-board hardware comparison. Class B isolates platform acceleration by implementing the identical algorithm and fixed-point function on CPU and FPGA. Class C compares algorithmic or network utility under matched topology, traces, candidate paths, seeds, and metrics. Class D uses published FPGA and related hardware work only as component or architectural context. A conclusion is restricted to the question answered by its class.

The primary defense comparison will therefore be Class A: H0 through H4 will be synthesized and run on the same Nexys 3 using a common external shell, input replay, graph state, candidate paths, numeric widths, start/done protocol, clock constraint, counters, and measurement boundaries. H0 is feasible shortest-distance routing, H1 is fixed key-aware routing, H2 is the existing fixed QFlow controller, H3 is a threshold/rule-based adaptive controller, and H4 is tabular QFlow-RL. This comparison tests whether adaptation helps, whether learning is necessary beyond a rule-based controller, and what hardware cost is paid for that intelligence.

Published QKD-routing papers remain important Class C counterparts for network behavior, but their decision latency is recorded as “not reported” unless the primary source explicitly measured it. FPGA reconciliation, error-correction, synchronization, genetic-algorithm, and packet-processing papers are retained as Class D context; their component throughput or latency is not treated as QFlow routing-decision latency. We have removed the heterogeneous “nanoseconds versus milliseconds” and “1000× faster” argument.

The literature conclusion is deliberately search-bounded. In the controlled 50-row audit completed on 17 July 2026, no Class A same-board or Class B same-function FPGA QKD-routing counterpart was identified. This supports the documented research gap, but it does not prove universal priority and is not used to claim that QFlow is the first such system.

The corrected position is therefore: QFlow-RL will be evaluated as an adaptive QKD-routing architecture whose network utility, bounded hardware cost, and decision latency are reported through matched evidence layers. Any claim that learning improves routing will depend on held-out Class C results and the same-board H0–H4 experiment; it is not assumed in advance.

## Comparison framework

| Class | Question answered | Required control | Permitted conclusion |
|---|---|---|---|
| A — same-board hardware | Which controller gives the best quality/cost trade-off? | H0–H4 on Nexys 3 with the common shell and identical inputs | Direct hardware comparison |
| B — same algorithm, CPU vs FPGA | What acceleration comes from the implementation platform? | Identical fixed-point function, vectors, and measurement boundary | Platform acceleration only |
| C — algorithm/network utility | Does adaptation improve QKD-network behavior? | Identical topology, traces, paths, seeds, traffic conditions, and metrics | Algorithmic or network-utility comparison |
| D — component/architecture context | How does QFlow relate to prior hardware and supporting methods? | Explicit separation of function and evidence layer | Context or feasibility only |

## Frozen same-board baselines

| ID | Controller | Purpose |
|---|---|---|
| H0 | Feasible shortest-distance | Minimal routing-hardware baseline |
| H1 | Fixed key-aware | Measures the value of key awareness |
| H2 | Existing fixed QFlow | Preserves the current fixed alpha/lambda anchor |
| H3 | Threshold/rule adaptive | Tests whether adaptation is sufficient without learning |
| H4 | Tabular QFlow-RL | Tests the learned state-to-profile contribution |

Every build will preserve the same external shell, input replay, graph state, candidate set, counters, fixed-point contract, reset/start/done interface, clock constraint, and UCF. Each policy receives an independent implementation report; resources will not be inferred from another build. Kernel cycles are measured internally, excluding host and UART overhead.

## Prepared answers to expected defense questions

### What is the novelty?

The defensible novelty is not a universal “first hardware QKD router” claim. The contribution under test is a reproducible cross-layer architecture that couples fidelity/key/load state to discrete hardware-safe QFlow coefficient profiles, then evaluates fixed, rule-based, and learned controllers on a common FPGA datapath. The literature finding is search-bounded: the documented 50-row audit did not identify a same-board or same-function FPGA QKD-routing counterpart.

### Why reinforcement learning?

The existing QFlow controller uses fixed alpha and lambda values. Those values encode one trade-off and may be unsuitable when key scarcity, fidelity, offered load, or utilization imbalance changes. Tabular Q-learning is used to select among a small set of hardware-safe coefficient profiles. H3 is essential: if the rule-based controller matches H4 at lower cost, the evidence will not support claiming that learning is necessary.

### Why tabular RL rather than DQN?

The defense objective is bounded, reproducible adaptation on a Spartan-6-class board. A small discrete state/action space can be represented by a compact policy ROM and maps directly to deterministic profile selection. DQN is optional journal work only and will be retained only if it materially improves held-out generalization enough to justify additional area, energy, verification, and quantization complexity.

### Why FPGA?

The FPGA contribution is deterministic, integrated state processing and route selection with explicit cycle, area, timing, and power boundaries. It is not justified by assuming that published software has millisecond inference. Platform acceleration can be claimed only through Class B with the identical QFlow function and vectors. Direct architecture efficiency will be established through Class A on Nexys 3.

### Where does training occur?

Training is offline in the controlled Python/OMNeT trace environment. The defense FPGA performs online state encoding and state-to-profile policy selection; it does not claim online weight training. An online temporal-difference update datapath is journal-only unless the mandatory defense path is already complete.

### What does the existing Artix-7 result prove?

The existing full-design evidence is a separate Artix-7 post-synthesis layer: 85 cycles, corresponding to 850 ns at a 10 ns clock, with 2991 LUT, 1128 FF, 16 BRAM, 5 DSP, and approximately 101.885 MHz post-synthesis timing. It demonstrates a concrete QFlow hardware datapath result. It is not a Nexys 3 board measurement, does not prove H4 benefit, and will not be relabeled as same-board H0–H4 evidence.

### Why reduce the design for Nexys 3?

Nexys 3 uses a smaller Spartan-6 device than the prior Artix-7 target. QFlow-Mini therefore preserves the comparison contract and the decision-critical FDPE/SKAG/path-evaluation behavior while reducing state bins, action profiles, and stored policy representation if required. Any reduction will be declared, applied consistently to H0–H4, and verified against fixed-point golden vectors.

### How is power handled?

Measured power will be reported only if the measurement setup is controlled and documented. Otherwise, power will be labeled as tool-estimated. All H0–H4 estimates will use the same activity assumptions, clock constraint, and boundary. Estimated power will not be described as board-measured power.

### How is scalability addressed?

The defense claim is limited to the frozen topology and trace set. Larger topologies, unseen traffic regimes, link failures, wider seed sets, sensitivity studies, and energy scaling belong to the journal-strengthening path. No generalization beyond the tested scope will be implied.

### What are the current limitations?

At the P1 boundary, Nexys 3 H0–H4 board results do not yet exist and are not claimed. Training is offline; the board design may use a reduced state/action representation; power may be estimated; and the literature audit is a controlled 50-row audit rather than proof of universal novelty. The OMNeT dynamic-load comparator is a GA-style proxy rather than the exact final PMO-GA selector. These limitations will remain explicit in the thesis and defense.

## Evidence boundaries and claim controls

| Earlier or unsafe wording | Controlled replacement |
|---|---|
| “QFlow is the first hardware dataplane solution.” | “In the documented 50-row audit, no same-function FPGA QKD-routing dataplane was identified; this is a search-bounded result.” |
| “All reviewed QKD routing is software.” | Identify each audited platform and evidence layer; do not universalize beyond verified sources. |
| “QFlow is 1000× faster than software.” | No heterogeneous ratio. Use Class B only with identical function, vectors, and boundary. |
| “Published routing inference is millisecond-scale.” | State “not reported” unless the primary source explicitly measures decision/inference runtime. |
| “All FPGA QKD work is physical-layer only.” | Describe the specific audited reconciliation, QEC, synchronization, post-processing, GA, and architecture examples. |
| “Novelty score 4/4.” | Remove the score and report evidence-backed distinctions and remaining Class A/B work. |
| “Artix-7 synthesis proves the Nexys 3 result.” | Keep Artix-7 synthesis and future Nexys 3 board evidence as separate layers. |
| “Learning improves QFlow.” | Treat this as a hypothesis until H4 passes the predeclared held-out and H0–H4 gates. |

## Evidence map

| Statement | Controlled evidence |
|---|---|
| Literature identities, platforms, metrics, and limitations | `literature/p1/audit/paper_audit.csv` |
| Search strings, publishers/databases, and screening trail | `literature/p1/audit/search_log.csv` |
| Repaired and removed claims | `literature/p1/audit/claim_register.csv` |
| Corrected defense-facing literature matrix | `literature/p1/corrected/QFlow_Literature_Review_Matrix_corrected.xlsx` |
| Comparison classes, H0–H4, fairness controls, and frozen experiment boundary | `docs/rl/benchmark_contract.md` |
| Defense/journal/archived scope | `docs/rl/scope_lock.md` |
| Existing Artix-7 hardware figures | Part A results dossier and corresponding repository reports |
| Dynamic-load network behavior | OMNeT final addendum and its locked CSV/figure sources |
| Future Nexys 3 hardware conclusions | Independent H0–H4 ISE reports, board CSVs, logs, hashes, and photos/video |

## Ninety-second oral version

The panel was correct that our earlier comparison mixed algorithmic and platform effects. We have repaired it using four evidence classes. Class A compares H0 through H4 on the same Nexys 3 and common shell. Class B compares CPU and FPGA only for the identical fixed-point function and vectors. Class C compares network utility under identical topology, traces, paths, seeds, and metrics. Class D uses published hardware only as component or architectural context.

This removes the earlier nanoseconds-versus-milliseconds and 1000-times argument. Published decision latency is now marked not reported unless directly measured. Our 50-row controlled audit found no same-board or same-function FPGA QKD-routing counterpart, but we present that only as a search-bounded gap—not as proof that QFlow is universally first.

The decisive experiment will be H0 shortest-distance, H1 key-aware, H2 fixed QFlow, H3 rule-adaptive, and H4 tabular QFlow-RL on the same board. The existing 85-cycle Artix-7 result remains separate evidence, not a Nexys 3 claim. We will claim a learning benefit only if H4 passes the frozen held-out network-utility gate and justifies its same-board hardware cost.

## P1 response conclusion

The comparison criticism is resolved at the protocol and literature-control level. The corrected matrix assigns every published row to an evidence class, unsupported latency and novelty statements have been removed or repaired, the same-board H0–H4 contract is frozen, and this response states the permitted conclusion for each evidence layer. Experimental superiority remains an open question for the later controlled runs; P1 does not pre-announce their outcome.
