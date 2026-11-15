# Complete stage-by-stage test specification

**This is a REQUIRED TEST INVENTORY, not a claim tests already exist.** Codex must implement each ID as executable tests in `tests/unit`, `tests/regression`, or `tests/integration` during the authorized stage, using meaningful assertions, deterministic fixtures and synthetic/hand-computed ground truth. Keep earlier test cases and run the entire suite every stage. Use `pytest.mark.parametrize` when useful, but preserve ID traceability in test names/docstrings or a test matrix. Every fixed defect adds a `BUG-...` regression ID.

## Common testing rules
- No test makes network calls, requires paid APIs or relies on GPU. Real-data adapter tests use a tiny checked-in permissibly redistributable fixture with provenance, or synthetic **explicitly labeled** fixtures.
- Use absolute/relative tolerances for floats; no exact equality for probabilistic computations except deterministic serialized bytes when schema is canonicalized.
- Separate agent-visible data and simulator private truth in function signatures and fixture types. Include structural leakage tests.
- Every test IDs must resolve to a named test. Codex must report count by category and any IDs missing/skipped with reason.
- At stage boundary `uv run pytest -q`, `uv run pytest tests/regression -q`, `uv run ruff check .`; CI must run tests and lint.
- Suggested unit/scientific branch coverage: **>=90% for new core scientific modules**, measured with `pytest-cov` when practical. Coverage is diagnostic, not a substitute for correct scientific assertions. No forced 100% if unreachable/platform branches are justified.

## Stage 1 — Simulator

| ID | Type | Test and expected assertion |
| --- | --- | --- |
| S1-U01 | Unit | Valid geology / instrument / observation schemas accept valid units and reject unknown states. |
| S1-U02 | Unit | Invalid budgets, NaN or negative measurement noise, invalid horizon/seed/config trigger meaningful errors. |
| S1-U03 | Unit | Same RNG seed + identical config/action sequence produce same observations and trace metadata. |
| S1-U04 | Unit | Different seeds generate variable stochastic observations for a nondegenerate noisy config; avoid flaky single comparison using several seeds. |
| S1-U05 | Unit | Healthy instrument observation expectations/variance agree with configured generative law within statistical tolerance, or use mocked RNG for exact path. |
| S1-U06 | Unit | Fixed bias shifts measurements by specified value and doesn't mutate hidden geology. |
| S1-U07 | Unit | Drift evolves correctly with time; drift reset/calibration semantics are explicit (if calibration is deferred, test the state transition primitive). |
| S1-U08 | Unit | Instrument-specific likelihood/measurement parameters distinguish two instruments. |
| S1-U09 | Unit | Action/resource accounting deducts correct energy/time once and refuses overspend/negative residual. |
| S1-U10 | Unit | Finite mission horizon and terminal conditions stop additional observations. |
| S1-U11 | Unit | Out-of-family generated geological truth remains separate from supported hypothesis labels. |
| S1-U12 | Unit | Agent-visible trace lacks secret ground truth fields and copies/serialization do not expose hidden states. |
| S1-R01 | Regression | Fixed seed `ordinary` scenario matches a versioned, minimal normalized observation trace fixture. |
| S1-R02 | Regression | Fixed seed `bias` and `drift` sensor traces retain documented output/statistics. |
| S1-R03 | Regression | Budget exhaustion trace produces stable stop reason and resource balance. |
| S1-R04 | Regression | JSON export/import preserves agent-visible trace, config/seed/schema version; no hidden-state leakage. |
| S1-I01 | Integration | CLI starts from clean environment and exits 0 on valid scenario, produces parseable structured trace. |
| S1-I02 | Integration | CLI rejects invalid scenario/config with nonzero code and useful diagnostic. |
| S1-I03 | Integration | All registered scenarios run headlessly with finite termination on CPU. |

## Stage 2 — Dashboard

| ID | Type | Test and expected assertion |
| --- | --- | --- |
| S2-U01 | Unit | UI control parsing accepts valid scenarios and rejects invalid inputs/ranges. |
| S2-U02 | Unit | Graph adapter x-axis time index is ordered and observation values match trace. |
| S2-U03 | Unit | Multi-instrument lines remain correctly associated with their instrument labels and units. |
| S2-U04 | Unit | Resource plot matches simulator history exactly and never dips below zero. |
| S2-U05 | Unit | Displayed event log preserves action, provenance and timing. |
| S2-U06 | Unit | Default adapter excludes private truth from visible charts/tables and downloads. |
| S2-U07 | Unit | Truth-inspection view is opt-in, clearly flagged, and isolated from agent-view data. |
| S2-U08 | Unit | CSV/JSON export contains version, seed, scenario, config and valid observations, preserving row order. |
| S2-U09 | Unit | Empty/single-step/large-but-reasonable trace can render without exceptions or misleading values. |
| S2-R01 | Regression | Stable plotting dataset from fixed seed matches approved trace fixture. |
| S2-R02 | Regression | Reset/rerun with same seed does not mix prior Streamlit session traces. |
| S2-R03 | Regression | Download export round-trip remains compatible with the stage schema. |
| S2-I01 | Integration | Streamlit AppTest (or justified equivalent) loads the dashboard and required controls. |
| S2-I02 | Integration | Scenario switch updates traces/graphs deterministically without corrupting previous state. |
| S2-I03 | Integration | UI service layer produces same trace as CLI for identical config and seed. |

