# QFlow Phase 0 Freeze Report

Overall status: PASS

## Gate checks
- unit_tests_passed: PASS
- tests_ran_nonzero: PASS
- ring6_command_ok: PASS
- constant_FIDELITY_BITS: PASS
- constant_FIDELITY_SCALE: PASS
- constant_WEIGHT_FRAC_BITS: PASS
- constant_WEIGHT_SCALE: PASS
- constant_LUT_ENTRIES: PASS
- constant_LUT_X_MAX: PASS
- constant_INF_WEIGHT: PASS
- lut_rel_error_below_0p1pct: PASS
- lut_first_entry_full_scale: PASS

## Frozen decisions
- Mandatory core remains FDPE + SKAG + PMO-GA + top-level wrapper. QP-TSN remains extension and must not block thesis completion.
- Fidelity arithmetic is frozen as Q0.16 unsigned with saturation 0..65535.
- Weight arithmetic is frozen as Q16.16 unsigned with 0xFFFF_FFFF as the infinity sentinel.
- FDPE LUT is frozen at 256 entries over x in [0, 8) with step 1/32 and piecewise-linear interpolation.
- Ring-6 reproducibility seed is frozen as 42, with the current GA defaults and alpha coefficients captured in qflow_frozen_config.json.
- SKAG packed edge entry contract is frozen before RTL: {qber[63:48], arrival_rate[47:32], avg_fidelity[31:16], key_count[15:0]}.

## Current reproducibility anchor
- Unit tests passed: True (26 tests)
- LUT max abs error: 7.602303880457906e-06
- LUT max rel error: 0.00011526125605395905
- Ring-6 best path: [0, 5, 4, 3]
- Ring-6 best latency: 5.460344
- Ring-6 best fidelity: 0.928396
- Ring-6 pareto front size: 64
- Ring-6 convergence steps: 11

## Remaining wording / documentation actions
- Replace any claim of proven cycle accuracy with 'verification anchor' or equivalent conservative wording unless later validated cycle-by-cycle.
- Remove any stale reference to nearest-neighbour LUT behavior and document the implementation as piecewise-linear interpolation everywhere.
- Deduplicate Pareto fronts in future publication plotting scripts; the current duplicate-heavy front is acceptable for early verification.

## Imported issue log
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

## Next recommended implementation step
Generate the frozen LUT artifact and FDPE golden vectors, then begin fdpe.v + tb_fdpe.v against those vectors.