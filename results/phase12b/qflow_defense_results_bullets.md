# Defense Results Bullets

## Slide: Hardware Closure
- Integrated core closed through staged bottleneck migration: SKAG first, then FDPE.
- tc5 achieved approximately 101.885 MHz at post-synthesis.
- OOC post-route preserved timing closure at approximately 100.392 MHz.
- Claim carefully limited to **post-synthesis + OOC post-route validated core**, not full board demo.

## Slide: Evaluation Headline
- Strongest classical baseline: **key-aware shortest path**.
- Random valid path is only a weak sanity-check baseline.
- Recommended software PMO-GA thesis variant: **ga_tcheby_pick_default**.

## Slide: What Changed After Selection-Policy Study
- Earlier PMO-GA collapse was strongly influenced by latency-first final selection.
- Weighted Tchebycheff selection made PMO-GA separate from key-aware on a meaningful subset of cases.
- Honest win: **better tradeoff handling**, especially balance / load spreading.

## Slide: Best Current Quantitative Cases
- Best balance case: depletion_plus_stricter_fidelity / irregular12, load-balance delta = -0.145170.
- Best fidelity case: current_like / mesh16, fidelity delta = 0.000444.
- Best latency-improvement case: depletion_plus_stricter_fidelity / irregular12, latency delta = -0.002931.

## Slide: Honest Takeaway
- QFlow hardware result is strong and thesis-worthy.
- Current evidence supports **multi-objective tradeoff benefits**, not universal dominance on every metric.
- Best paper-safe claim: **100 MHz-class validated QFlow core with tradeoff-aware routing benefits over simpler baselines**.