## Stage 3 — Belief engine and adequacy

| ID | Type | Test and expected assertion |
| --- | --- | --- |
| S3-U01 | Unit | Priors accept only finite nonnegative probability vectors summing to one within tolerance. |
| S3-U02 | Unit | Discrete likelihoods are nonnegative, normalized and finite for all supported states/actions. |
| S3-U03 | Unit | Hand-worked Bayes example returns analytically calculated posterior within numeric tolerance. |
| S3-U04 | Unit | Sequential update matches hand-derived or batch equivalent for conditionally independent samples. |
| S3-U05 | Unit | Posterior sums to one and contains no NaN/Inf under ordinary observations. |
| S3-U06 | Unit | Nearly zero/zero likelihood handled by defined fallback/error rather than silent nan or arbitrary certainty. |
| S3-U07 | Unit | Log-domain numeric stabilization handles extreme but finite likelihood ratios. |
| S3-U08 | Unit | Fault-free synthetic evidence gives plausible posterior behavior (probabilistic expectation, not guaranteed one-case perfection). |
| S3-U09 | Unit | Fault evidence shifts sensor-health beliefs appropriately on diagnostic toy input. |
| S3-U10 | Unit | Conflicting sensors preserve uncertainty rather than forcing certainty with a bad prior. |
| S3-U11 | Unit | Unknown/missing-model diagnostic catches a constructed high-discrepancy example and records false-alarm controls. |
| S3-U12 | Unit | Posterior predictive values are normalized and calculated from the stated model, not simulator truth. |
| S3-U13 | Unit | Inference output includes explicit observation provenance, uncertainty/limits, and no private state reference. |
| S3-R01 | Regression | Fixed toy analytic posterior remains unchanged unless a documented model version changes. |
| S3-R02 | Regression | Fixed-seed healthy/fault posterior trajectory fixtures remain consistent. |
| S3-R03 | Regression | Missing-hypothesis scenario produces documented adequacy behavior on test fixture. |
| S3-R04 | Regression | Irrelevant changes to private truth metadata don't affect belief results with same visible trace. |
| S3-I01 | Integration | Simulation observation feeds inference under typed agent-only API. |
| S3-I02 | Integration | Posterior data adapter renders valid probability and warning traces in dashboard. |
| S3-I03 | Integration | Replaying saved visible history yields identical posterior trajectories. |
| S3-I04 | Integration | Deliberate private-truth mutation has no effect on inferred beliefs/actions; no forbidden interface fields. |

## Stage 4 — Actions, VOI, mission and baselines

| ID | Type | Test and expected assertion |
| --- | --- | --- |
| S4-U01 | Unit | Every action has explicit preconditions, cost, effect and legal terminal/nonterminal class. |
| S4-U02 | Unit | Feasibility rejects unaffordable or unavailable actions before ranking. |
| S4-U03 | Unit | Reward/terminal expected utility in hand-constructed belief state matches explicit reward table. |
| S4-U04 | Unit | One-step VOI from tiny discrete worked example matches hand calculation. |
| S4-U05 | Unit | Predictive observation probabilities for candidate action sum to one. |
| S4-U06 | Unit | Action costs are subtracted exactly once, including calibration and communication. |
| S4-U07 | Unit | Zero-resource budget selects legal terminal choice; does not loop. |
| S4-U08 | Unit | Finite horizon forces terminal decision or explicit safe stop. |
| S4-U09 | Unit | Deterministic tie-breaking chooses stable action and records tie rationale. |
| S4-U10 | Unit | Calibration changes instrument/observation dynamics as documented and consumes correct cost. |
| S4-U11 | Unit | Independent sensor cross-check uses correct distinct observation model. |
| S4-U12 | Unit | Unknown hypothesis uncertainty can favor abstention/verification under configured utilities. |
| S4-U13 | Unit | Fixed-model baseline ignores reliability in declared way but respects budgets/availability. |
| S4-U14 | Unit | Information-gain and threshold baseline selection obey documented criterion on toy examples. |
| S4-U15 | Unit | Privileged oracle is inaccessible from ordinary planner and deployable baseline APIs. |
| S4-R01 | Regression | Small, hand-checkable VOI fixture and chosen action are stable. |
| S4-R02 | Regression | Same scenario+seed+policy reproduces full action sequence and stop reason. |
| S4-R03 | Regression | Budget-limited mission never overspends and terminates in bounded steps. |
| S4-R04 | Regression | Changing hidden evaluation truth metadata only leaves policy decisions unchanged given same observations. |
| S4-I01 | Integration | End-to-end agent mission executes until terminal decision, safe stop or bounded horizon. |
| S4-I02 | Integration | Every baseline receives the same legal action types/resource contracts and only visible state. |
| S4-I03 | Integration | Dashboard step/autoplay reflects actual action utilities, belief updates and resource changes. |
| S4-I04 | Integration | Full trace replay reproduces selected actions, belief path, costs and terminal conclusion. |

