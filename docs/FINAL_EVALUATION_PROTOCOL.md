# Frozen Step 2 protocol — research-final-2

`configs/research_final_v2.json` is frozen before any new final seed is executed.
Original benchmark-2 and BUG-002 remain unchanged. There are exactly two user
steps; Step 2 is authorized and introduces no additional approval stages.

## Comparison and samples

Final: 20 families × 50 seeds (10000–10049) × five policies = 5,000 episode rows,
1,000 per policy. Development uses only the 14 Step 1 families and 20 seeds
(9000–9019). Six `unseen_*` families are excluded from development. Robustness
and ablations use separate seeds 12000–12009. All partitions are disjoint from
the original benchmark and Step 1 seeds. No final-set parameter search occurs.

Every matched policy has identical five acquisition actions, budgets, horizon,
keyed noise, pre-reset reference readings, perfect repair and two-instrument
verification. The legacy composite `discriminate` is excluded for all matched
policies. Calibration is 4 Wh/2 h, including reference and science; checks are
1 Wh/1 h. Noise uses SeedSequence(seed, instrument, within-kind count, kind,
128-bit SHA-256 case-name key). Cases have independent streams; policies share
streams within each case. The earlier v1 streams reused noise across cases,
which conflicted with independent-case interval assumptions. V1 source,
outputs and partial checkpoints are preserved as superseded. The sampling
correction uses fresh untouched partitions and changes no policy parameters;
final aggregate scores had not been inspected when it was identified.
Private generating parameters never enter the policy interface.

Policies: improved continuous VOI; original binned VOI adapted to the common
contracts; binned information gain; fixed healthy-instrument model; and the
original 0.85 threshold with matched verification/feasibility. The legacy
adapter retains 36-state fault support, seven bins and original priors. It
supports reference evidence and preserves initial identities through repair
for consistent diagnosis timing. It is not labeled an unchanged original run.
The untouched original VOI runs separately on six original families × 50 final
seeds as a historical bridge, never mixed into the matched ranking.

Primary utility stays +10 correct, -20 incorrect, 0 abstention, minus 0.15/Wh
and 0.10/hour. Regret uses the same privileged offline reference, 10 for known
truth and 0 for unsupported truth. Costs count once. Fault/unknown thresholds
stay 0.5. There is no bonus for diagnosis or discovery.

## Metrics and uncertainty

Report conclusion accuracy including abstention, selective accuracy, coverage,
false-conclusion proportion, supported sulfate recall, and unsupported-geology
precision/recall/F1 separately. Initial fault diagnosis is scored against
initial truth without erasing history. Active faults are scored before repair
and after each action against contemporaneous truth. Repeated instrument-times
are clustered inside each resampled episode. Brier scores, costs, removed-fault
counts and actual selection-call latencies are included.

Wilson 95% intervals describe episode proportions. Case-stratified episode
bootstrap (1,000 replicates, seed 42026) describes mean utility, regret,
resources, F1 and paired differences. Active-fault intervals resample episode
clusters. Latency median/p95 is descriptive. Intervals reflect noise sampling
within fixed families, not uncertainty about the whole planetary environment.

## Controlled components and robustness

Seven ablation arms share 20 families × 10 separate seeds: nominal,
no-reference evidence (same generated readings/costs, ignored by inference),
no-fault prior support, no-unknown support, no-verification gate, no-resource-
penalty ranking, and information-gain ranking. Each changes one named component;
feasibility and realized scoring costs stay fixed. Gate removal changes policy
safety; no-cost changes ranking utility, not physical budgets.

Sixteen frozen sensitivity arms cover unknown and healthy-instrument priors,
noise magnitude and misspecification, bias/drift severity, wrong-claim penalties,
and 7 versus 15 quadrature nodes. Six development families × ten robustness
seeds per arm. Reward sensitivities are explicitly separate from the primary
ranking. Nominal parameters stay unchanged regardless of measured outcomes.

## Real measurements and reproducibility

Reuse the official PDS sol-46 APXS product. Preserve each analyte's concentration,
statistical precision, label units, timestamp and hashes. Do not equate precision
with total accuracy or invent covariance, geology/fault labels or an APXS
likelihood. The permitted conclusion is a documented feasibility demonstration.

Completed outputs cannot be overwritten. JSONL checkpoints resume only under
identical config and source hashes; partial test runs are flagged. Full source
and config snapshots, per-episode rows, CSV summaries and negative results
accompany the final report.
