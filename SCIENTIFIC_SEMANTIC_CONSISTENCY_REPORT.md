# Scientific Semantic Consistency Report

## Scope and authority

This second-pass review treats branch `rl-nexys3-adaptive`, commit
`290b4ad75eef2af2b9da2f1f281a2b89416cfd24`, as the authoritative snapshot for
the completed controller and Nexys 3 experiment. The review covered the registered
model card, selection and freeze records, training/reward configuration, threshold
and profile manifests, policy/profile ROMs, H3 rules, H4 RTL/reference behavior,
physical replay summaries, and the compact submission extracts in `data/`.

No artifact chain was found for a corrected replenishment controller that was
retrained, re-exported, reverified, rebuilt, and physically replayed. Decision rule B
therefore applies.

## Semantic decisions

| Item | Executed meaning retained in the thesis | Check |
|---|---|---:|
| H4 feature 0 | Minimum key occupancy | PASS |
| H4 feature 1 | Bounded bottleneck route-quality code from the registered experimental contract | PASS |
| H4 feature 2 | Offered request load | PASS |
| H4 feature 3 | Utilization imbalance | PASS |
| Profile Pi0 | Balanced | PASS |
| Profile Pi1 | Scarcity protection | PASS |
| Profile Pi2 | Fidelity protection, retained as the registered identifier and limited to route-quality-code emphasis | PASS |
| Profile Pi3 | Low-latency, meaning path-cost/hop preference rather than FPGA evaluation latency | PASS |
| Runtime learning | None; H4 performs frozen policy-ROM inference with minimum-dwell control | PASS |

The route-quality feature is not called replenishment, key-generation condition, or
stored-key quantum fidelity. The thesis states that it is an abstract bounded
controller input used in the completed experiment. The registered word “fidelity” is
retained only where it is part of a historical artifact identifier or profile name,
and its experimental interpretation is constrained explicitly.

## Model separation

The revised thesis separates two scopes throughout:

1. The final network-control model uses classical key-pool occupancy, generation,
   consumption, status, utilization, policy freshness, and externally supplied health
   indicators.
2. The completed H4 hardware experiment uses the registered four-feature controller
   contract to establish policy-ROM inference, fixed-point exactness, timing,
   resources, and adaptive behavior.

No stored-classical-key coherence-decay model is presented as the final network model.
No legacy quantity is renamed and offered as corrected-model evidence.

## Reward, controller, and protocol consistency

- The Q-learning update and the complete immediate-reward equation are both present.
- Success, blocking, profile-change, route-quality, balance, and hop terms retain the
  registered signs, coefficients, clipping, and conditional evaluation.
- The original evaluation reward is distinguished from the validation-only balance
  coefficient revision used to select seed 229.
- The radix-4 thresholds, equality behavior, state address construction, profile
  payloads, H0-H4 definitions, H3 first-match rules, H4 dwell behavior, and
  deterministic tie breaking are stated at implementation precision.
- The physical request/response contract identifies all statuses and all nine checked
  fields. It excludes host, UART serialization, KMS/SDN, candidate generation, and
  route-installation time from kernel latency.

## Result-claim consistency

- Five independent H0-H4 implementations are described, not one reconfigured result.
- The 420-record, 3,780-field exactness claim is limited to physical/reference field
  agreement.
- Route-quality differences remain in UNORM16 units and are also expressed as
  normalized changes. Both confidence intervals cross zero; route-quality superiority
  is not claimed.
- H4 resource/timing/adaptation claims are configuration-specific and do not imply a
  universal FPGA advantage.
- OpenROAD areas are reported for three isolated kernels and are not summed into a
  QFlow chip area. The repository identifier FDPE-V3 is described as a
  LUT/interpolation arithmetic kernel, not as current QFlow functionality.

## Residue and terminology checks

Removed or excluded from the research narrative: PMO-GA, FDPE as a general
abbreviation, historical Artix-7 claims, historical OMNeT++ results, project timeline,
claim ledger, prepared defense answers, model-correction chronology, and the sentence
advertising the old numerical-audit report. P0-P6 identifiers remain confined to
repository traceability.

## Disclosed limitations

The physical bootstrap confidence intervals were recomputed from the available raw
paired rows using 10,000 paired-row replicates, MT19937 seed 20260731, and declared
percentile quantiles. No authenticated board photograph is used as thesis evidence.
The verification ladder, architecture, trade-off,
confidence-interval, and routed-layout figures provide the required technical visuals.

## Outcome

PASS. The revised thesis presents the executed controller directly, keeps the final
network model distinct, and makes no semantic relabelling that would convert legacy or
synthetic data into corrected-model evidence.
