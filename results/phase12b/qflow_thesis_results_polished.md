# Polished Thesis Results Subsection

## Implementation and Timing-Closure Results

The integrated QFlow core was closed through a staged timing-closure process rather than a single monolithic optimization pass. In the early integrated baseline (tc3), the dominant critical path was still concentrated in the SKAG update datapath, and the design missed the 10 ns requirement by a large margin. After restructuring and deepening the SKAG pipeline in tc4, the worst path migrated from SKAG into FDPE. This shift was important because it showed that the original SKAG bottleneck had been reduced sufficiently for FDPE to become the next limiting stage. The final tc5 revision then re-pipelined FDPE and achieved positive setup slack at the 10 ns target, reaching approximately 101.885 MHz at post-synthesis. This result was subsequently corroborated by out-of-context post-route implementation, which also reported positive setup and hold slack and an approximate post-route frequency of 100.392 MHz.

Accordingly, the correct engineering narrative for the integrated core is: **SKAG bottleneck in tc3 → SKAG repair in tc4 → FDPE bottleneck exposed in tc4 → FDPE pipelining in tc5 → 100 MHz-class timing closure at post-synthesis and OOC post-route**. This is the thesis-safe interpretation of the closure history. It should also be emphasized that the implementation claim is an **OOC post-route validation of the core**, not a completed full board-level deployment.

## Baseline Evaluation Results

The baseline study shows that the strongest classical comparator is the **key-aware shortest-path heuristic**, not the random-path baseline. Earlier software evaluation suggested that the PMO-GA reference collapsed to the key-aware baseline; however, the follow-up selection-policy study showed that this behavior was substantially influenced by a latency-first final-answer rule. Once the final GA candidate was selected from the Pareto set using weighted Tchebycheff scoring, the software PMO-GA became distinct from the key-aware heuristic on a meaningful subset of the evaluated cases. Based on the current six-case evaluation sweep, the most appropriate software reference for the thesis is **ga_tcheby_pick_default**.

The main quality advantage observed for the Tchebycheff-selected PMO-GA is **improved load spreading**, reflected by lower load-balance values than the key-aware baseline in the strongest cases. The largest observed balance gain appeared in the **depletion_plus_stricter_fidelity / irregular12** scenario, where the recommended GA variant changed the load-balance metric by -0.145170 relative to key-aware routing, while also slightly improving latency by -0.002931. The strongest current fidelity-oriented case appeared in **current_like / mesh16**, where the recommended GA variant improved fidelity by 0.000444, albeit with a small latency penalty of 0.041286. These results indicate that the honest claim is **tradeoff-aware separation**, not universal domination over the key-aware heuristic on every metric.

## Final Thesis-Safe Takeaways

1. The hardware result is strong: the final integrated core met the 10 ns target at both post-synthesis and OOC post-route.
2. The strongest algorithmic comparator is the key-aware shortest-path baseline, which must be treated as the main non-trivial reference in the thesis.
3. The most faithful software representation of the proposed PMO-GA is **ga_tcheby_pick_default**.
4. The current evidence supports **multi-objective tradeoff benefits**, especially improved balance and route spreading, but it does not support a claim that PMO-GA universally dominates key-aware routing on all metrics.
5. Board-level deployment language must remain precise: the present claim is **post-synthesis and OOC post-route validation of the core**, not a completed physical board demonstration.
