# Research improvement — Step 1 report

Status: READY_FOR_REVIEW. Step 2 is blocked pending user approval. This report
contains development diagnostics, not the final research benchmark.

## Root causes

1. The original calibration action resets the physical spectrometer and maps
   its fault posterior to healthy *before* taking a science reading. It never
   observes the initial fault against a reference standard.
2. Original endpoint scoring compares that repaired-state posterior with an
   initial-fault truth label. Thus zero recall mixes intervention with diagnosis.
   BUG-002 correctly fixes fixed-model scoring and is preserved unchanged.
3. Original utility rewards geological conclusions, not fault identification.
   A cheap repair can be useful without identifying the removed fault. No new
   diagnosis reward was added to artificially favor the improved policy.
4. One sensor confounds geological means with sensor offsets. The original
   fixed positive bias/drift hypotheses omit negative and weaker faults;
   seven bins lose magnitude information and collapse all high outliers.
5. The original unknown likelihood is uniform over bins and independent from
   reading to reading. The easy outside preset does not test overlapping
   geological distributions. Unknown fault states are likelihood-unidentified.
6. Legacy discovery recall counts outside-family truth as discoverable while
   only allowing supported sulfate conclusions. Its 0.5 ceiling is a metric
   definition issue. That historical metric remains unchanged.

## Versioned corrections and assumptions

The original core, benchmark-2 manifest/results and BUG-002 test are unchanged.
`research_archive/benchmark2_source.zip` archives the original source;
`research_archive/preserved_hashes.json` verifies historical artifact bytes.

`research_model.py` implements a 196-state joint mixture: four geological
components times seven initial fault hypotheses per instrument. Fault support
includes healthy, constant offsets ±0.6 and ±1.5 index, and slopes ±0.5
index/hour. Priors are 0.8 healthy, 0.15 total constant bias and 0.05 total
drift per instrument. Known geology means retain the existing public model.
Unknown geology has persistent independent Normal(3, 2²) instrument means,
integrated through conjugate Gaussian updates. Continuous Gaussian measurement
likelihoods and log normalization retain reading magnitude. This adds modeling
assumptions; it does not claim a calibrated physical model. Predictive log
densities are recorded, not presented as calibrated p-values.

Initial fault identities remain latent throughout a mission. A separate
repair mask determines active fault probabilities. Reference evidence measures
a zero standard independent of geology, with the same synthetic bias/drift
and sensor noise as science measurements. That transferability and perfect
repair are assumptions requiring real instrument validation.

`research_mission.py` records a reference reading before a spectrometer reset
within the existing 4 Wh/2 h calibration cost. It also offers non-destructive
1 Wh/1 h reference checks. These are new information contracts, not newly
discovered simulator labels. The policy receives belief/evidence and public
resources, never a Case or generating means. A supported conclusion requires
science evidence from both instruments; insufficient budget permits abstention.
The utility remains +10 correct, -20 incorrect, 0 abstain, minus 0.15/Wh and
0.10/hour. Seven-node Gauss-Hermite integration approximates one-step terminal
VOI; calibration scoring conservatively omits the reference's extra value and
scores the post-reset science reading. These approximations need Step 2
resolution sensitivity and matched-contract comparisons.

The 0.5 fault/unknown thresholds are inherited, not selected against final
data. Development Brier scores, reliability bins and threshold sensitivity are
reported. They are diagnostics, not evidence that probabilities are calibrated.
Supported sulfate recall and unsupported-geology identification are now
separate diagnostic metrics; legacy benchmark-2 remains intact.

## Development diagnostics

Frozen settings: `configs/research_step1.json`, seeds 200–209, disjoint from
all benchmark-2 seed partitions. No final partition was created or evaluated.
The new cases include overlapping unknown means, an exact observational alias,
boundary unknown geology, combined unknown plus bias, high noise, weak and
negative bias, and both instruments faulty. Private generating means only
enter the simulator. None of the old preset truth values were changed.

