# P3 Step 8 Statistics, Utility Gate and Ablation Boundary

## Frozen held-out analysis

Step 8 reads the 12 checksum-bound Step 7 controller/trace rows. It does not
generate a new test trace, change the seed-229 controller or train another
candidate. H4-H2 and H4-H3 reward differences are paired by the four frozen
test seeds.

Each comparison reports the paired mean difference, a deterministic 10,000
replicate paired percentile-bootstrap 95% interval, exact two-sided paired
permutation p-value, Holm-adjusted p-value and paired Cohen's dz. With four
pairs, the smallest attainable exact two-sided p-value is 0.125. Consequently,
even four positive paired differences cannot support a p<0.05 superiority
claim. Positive effects are labelled descriptive with insufficient power.

## Utility decision

The predeclared adaptation, blocking, reward, fidelity, balance and switching
checks are evaluated without changing their thresholds. A complete pass with
insufficient statistical power authorizes the frozen H4 controller for P4 but
does not authorize the phrase "statistically superior."

H4's higher hop count and switch rate relative to forced-fixed H2 are disclosed
alongside its comparison with H3. No adverse metric is hidden.

## Defense-level ablations

Feature removal is a validation-only diagnostic. For one feature at a time,
the frozen policy's four actions across that feature's bins are marginalized by
deterministic modal action, leaving a controller independent of that feature.
The resulting policy is evaluated on the four validation traces with dwell 3.

Reward-term removal counterfactually rescores the unchanged frozen H4
validation trajectory after deleting one decomposed term. It does not claim the
causal effect of retraining. Dwell 1 and dwell 3 are compared on the validation
set. A broader retrained journal ablation matrix remains J2 work.

## Scope firewall

Step 8 performs no post-test revision, additional training, model selection,
ROM export, RTL, synthesis, board work, commit or push.
