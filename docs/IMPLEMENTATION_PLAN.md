# IMPLEMENTATION PLAN — ALL FIVE STAGES IN ONE FILE

> **Codex instruction:** Implement **ONE STAGE ONLY** per explicit authorization. Initially Stage 1 only. After completing any stage, run all required tests, record evidence in `docs/STAGE_STATUS.md`, and **STOP — AWAIT USER APPROVAL**. Never interpret this file's inclusion of later stages as approval to start them. All suggested algorithms/tools may be changed only after user approval of a material alternative, per `AGENTS.md`.

## Global constraints (all stages)
- Start from scratch; Python 3.11+, `uv`, local CPU, Streamlit dashboard, hybrid dataset strategy, no paid services. Minimize dependencies and rework.
- Core domain API separate from UI. Explicit unit/likelihood/seed provenance. No hidden simulator state in agent prediction/planning.
- Implement all current-stage test IDs in `TEST_PLAN.md`; fixed bugs need regression tests. Do not skip tests silently or reduce assertions. All prior tests must still pass.
- Run `uv run pytest -q` and `uv run ruff check .` for each stage; CI checks on push/PR once Stage 1 completes. Execute the demo before requesting approval.
- Mark `READY_FOR_REVIEW`, not approved. Report completed features, commands, test counts, benchmark caveats, diff summary, commit (if created), limitations and approval request. **STOP.**

## STAGE 1 — Foundation, reproducible planetary simulator & tests
**Authorization:** automatically authorized as first stage ONLY.  
**Model/effort:** cheapest appropriate Codex coding model / Low effort; escalate for scientific observation-model design only.

**Outcome:** working command-line simulator and stable typed contracts; no UI or inference yet.

**Implement**
1. Set up editable `src/aurora` Python package, `pyproject.toml`, committed `uv.lock`, Ruff, pytest, GitHub Actions and Windows PowerShell setup guide. Don't create empty modules for future stages.
2. Typed/scientifically documented models: scenario, geology, instrument condition, observation, action, resources, terminal state, agent-visible trace, private evaluation truth. Explicit units and validation.
3. Three distinguishable yet overlapping geological classes; at least two instruments with different observation patterns; conditions healthy, fixed bias and time-dependent drift. Explicitly state simplifications.
4. Seeded observations using passed NumPy RNG, reproducible deterministic config and independent/private simulation truth. A mission step must never spend negative budget.
5. Configurable cases: ordinary, genuine unusual, biased instrument, drifting instrument, conflicting instruments and truth outside hypothesis family; finite horizon and exhausted budget.
6. CLI: `uv run python -m aurora --scenario <name> --seed 42` (or a clearly documented equivalent), emit concise agent observations plus optional clearly labeled evaluation truth and exportable JSON trace.
7. Documentation: observations, priors (if not used yet, only define expected future interface), noise distributions, units, state transitions, seed/version metadata, commands.

**Mandatory tests:** S1-U01..S1-U12, S1-R01..S1-R04, S1-I01..S1-I03 in `TEST_PLAN.md`. Full suite, lint and CI configuration. Ensure randomized scenarios exercise fixed-seed invariant behavior without all outputs becoming constants.

**Demo:** run same seed twice -> identical agent-visible trace; alter seed -> normally differing stochastic trace; compare healthy vs faulty sensor and budget consumption. Show omitted-hypothesis episode only as generated truth, not a “detected” unknown.

**Acceptance:** install from lockfile; CLI works on CPU; test inventory green; stable fixture snapshots and no truth leakage; no Stage 2+ components. Update `STAGE_STATUS.md`; git commit if permitted. **STOP — REQUEST APPROVAL FOR STAGE 2.**

## STAGE 2 — Working Streamlit scientific dashboard & tests
**Prerequisite:** explicit user `APPROVE STAGE 1; START STAGE 2`.  
**Model/effort:** cheap Codex model / Low effort.

**Outcome:** impressive but truthful early demo of the simulation with clean UX.

**Implement**
1. Thin Streamlit/Plotly layer using Stage 1 service/trace contracts. No posterior formulas or planner decisions inside UI.
2. Controls: scenario, seed, energy/time constraints, number of steps, run/reset, and compatible instrument settings. Validate invalid/edge inputs.
3. Visualize observation timelines with instrument IDs, uncertainties as documented; energy/time over steps; event log and scenario context. Use sensible labels and units, accessible plot titles.
4. Agent-view default. Evaluation ground truth hidden unless explicitly toggled and clearly labeled **SIMULATOR TRUTH—NOT AVAILABLE TO AGENT**.
5. Provide CSV/JSON download with config, seed, trace schema version and provenance. Stable reruns must not mix Streamlit session state.
6. Document exact UI launch command and a 2-minute local demonstration script.

