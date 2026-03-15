# Phase 0 open issues / freeze items

- Unit tests currently pass, so the model is stable enough to serve as the verification anchor.
- Q0.16 saturation convention is 0..65535, not a true mathematical [0,1] fixed-point with exact 1.0. Freeze this explicitly in the contract.
- LUT depth is 256, consistent with the architecture and thesis plan.
- LUT domain is [0,8], matching the current plan and architecture description.
- The file describes itself as cycle-accurate. Keep this wording conservative in the thesis unless cycle-level timing equivalence is actually proven.
- A docstring still mentions nearest-neighbour as an option, but the implemented LUT path performs linear interpolation. Freeze the implementation as linear interpolation everywhere.
- The Python model includes TSN scheduling logic. In the thesis scope freeze, keep QP-TSN as extension unless the core path finishes early.
- The default ring experiment reports many duplicate Pareto solutions. This is acceptable now, but later evaluation scripts should deduplicate fronts before publication figures.
- You still need a frozen default seed/config file so that all future vectors and plots are reproducible.
- You still need an explicit alpha-coefficient table and address-map freeze before FDPE/SKAG/GA RTL begins.
