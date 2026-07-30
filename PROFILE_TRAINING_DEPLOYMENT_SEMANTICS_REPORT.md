# Profile Training/Deployment Semantics Report

## Finding

The authoritative implementation is **Case B**. An offline training action uses the
complete profile: four path-cost coefficients and three Tchebycheff objective
weights. The completed physical FPGA experiment deploys only the three objective
ratios because candidate path cost is supplied externally and is common across
profiles.

## Training action

For action/profile `Pi_k`, `rl/ring6_environment.py::_path_objectives` constructs
each candidate cost as

```text
sum(alpha1 / key_count
  + alpha2 / quality
  + alpha3 / key_rate
  + alpha4 * qber)
```

`Ring6Environment.step` obtains the selected profile, calls `_path_objectives` with
that profile, and then calls route selection with the same profile's three
Tchebycheff weights. Thus all four alpha values and all three ratios can change the
training decision.

The software excludes a path containing key count below 1, route quality below
0.90, or nonpositive synthetic key rate before applying the reciprocal formula.

## Deployment action

The physical request supplies candidate validity, precomputed UQ16.16 path cost,
UNORM16 route quality, UQ16.16 utilization, hop count, and candidate slot.
`rtl/spartan6/p5_b5_policy_shell.v` passes only profile payload bits `[5:4]`,
`[3:2]`, and `[1:0]` to `rtl/spartan6/p5_b4_candidate_evaluator.v`. Bits `[17:6]`
are not used by the physical candidate evaluator. The three ratios weight supplied
path cost, route-quality deficit, and utilization respectively.

## Bit use

| Payload bits | Meaning | Training | Physical candidate selection |
|---|---|---|---|
| `[17:15]` | alpha 1 | Used | Not used |
| `[14:12]` | alpha 2 | Used | Not used |
| `[11:9]` | alpha 3 | Used | Not used |
| `[8:6]` | alpha 4 | Used | Not used |
| `[5:4]` | path-cost ratio | Used | Used |
| `[3:2]` | route-quality-deficit ratio | Used | Used |
| `[1:0]` | utilization ratio | Used | Used |

The four payloads are `0x13329`, `0x1B516`, `0x14399`, and `0x0A2A5`.

## Numerical profile meaning on the FPGA

- Pi0 Balanced uses ratio `(2,2,1)`.
- Pi1, registered as Scarcity protection, uses `(1,1,2)` and therefore places its
  strongest direct deployed emphasis on utilization/scarcity management.
- Pi2, registered as Fidelity protection, uses `(1,2,1)` and places its strongest
  deployed emphasis on route-quality deficit.
- Pi3, registered as Low-latency, uses `(2,1,1)` and places its strongest deployed
  emphasis on supplied path cost. The name does not imply fewer FPGA cycles.

## Authoritative sources

All implementation sources below are from evidence commit
`290b4ad75eef2af2b9da2f1f281a2b89416cfd24`:

- `rl/ring6_environment.py`
- `rl/profile_codebook.py`
- `rl/config/profile_codebook_v0.json`
- `rtl/spartan6/p5_b5_policy_shell.v`
- `rtl/spartan6/p5_b4_candidate_evaluator.v`
- `rtl/spartan6/p6_physical_campaign_core.v`
- `reference_model.py`
- `docs/rl/p5_qflow_mini_contract.md`
- `rl/config/p5_qflow_mini_contract_v1.json`

## Thesis wording and remaining limitation

The abstract, Chapters 1--5, and Appendices B and C now distinguish the complete
software-training action from its ratio-only physical projection. They state that
physical exactness proves agreement with the ratio-only reference contract, not
equivalence to the full training-environment action or on-chip evaluation of the
alpha-dependent path-cost equation.

The remaining limitation is architectural: the completed physical shell did not
implement profile-conditioned path-cost construction. Closing that gap would require
either adding the cost function to the hardware boundary or training against the
same profile-independent supplied costs used in deployment.
