# QFlow Thesis Results Section Draft

## 1. Implementation and Timing-Closure Results

The integrated QFlow core was refined through successive timing-closure iterations. In the tc3 baseline, the dominant bottleneck remained inside SKAG and the design failed the 10 ns target by a large margin. After restructuring the SKAG datapath in tc4, the worst path shifted into FDPE, indicating that the primary SKAG bottleneck had been sufficiently reduced. The final tc5 revision re-pipelined FDPE and achieved positive setup slack at the 10 ns target. This timing result was then corroborated by out-of-context (OOC) post-route implementation, which also reported positive setup and hold slack.

| version | WNS (ns) | TNS (ns) | approx. Fmax (MHz) | data path delay (ns) | interpretation |
|---|---:|---:|---:|---:|---|
| tc3 | -68.443 | -1412.372 | 12.773 | - | - |
| tc4 | -8.154 | -178.942 | 55.549 | - | - |
| tc5 | 0.033 | 0.000 | 101.885 | - | - |
| tc5_ooc_impl | 0.039 | 0.000 | 100.392 | - | - |

The most important engineering narrative is therefore: **SKAG bottleneck in tc3 → SKAG repair in tc4 → FDPE bottleneck exposed in tc4 → FDPE pipelining in tc5 → timing closure at 100 MHz class**. This is the correct interpretation of the closure history and should be used consistently in the thesis.

## 2. Evaluation and Baseline Comparison

The baseline evaluation progressed in two stages. First, the earlier software PMO-GA evaluation appeared to collapse to the key-aware shortest-path baseline. A focused follow-up study then showed that this collapse was substantially influenced by the **final-answer selection policy**. When the Pareto-front candidate was selected using weighted Tchebycheff scoring rather than a latency-first rule, PMO-GA began to separate from the key-aware heuristic on a meaningful subset of cases.

| profile | topology | recommended GA variant | Δ latency (GA - key-aware) | Δ fidelity (GA - key-aware) | Δ load-balance (GA - key-aware) |
|---|---|---|---:|---:|---:|
| current_like | mesh9 | ga_tcheby_pick_fidelityheavy | 0.009086 | -0.000624 | -0.032559 |
| current_like | mesh16 | ga_tcheby_pick_default | 0.041286 | 0.000444 | -0.025694 |
| current_like | irregular12 | ga_tcheby_pick_default | 0.007135 | 0.000190 | -0.031157 |
| depletion_plus_stricter_fidelity | mesh9 | ga_tcheby_pick_default | 0.000000 | 0.000000 | 0.000000 |
| depletion_plus_stricter_fidelity | mesh16 | ga_tcheby_pick_default | 0.006393 | 0.000000 | -0.033333 |
| depletion_plus_stricter_fidelity | irregular12 | ga_tcheby_pick_default | -0.002931 | -0.001342 | -0.145170 |

Across the current sweep, **ga_tcheby_pick_default** is the best overall software reference for the proposed PMO-GA. Its strongest observed benefit is generally improved load spreading, reflected by lower load-balance values than the key-aware baseline. In some current-like scenarios it also yields small fidelity improvements, although these gains are not universal. Accordingly, the honest claim is **tradeoff-aware separation**, not universal domination over the key-aware shortest-path heuristic.

## 3. Thesis-Safe Takeaways

- The hardware timing result is strong: tc5 met the 10 ns target at post-synthesis and OOC post-route.
- The strongest classical comparator is the key-aware shortest-path baseline, not the random-path baseline.
- PMO-GA should be represented in software using **ga_tcheby_pick_default** for the thesis narrative.
- The current evaluation supports **multi-objective tradeoff benefits**, especially better balance, but does not support a claim of universal superiority on every metric.
- Hardware deployment should still be described as **post-synthesis and OOC post-route validated**, not as a completed full board demonstration.