## Stage 5 — Benchmarks, statistical evaluation, real-data adapter

| ID | Type | Test and expected assertion |
| --- | --- | --- |
| S5-U01 | Unit | False-positive discovery rate computes exact numerator/denominator on known contingency table. |
| S5-U02 | Unit | Discovery recall and miss rate use explicit positive truth population denominator. |
| S5-U03 | Unit | Precision, recall and F1 for instrument faults work on known confusion matrix. |
| S5-U04 | Unit | Adequacy/unknown model detection precision/recall/F1 calculated correctly on labels. |
| S5-U05 | Unit | All-zero predictions/positives and undefined rates return labeled `N/A`, not fabricated zero. |
| S5-U06 | Unit | Abstention fraction, decision accuracy and coverage reported separately with correct denominators. |
| S5-U07 | Unit | Energy/time per *correct* conclusion handles zero correct conclusions explicitly. |
| S5-U08 | Unit | Oracle decision regret uses identical utility definition and appropriate sign/interpretation. |
| S5-U09 | Unit | Binary Brier score and calibrated confidence bin calculations match analytic fixture. |
| S5-U10 | Unit | Median/p95 CPU latency computed correctly from provided measurements (no wall-clock-dependent test). |
| S5-U11 | Unit | Paired episode-level bootstrap confidence interval has fixed-seed reproducibility and correct percentile convention. |
| S5-U12 | Unit | Benchmark configuration rejects overlap among train/tune, development and held-out seed partitions. |
| S5-U13 | Unit | Benchmark policy execution can't inspect secret truth, oracle excluded from deployable comparison ranking. |
| S5-U14 | Unit | Ablation options disable intended component only, maintain comparable interfaces and version identifier. |
| S5-U15 | Unit | Real-data schema adapter validates units, missing metadata, timestamps, quality flags and provenance; rejects incompatible samples. |
| S5-U16 | Unit | Result export includes seed/config/code version, sample sizes, metric denominators, caveats and CI method. |
| S5-R01 | Regression | Frozen toy confusion-matrix metrics match golden values. |
| S5-R02 | Regression | Fixed-seed small benchmark summary reproducibly matches approved fixture within documented tolerances. |
| S5-R03 | Regression | CIs and paired differences from fixed synthetic episode table remain stable. |
| S5-R04 | Regression | Real adapter fixture round-trip retains metadata and clearly marks lack of ground-truth fault labels. |
| S5-R05 | Regression | Benchmark dashboard uses actual summary file data and no hardcoded performance claims. |
| S5-I01 | Integration | One command runs small headless benchmark and emits structured results and provenance. |
| S5-I02 | Integration | Paired policies run on matched scenario seeds, budgets and utility definitions. |
| S5-I03 | Integration | Full benchmark replay from saved config/seed returns same decisions/results. |
| S5-I04 | Integration | Ablations all execute against benchmark interface and produce interpretable rows. |
| S5-I05 | Integration | Dashboard replays representative success/failure missions with metrics and appropriately labeled truth. |
| S5-I06 | Integration | Real-data external validation reports supported checks only or a clear infeasibility/adapter-only status; never simulated labels as real. |

## Stage-end quality report template

```text
Stage: N
Required test IDs: [count] / implemented: [count] / missing: [IDs]
Unit: passed/failed/skipped
Regression: passed/failed/skipped
Integration/smoke: passed/failed/skipped
All previous stages regression: PASS/FAIL
Full pytest exact command/result:
Ruff exact command/result:
Coverage of new scientific core (if collected):
CLI/dashboard demo exact command/result:
Known skipped tests or CI limitations:
Git revision (if any):
Status: READY_FOR_REVIEW or BLOCKED
STOP — AWAITING USER APPROVAL.
```