| Diagnostic, same six original presets / 60 development episodes | Original VOI | Audit model/policy |
| --- | ---: | ---: |
| Initial fault TP / faulty episodes | 0 / 30 | 21 / 30 |
| Initial fault FP / healthy episodes | 0 / 30 | 1 / 30 |
| Initial fault precision | N/A | 95.45% |
| Initial fault recall | 0% | 70.00% |
| Initial fault F1 | N/A | 0.8077 |
| Correct conclusions / all episodes | 48 / 60 | 50 / 60 |
| Wrong claims | 0 | 0 |
| Abstentions | 12 | 10 |
| Mean original utility | 6.7333 | 7.1567 |
| Unsupported-geology recall on easy outside preset | 100% | 100% |
| Supported sulfate recall, corrected denominator | 100% | 100% |

These before/after runs share case/seed settings but the improved pipeline
collects a reference reading and requires cross-instrument evidence. Therefore
they do not isolate an inference-only causal effect and are not a final fair
ranking of policies. Step 2 must expose consistent observation contracts to
comparators and distinguish original-contract from matched-contract results.

Across all 14 development cases (140 episodes), the improved pipeline made
90 correct and 27 incorrect claims, abstained 23 times, and had mean utility
1.2693. Initial fault precision/recall/F1 were 0.9200/0.6571/0.7667.
Unsupported-geology precision/recall/F1 were 1.0000/0.4600/0.6301. The difficult
cases therefore remove the misleading impression of perfect unknown detection.
Initial-fault Brier score was 0.1295 and unknown Brier score 0.1771.

Historical fault evidence and active faults are separately recorded. On the
six matched presets, 30 initially faulty instruments were repaired; all 258
post-action instrument observations had healthy active truth and no positive
active predictions. Active recall is consequently undefined there. On all
cases the post-action instrument-time counts were TP 10, FP 6, TN 672, FN 16;
these repeated observations are not independent episodes and are not used to
inflate an episode sample size. Seventy initial instrument faults were removed.

## Failures and remaining limitations

- Initial continuous-only smoke runs could conclude after one sensor; a
  general two-instrument evidence precondition was added before diagnostic
  collection. It consumes resources and is itself a policy intervention.
- Drift recall is only 20% and weak-bias recall is 0% in development. A first
  reference at one hour often cannot identify weak drift. Diagnosis-only
  checks have limited VOI under the unchanged geological utility.
- The exact unknown alias produces identical observations and decisions to
  basalt, with 10 incorrect claims in 10 trials. No method can distinguish
  identical distributions from these measurements. A regression explicitly
  preserves this negative result.
- Overlap unknowns produced 7/10 incorrect claims, boundary unknowns 4/10,
  and combined unknown/fault cases 6/10. The model can abstain, but does not
  reliably recognize all unsupported geology.
- Lowering the fault threshold to 0.25 improves development recall to 84.29%
  but increases false positives to 15/70; 0.75 gives recall 60% and 0/70 false
  positives. The configured threshold remains 0.5 (recall 65.71%, FP 4/70).
  This tradeoff is recorded rather than optimized against held-out data.
- Unknown mean independence, finite fault support, perfect calibration and
  assumed noise remain model limitations. No real-world accuracy was added;
  the official APXS feasibility artifacts are unchanged.

## Verification and reproduction

Full suite: 145 passed, 0 failed, 0 skipped. All regressions: 24 passed.
New Step 1 checks: 16 unit, 3 regression, 16 integration/parameterized cases
(35 total), including audit dashboard truth isolation. Ruff passed; locked
dependency check passed. CI is configured but unexecuted because this directory
has no Git repository/remote. No commit was created; coverage was not measured.

```powershell
cd D:\Projects\Project_AURORA
python -m uv sync --locked --extra dev
python -m uv run --extra dev python -m pytest -q
python -m uv run --extra dev python -m ruff check .
python -m uv run --extra dev python -m aurora.research_diagnostics --output results/research_step1_diagnostics.json
python -m uv run --extra dev python -m streamlit run src/aurora/dashboard/research_app.py
```

The result includes per-case rows, initial/active fault counts, threshold
sensitivity, predictive calibration diagnostics and representative evidence
replays. Configuration SHA-256:
`f9ae999a46da7f694b6f00079006d11b474a87e3322f26c5b9324834a0df3a0e`.
Source SHA-256 (relative source path + file bytes, sorted):
`5f7e929922d25e6d4d84ffc51772374b73caea0a0f7aa059760a093371c619d2`.
All archived baseline artifact hashes match.

Step 2 remains unstarted: no new final benchmark, held-out tuning, final report,
robustness claim, or additional real-data validation has been performed.