**Mandatory tests:** S2-U01..S2-U09, S2-R01..S2-R03, S2-I01..S2-I03 plus all Stage 1 tests; Streamlit AppTest smoke where feasible.

**Demo:** launch localhost dashboard; run a healthy and drifting sensor scenario; graphs change with scenario and remain reproducible with seed; export and reload trace. Clearly label this as simulator visualization, **not autonomous intelligence yet**.

**Acceptance:** UI starts with no paid services or GPU, validated inputs, correct chart data, no truth on agent view/export, all tests pass. Update stage evidence and commit if permitted. **STOP — REQUEST APPROVAL FOR STAGE 3.**

## STAGE 3 — Joint Bayesian scientific self-auditing & tests
**Prerequisite:** explicit user `APPROVE STAGE 2; START STAGE 3`.  
**Model/effort:** strongest available Codex reasoning model / High for initial scientific formulation, Medium for code/tests.

**Outcome:** calibrated or appropriately qualified inference explaining scientific evidence vs unreliable instruments or inadequate model assumptions.

**First — model review checkpoint:** Examine whether geology, fault modes, and unknown hypotheses are *identifiable* from available observations. If impossible to support scientifically, propose the smallest observation/experiment change and **pause for user approval before implementing that material change**.

**Implement**
1. Transparent discrete priors and normalized likelihoods; sequential joint belief over geology and sensor condition (and explicit unknown/adequacy mechanism), using numerically stable inference.
2. Separate predictions, observed evidence, posterior probabilities and calibration diagnostics. No silent renormalization of known states to “detect” an unknown.
3. Posterior predictive or out-of-family adequacy diagnostic with documented false-positive limitations; explicit uncertainty and abstention-ready outputs.
4. Instrument reliability warnings distinguishing sensor drift/bias from unusual geology **where data supports it**. Show ambiguity otherwise; never claim impossible certainty.
5. Explainable evidence trace and dashboard panels for posterior, fault likelihood and adequacy flag; simulator truth only in a separate optional view.
6. Version prior/likelihood assumptions; no oracle/data leakage to belief updates.

**Mandatory tests:** S3-U01..S3-U13, S3-R01..S3-R04, S3-I01..S3-I04, all earlier tests; analytical hand-checked toy Bayesian example, likelihood normalization, posterior normalization, zero/near-zero likelihood, history order and hidden-truth invariance.

**Demo:** compare genuine novel geology against biased sensor and conflicting measurements. Show posterior movements with new evidence; missing-hypothesis scenario should trigger supported caution/adequacy diagnostic, **not perfect detection**.

**Acceptance:** numerically and scientifically sound small worked cases, no truth leakage, honest uncertainty limitations, reproducible posterior trajectories, dashboard plots; full suite green. Update evidence. **STOP — REQUEST APPROVAL FOR STAGE 4.**

## STAGE 4 — Autonomous resource-aware decision planning & tests
**Prerequisite:** explicit user `APPROVE STAGE 3; START STAGE 4`.  
**Model/effort:** strongest available Codex reasoning model / High for utility/VOI semantics, Medium for implementation.

**Outcome:** live mission decision loop that explains *why* it gathers evidence, cross-checks, calibrates, concludes, abstains or escalates.

**Implement**
1. Legal actions with prerequisites and coherent observation effects: measure, independent cross-check, calibrate, discriminating test, conclude, abstain, and communication-aware escalation.
2. Transparent terminal utility and action cost model (energy/time/risk/communication; cost only counted once); state stopping rule before optimizing.
3. One-step VOI over possible future observations relative to best terminal decision. Use exact enumeration for small model; document approximation if approved.
4. Respect remaining budget, finite horizon, unavailable instrument states, zero budget, unknown hypothesis, and unavailable communications. Deterministic tie breaking, step bound and stop reason.
5. Implement baseline policies behind same action/observation interface: fixed-model, information gain, threshold verification; isolate oracle's privileged access for offline comparison only.
6. Dashboard autoplay/step, competing action values, selected action and justification, mission resources, belief trajectories and terminal decisions.

