# Final Mathematical Correction Report

## Equation 3.10

The pre-pass thesis source at commit
`ad16401908bd3227fa43527f18ae4c44907ff455` already displayed the reciprocal form:

```text
c_i^(k) = sum(alpha1/K + alpha2/Q + alpha3/R + alpha4 B).
```

It did not, however, fully specify units, invalid denominators, saturation, or the
different places where the coefficients do and do not execute. The nonreciprocal
form raised for investigation, `alpha1/K + alpha2 Q + alpha3 R + alpha4 B`, is not
the authoritative implementation and has not been introduced into the thesis.

The final Equation 3.10 remains the code-supported expression

```text
c_i^(k) = sum over links in route i of
          (alpha1^(k)/K_uv + alpha2^(k)/Q_uv
           + alpha3^(k)/R_uv + alpha4^(k) B_uv).
```

The correction pass makes its semantics explicit:

- `K_uv`: integer available-key count.
- `Q_uv`: dimensionless bounded route-quality value in `[0,1]`.
- `R_uv`: positive synthetic key-rate contract value; the training generator uses
  3--9 without claiming a calibrated physical unit.
- `B_uv`: dimensionless synthetic QBER in `[0,1]`.
- Software infeasibility: any link with `K < 1`, `Q < 0.90`, or `R <= 0` rejects the
  candidate before evaluating the reciprocal sum.
- Fixed-point zero denominator: exported cost is `0xFFFFFFFF` (infinity).
- Finite cost overflow: saturation at `0xFFFFFFFE`.

## Source implementation

The formula and guards were checked at evidence commit
`290b4ad75eef2af2b9da2f1f281a2b89416cfd24` in:

- `rl/ring6_environment.py::_path_objectives`;
- `reference_model.py`;
- `tools/generate_p5_b3_skag_vectors.py`;
- `docs/rl/p5_qflow_mini_contract.md`; and
- `rl/config/p5_qflow_mini_contract_v1.json`.

## Where alpha coefficients are used

During offline training, a selected profile's four alpha coefficients construct
profile-dependent candidate costs. The same profile's three Tchebycheff ratios then
weight path-cost, route-quality-deficit, and utilization objectives. All seven
profile parameters can therefore affect a software-training decision.

## Where alpha coefficients are not used

In the completed physical replay, candidate path cost is supplied precomputed and is
common across profiles. `rtl/spartan6/p5_b5_policy_shell.v` supplies only profile
bits `[5:0]` to the candidate evaluator. Consequently, alpha bits `[17:6]` do not
affect H2--H4 physical selection, and Equation 3.10 is not computed by the FPGA
candidate-evaluation datapath.

## Fixed-point range correction

- Path cost: UQ16.16 code `0xFFFFFFFF` is reserved for infinity. Maximum finite code
  `0xFFFFFFFE` represents `2^16 - 2^-15`.
- Utilization: UQ16.16 uses the complete unsigned range. `0xFFFFFFFF` is an ordinary
  maximum value representing `2^16 - 2^-16`, not infinity.

Table 3.1, Appendix Table B.3, and surrounding prose now apply these conventions
separately rather than transferring the path-cost sentinel to utilization.
