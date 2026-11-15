# Scientific evaluation protocol — freeze before Stage 5 held-out run

## Primary question
Under equal action availability, costs, rewards, scenario distributions and resource budgets, does joint uncertainty reasoning plus decision-focused VOI **reduce false scientific conclusions and decision regret** while preserving useful discovery recall?

## Registered comparisons
1. **Fixed-model baseline:** assumes instruments and scientific model are reliable; respects identical resource constraints.
2. **Information-gain baseline:** chooses expected entropy reduction as objective; same observation model and feasible actions, except where method's assumptions are explicitly declared.
3. **Threshold verification:** rule-based confidence thresholds for verify/calibrate/conclude; thresholds determined on development data.
4. **AURORA:** joint geology + sensor reliability + model adequacy with decision-focused VOI.
5. **Oracle:** privileged simulator-truth reference only; **not** a feasible fair comparator or a production policy.

## Fairness and split strategy
- Separate tuning/development scenario seeds from a frozen held-out evaluation suite. Store full split manifest and prevent leakage.
- Prefer paired episode design with matched scenario seeds and config; handle policy-dependent action paths by sharing exogenous world configuration and documented keyed observation noise rather than requiring identical action histories.
- All policies get same initial public priors (except explicitly documented baseline assumption), budgets, time horizon, action availability and terminal scoring rules.
- Freeze priors, reward weights, thresholds, likelihoods, baseline behavior and data definitions before held-out scores. Code bug fixes after seeing held-out results require a disclosed rerun/version, not silent tuning.
- Default exploratory 100 paired development episodes per scenario and planned ~500 held-out paired episodes/scenario if practical; adapt based on CPU cost and uncertainty/precision, **never invent completed runs**.

## Metrics (all with sample sizes and denominators)
- **False conclusion rate (false discovery proportion):** number of asserted positive discoveries that are incorrect / number of positive discovery assertions. `N/A` if no positive claims. Report separately from **false-positive episode rate** (false positive claims / all relevant negative episodes).
- **Discovery recall:** correct positive discoveries / total truly positive episodes. Include missed discoveries and number of abstentions.
- **Decision accuracy:** correct terminal scientific conclusions / all eligible episodes; report decision coverage and selective accuracy separately so abstention is visible.
- **Fault / model-adequacy detection:** TP, FP, TN, FN, precision/recall/F1 at prespecified threshold; prevalence and threshold disclosed. Report per-fault type where feasible.
- **Calibration:** Brier score for relevant binary event plus reliability diagram or expected calibration error with bin choice explained.
- **Decision utility/regret:** same explicit final reward/cost score across policies. Oracle regret `oracle utility - policy utility`; note negative values if oracle is merely heuristic rather than true optimum.
- **Resources:** mean/median energy & time per correctly supported conclusion; `N/A` when denominator zero; percent missions within budget.
- **Runtime:** elapsed decision latency median, p95, CPU model, Python version, package versions. Do not claim mission real-time control from a local simulator timing benchmark.
- **Robustness:** stratify by noise, bias, drift magnitude, omitted hypotheses, budget, seed and sensor conflicts.

## Statistical reporting
Compute **paired policy differences at the mission-episode level** (not one CI per observation as though independent). Provide 95% episode-level bootstrap CIs with documented resample count and RNG seed. For each figure/table, include sample size, conditions, uncertainty, computation budget and limitation. If results fail targets, report clearly.

## Ablation design
- Remove fault belief modeling.
- Remove model adequacy diagnostics.
- Replace VOI with entropy reduction.
- Remove or zero resource penalties (interpret with caution: changes objective and may alter budgets, so keep feasibility constraints intact).
Document what is disabled and which effects remain coupled. No data leakage from private truth into deployable policies.

## Targets, not claims
- Aspirational: >=20% relative drop in false conclusion proportion vs strongest non-oracle comparator, **conditional on comparable discovery recall**.
- >=15% relative decrease in regret on matched tasks.
- Model-error detection F1 >=0.80 on prespecified simulated labels.
- Median planning decision latency <=1 second on documented CPU.
These targets are optional hypothesis probes; do not manipulate benchmarks or reporting to reach them. Achievement unknown until measured.

## Real planetary data validation
Prefer official NASA PDS resources if compatible. Confirm archive, product ID, instrument, units, calibration/quality fields, license/terms, download date and reproducible adapter schema. Real observations without ground truth cannot establish real-world fault precision/F1 or discovery classification accuracy. Record external plausibility checks distinctly. If dataset infeasible, state that clearly and don't claim hybrid validation completed.

## Final outputs
- `results/` machine-readable config, aggregated metrics, denominators/CIs, per-scenario comparisons, ablation summaries and trace references. Large runs locally ignored by Git; commit tiny curated reproducibility examples.
- `docs/RESEARCH_RESULTS.md` created **only once measurements exist**, including experimental methods, tables, negative findings, threats to validity and reviewer-ready reproducibility commands.
- Dashboard demo: genuine unexpected geology, sensor-induced false alarm, omitted-hypothesis caution, baseline comparison with visible decision rationale.