**Mandatory tests:** S4-U01..S4-U15, S4-R01..S4-R04, S4-I01..S4-I04 and all prior tests; analytically computed VOI examples, impossible actions, no budget overspend, no reward double count, stopping, no oracle leakage and full replay.

**Demo:** choose a drifting-sensor scenario. System decides between another observation and calibration/cross-check based on utility and budget, explains action, updates beliefs, and eventually safely concludes/abstains.

**Acceptance:** policy comparisons run under consistent contracts; planner behaves on hand-check examples; mission terminates; full tests green. Document limitations. **STOP — REQUEST APPROVAL FOR STAGE 5.**

## STAGE 5 — Honest experiments, hybrid official dataset, research-ready product & tests
**Prerequisite:** explicit user `APPROVE STAGE 4; START STAGE 5`.  
**Model/effort:** inexpensive Codex coding model / Medium; High reasoning only for experiment/statistical review.

**Outcome:** reproducible report, research benchmark, ablation study, accessible CPU dashboard and interview demo.

**Implement**
1. Freeze metric definitions, policies, scenario distribution, tuning/dev seeds and held-out evaluation seeds **before** scoring. Record immutable config hashes, code revision, RNG construction and CPU details.
2. Fair paired-episode comparison of AURORA, fixed-model, info-gain, threshold-verification; privileged oracle as *upper reference*, not a fair deployable baseline. Consistent budgets, rewards and feasible action space.
3. Outcomes: false scientific claim rate, discovery recall, false negatives, abstention, correct terminal decision, calibration/Brier, sensor/model detection precision/recall/F1, mission success, energy/time per supported conclusion, oracle-regret, latency median/p95 and robustness by noise/drift/unknown scenarios.
4. Report denominators and `N/A` for undefined rates (zero positive predictions, etc.), 95% paired episode-level bootstrap CIs (and seeds), uncertainty and caveats. Avoid pretending hundreds of correlated steps are independent samples.
5. Ablations: remove reliability modeling, remove inadequacy diagnostic, replace VOI with information gain, remove resource penalties. If an ablation changes action feasibility/utility, make its interpretation explicit.
6. Real planetary dataset **feasibility gate**: confirm an official, accessible, documented PDS-like dataset with sensor semantics/provenance and permissible use. Implement minimal adapter and clearly distinguish qualitative external sanity checks from simulated ground-truth metrics. If unavailable or incompatible: record failed feasibility, implement a tested adapter contract and **do not claim external validation**. No fabricated real-data labels.
7. Produce reproducible benchmark command, compact CSV/JSON metrics, confidence interval tables, representative successful and failed mission replay, dashboard comparison charts, limitations and README 5-minute MS interview script.
8. Run final tests, regression suite, lint, replay and benchmark smoke. Do not publicly deploy or post results without user approval.

**Mandatory tests:** S5-U01..S5-U16, S5-R01..S5-R05, S5-I01..S5-I06 plus prior stages; evaluate metric edge cases, paired seed design, no test-set tuning, bootstrap reproducibility, adapter provenance, honest N/A, fairness, benchmark replay and dashboard smoke.

**Suggested run plan:** begin with 100 paired development episodes per scenario; attempt ~500 paired final episodes/scenario if CPU budget permits, selecting final sample size from compute and CI precision. Do not fake results or hardcode proposed targets. Candidate *research targets* (not achieved): >=20% relative reduction in false conclusions at comparable discovery recall, >=15% regret reduction, model-error F1 >=0.80, median decision latency <=1 s on specified CPU.

**Acceptance:** any claim traceable to saved result and config/seed; results include failures and limitations; real-data status truthful; interview-ready local dashboard; full suite green. Update report and status. **STOP — REQUEST FINAL USER ACCEPTANCE.**

## Global approval template — copy into each Codex stage closeout

```text
STAGE <N>: READY_FOR_REVIEW or BLOCKED
Implemented:
Demo command and observed result:
Unit / regression / integration test IDs and counts:
Full pytest command/outcome:
Ruff command/outcome:
Git commit/revision (if created):
Scientific limitations and pending ADR decisions:
Next stage: BLOCKED.
STOP — AWAITING USER APPROVAL FOR NEXT STAGE.
```

Only the user may respond `APPROVE STAGE <N>; START STAGE <N+1>`. If not approved, fix this stage only.
