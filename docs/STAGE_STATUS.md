# Project AURORA — Stage gates and evidence

**Current authorized stage:** 5  
**Authorization:** User: `APPROVE STAGE 4; START STAGE 5`.  
**Overall status:** Stage 5 ACCEPTED by user; project stage sequence complete.

**Current research improvement authorization:** Step 2, per user's two-step
request. Original stages remain accepted. Step 1 is APPROVED; Step 2 is COMPLETE
and READY_FOR_REVIEW. Both requested steps are finished; no Step 3 is introduced.
User authorization: `I approve step 1, go for the next step`.
No additional approval stages exist.

| Stage | Name | Implementation status | Test status | User approval to START next stage |
| --- | --- | --- | --- | --- |
| 1 | Foundation & simulator | APPROVED | 21 PASS | GRANTED |
| 2 | Interactive dashboard | APPROVED | 36 PASS (full suite) | GRANTED |
| 3 | Joint inference & self-audit | APPROVED | 58 PASS (full suite) | GRANTED |
| 4 | Autonomous VOI planner | APPROVED | 82 PASS (full suite) | GRANTED |
| 5 | Evaluation & demo | ACCEPTED | 110 PASS (full suite) | FINAL ACCEPTANCE GRANTED |

> Only the user can approve a stage. A successful test suite or Codex-generated update is not an approval. On completion of Stage 1, set `READY_FOR_REVIEW`, report results and STOP. After an explicit user message such as `APPROVE STAGE 1; START STAGE 2`, record that exact approval and unlock Stage 2.

## Stage evidence record (append one section per completed stage)

### Stage 1 — Foundation and simulator
- **Authorization text from user:** "Start implementing Stage 1 ONLY from scratch."
- **Commit hash / revision:** None; supplied directory has no `.git` repository.
- **Summary of implementation:** Typed synthetic scenario, observation, resource and private-truth contracts; seeded simulator; six scenarios; JSON CLI; setup guide; lockfile; GitHub Actions workflow.
- **Demo command and observed behavior:** `python -m uv run --extra dev python -m aurora --scenario drift --seed 42 --truth` exited 0, emitted five agent observations with 2 Wh and 7 h remaining, followed by separately labeled private truth. `ordinary` seed 42 also exited 0.
- **Test IDs implemented:** S1-U01..S1-U12, S1-R01..S1-R04, S1-I01..S1-I03 (19/19 IDs); two additional unit validation tests.
- **Unit:** 14 passed, 0 failed, 0 skipped (full-suite result).
- **Regression:** `python -m pytest tests/regression -q`: 4 passed, 0 failed, 0 skipped.
- **Integration/smoke:** 3 passed, 0 failed, 0 skipped (full-suite result).
- **Full suite:** `python -m uv run --extra dev python -m pytest -q`: 21 passed, 0 failed, 0 skipped. Direct `python -m uv run pytest -q` could not spawn the pytest executable due to Windows Application Control (error 4551); the equivalent Python module invocation passed.
- **Ruff and CI:** `python -m uv run --extra dev python -m ruff check .`: all checks passed. GitHub Actions workflow configured for pushes and PRs; not executed because this directory is not a Git repository and has no CI remote.
- **Fixed seed/config and trace location:** `ordinary`, seed 42, `synthetic-1`; versioned regression values in `tests/regression/test_stage1.py`. CLI JSON can be redirected to a file.
- **Known scientific limitations and defects:** Illustrative dimensionless synthetic measurements; no calibrated planetary data, inference or detection. Public scenario names reveal preset identity to a human; future agent APIs must not use them as evidence. No calibration action yet. CI has not run. No commit was created.
- **Material deviations / ADR IDs:** None.
- **Final status:** READY_FOR_REVIEW
- **Explicit user approval to move forward:** `APPROVE STAGE 1; START STAGE 2`

## Approval sequence
1. Codex finishes active stage and all mandatory tests, updates evidence and stops.
2. User checks demo, test summary, research assumptions and changes.
3. User explicitly says `APPROVE STAGE N; START STAGE N+1` (or rejects/requests changes).
4. Codex records user's actual approval, updates authorized stage, then proceeds with **only** next stage.
5. Stage 5 ends with presentation for final user acceptance; no automatic public deployment.

### Stage 2 — Interactive dashboard
- **Authorization text from user:** `APPROVE STAGE 1; START STAGE 2`
- **Commit hash / revision:** None; supplied directory is not a Git repository.
- **Summary of implementation:** Streamlit/Plotly simulator dashboard with scenario, seed, budget, step and instrument controls; observation and resource plots; event log; agent JSON/CSV downloads; opt-in labeled evaluation truth; pure adapter service; 15 Stage 2 test IDs.
- **Demo command and observed behavior:** `python -m uv run --extra dev python -m streamlit run src/aurora/dashboard/app.py --server.headless true --server.port 8765` started locally. `GET /` returned HTTP 200 and `GET /_stcore/health` returned `ok`. Streamlit AppTest exercised run, scenario switch, deterministic rerun, reset and truth toggle.
- **Test IDs implemented:** S2-U01..S2-U09, S2-R01..S2-R03, S2-I01..S2-I03 (15/15); BUG-001 assertion in S2-I01 for complete app rendering. All 19 Stage 1 IDs remain.
- **Unit:** 9 passed, 0 failed, 0 skipped (Stage 2).
- **Regression:** `python -m uv run --extra dev python -m pytest tests/regression -q`: 7 passed, 0 failed, 0 skipped across Stages 1–2; 3 are Stage 2.
- **Integration/smoke:** 3 passed, 0 failed, 0 skipped (Stage 2); AppTest and local HTTP checks passed.
- **Full suite:** `python -m uv run --extra dev python -m pytest -q`: 36 passed, 0 failed, 0 skipped (21 Stage 1 + 15 Stage 2).
- **Ruff and CI:** `python -m uv run --extra dev python -m ruff check .`: all checks passed. `python -m uv sync --locked --extra dev`: checked 42 packages. CI workflow remains configured but unexecuted because no Git repository or remote exists. Direct `uv run pytest -q` remains blocked by host Windows Application Control; equivalent module invocation passed.
- **Fixed seed/config and trace location:** `ordinary`, seed 42, `synthetic-1`; Stage 2 plotting fixture in `tests/regression/test_stage2.py`. JSON downloads preserve agent-visible trace schema; CSV repeats public metadata per observation.
- **Known scientific limitations and defects:** Dashboard visualizes synthetic data only; no inference, diagnosis or autonomous decisions. Error bars represent configured noise SD, not confidence intervals. Public scenario name reveals the preset to a human. Empty-run CSV has a header only; JSON carries full metadata. This host's Application Control blocks some pandas DLLs, so event/truth displays use Streamlit JSON; Plotly charts and AppTest pass. CI has not run.
- **Material deviations / ADR IDs:** None.
- **Final status:** READY_FOR_REVIEW
- **Explicit user approval to move forward:** `Stage 2 approved, start next stage`

### Stage 3 — Joint inference and self-audit
- **Authorization text from user:** `Stage 2 approved, start next stage`
- **Commit hash / revision:** None; supplied directory is not a Git repository.
- **Summary of implementation:** Versioned binned Gaussian joint belief over three known geology classes, explicit broad unknown component and per-instrument healthy/bias/drift conditions; log-domain sequential updates; predictive adequacy caution; geology/fault/unknown dashboard panels and evidence trace.
- **Demo command and observed behavior:** `python -m uv run --extra dev python -m streamlit run src/aurora/dashboard/app.py` is the working host form; Stage 3 AppTest rendered the belief panel after a run with no exception. Fixed-seed ordinary, bias and outside trajectories were generated and checked in regression tests. The separate simulator truth toggle remains isolated.
- **Test IDs implemented:** S3-U01..S3-U13, S3-R01..S3-R04, S3-I01..S3-I04 (21/21 IDs), plus one additional invalid-input unit test. All 34 earlier required IDs remain implemented.
- **Unit:** 14 passed, 0 failed, 0 skipped (Stage 3).
- **Regression:** `python -m uv run --extra dev python -m pytest tests/regression -q`: 11 passed, 0 failed, 0 skipped across Stages 1–3; 4 are Stage 3.
- **Integration/smoke:** 4 passed, 0 failed, 0 skipped (Stage 3), including Streamlit AppTest belief rendering and agent-only trace replay.
- **Full suite:** `python -m uv run --extra dev python -m pytest -q`: 58 passed, 0 failed, 0 skipped (36 previous + 22 Stage 3).
- **Ruff and CI:** `python -m uv run --extra dev python -m ruff check .`: all checks passed. `python -m uv sync --locked --extra dev`: 42 packages checked. CI configured but unexecuted because no Git repository or remote exists. This host blocks the direct `uv run pytest` launcher; equivalent Python module invocation passed.
- **Fixed seed/config and trace location:** `ordinary`, `bias`, `outside`, seed 42, model `joint-binned-1`; regression values in `tests/regression/test_stage3.py`. No generated trace file was committed.
- **Known scientific limitations and defects:** Single-instrument geology/fault confounding; finite noisy two-instrument histories retain ambiguity. Unknown component is broad and uncalibrated; a low predictive bin warning is not proof of outside geology. Bias assumption +1.2 differs from conflict preset +1.5. No real-data calibration or measured false-alarm rate. No autonomous decision policy yet. Details in `docs/STAGE3_MODEL.md`.
- **Material deviations / ADR IDs:** None; explicit unknown component and binning implement the recommended small discrete model without simulator-truth access.
- **Final status:** READY_FOR_REVIEW
- **Explicit user approval to move forward:** `Approved, start next stage` (user response to Stage 3 handoff)

### Stage 4 — Resource-aware decisions and mission loop
- **Authorization text from user:** `Approved, start next stage` (Stage 3 approval and Stage 4 start)
- **Commit hash / revision:** None; supplied directory is not a Git repository.
- **Summary of implementation:** Feasible typed actions, terminal utility, exact binned one-step VOI, calibration and cross-check effects, bounded mission runner, fixed-model/information-gain/threshold baselines, dashboard autoplay and decision replay. No Stage 5 benchmark or real-data code.
- **Demo command and observed behavior:** `python -m uv run --extra dev python -m streamlit run src/aurora/dashboard/app.py`; Stage 4 AppTest rendered autonomous replay without exception. Fixed `drift`, seed 42 VOI smoke mission selected `calibrate_spectrometer`, `measure_spectrometer`, `conclude_clay`, ending at 6 Wh and 9 h. This is a synthetic fixture, not a performance claim.
- **Test IDs implemented:** S4-U01..S4-U15, S4-R01..S4-R04, S4-I01..S4-I04 (23/23 IDs), plus one invalid-state/policy unit test. All earlier required IDs remain.
- **Unit:** 16 passed, 0 failed, 0 skipped (Stage 4).
- **Regression:** `python -m uv run --extra dev python -m pytest tests/regression -q`: 15 passed, 0 failed, 0 skipped across Stages 1–4; 4 are Stage 4.
- **Integration/smoke:** 4 passed, 0 failed, 0 skipped (Stage 4), including AppTest replay and baseline mission runs.
- **Full suite:** `python -m uv run --extra dev python -m pytest -q`: 82 passed, 0 failed, 0 skipped (58 previous + 24 Stage 4).
- **Ruff and CI:** `python -m uv run --extra dev python -m ruff check .`: all checks passed. `python -m uv sync --locked --extra dev`: 42 packages checked. CI configured but unexecuted because no Git repository or remote exists. Direct uv launcher may remain blocked by host Application Control; Python-module invocation passed.
- **Fixed seed/config and trace location:** `drift`, seed 42, policy `voi-1`; action and VOI fixtures in `tests/regression/test_stage4.py`. No trace file was committed.
- **Known scientific limitations and defects:** Utility weights, calibration reset, priors and synthetic likelihoods are illustrative, not mission-calibrated. Calibration is a composite reset-plus-measure action. One-step VOI and baselines are not yet benchmarked; sensor/geology/unknown confounding remains. Mission runner returns private truth separately for future offline evaluation; planner and baselines receive visible state only. Details in `docs/STAGE4_DECISIONS.md`.
- **Material deviations / ADR IDs:** None.
- **Final status:** READY_FOR_REVIEW
- **Explicit user approval to move forward:** `APPROVE STAGE 4; START STAGE 5`

### Stage 5 — Evaluation and demo
- **Authorization text from user:** `APPROVE STAGE 4; START STAGE 5`
- **Approved scientific-method decisions:** User approved benchmark-only keyed observation noise for paired comparisons and a versioned correction to fixed-model fault scoring. `benchmark-1` JSON outputs are preserved as `results/benchmark_v1_superseded_*.json`; final claims use `benchmark-2` only.
- **Commit hash / revision:** No commit; supplied directory has no `.git` repository. Source SHA-256 `43f894937f199a2dbddd0f083792de4963818c0899d35ce62657c261eff6e6a5`.
- **Summary of implementation:** Frozen benchmark manifest and disjoint seed partitions; keyed paired runs for four policies; offline truth-only scoring, denominators, undefined-rate handling, calibration/Brier, paired bootstrap intervals, latency and ablations; JSON and CSV outputs; official PDS APXS provenance adapter and product; measured benchmark dashboard replay; README interview walkthrough and research report.
- **Demo command and observed behavior:** `python -m uv run --extra dev python -m streamlit run src/aurora/dashboard/app.py --server.headless true --server.port 8765` started locally; HTTP `/` returned 200, `/_stcore/health` returned `ok`. AppTest rendered measured benchmark, supported and incorrect mission examples, and optional labeled simulator truth.
- **Test IDs implemented:** S5-U01..S5-U16, S5-R01..S5-R05, S5-I01..S5-I06 (27/27 IDs) plus BUG-002 targeted regression (28 Stage 5 tests). All prior required IDs remain.
- **Unit:** 16 passed, 0 failed, 0 skipped (Stage 5).
- **Regression:** `python -m uv run --extra dev python -m pytest tests/regression -q`: 21 passed, 0 failed, 0 skipped across Stages 1–5; 6 are Stage 5 including BUG-002.
- **Integration/smoke:** 6 passed, 0 failed, 0 skipped (Stage 5), plus HTTP 200/health smoke.
- **Full suite:** `python -m uv run --extra dev python -m pytest -q`: 110 passed, 0 failed, 0 skipped (82 previous + 28 Stage 5).
- **Ruff and CI:** `python -m uv run --extra dev python -m ruff check .`: all checks passed. `python -m uv sync --locked --extra dev`: 42 packages checked. GitHub Actions workflow configured but unexecuted because no Git repository or remote exists. Direct `uv run pytest` launcher remains blocked by host Application Control; Python-module invocation passed.
- **Fixed seed/config and trace location:** `configs/benchmark_v2.json`, SHA-256 `740ec9df4cf5c9f364442f345dd810d59b1cea23a4c098ae5edd324cbde8bfce`; development seeds 100–109, held-out 1000–1009, bootstrap seed 2026; `results/benchmark_development.json/.csv` and `results/benchmark_heldout.json/.csv`. Each split: 240 paired-policy episode rows (60 per policy) plus four ablations of 60 episodes each. Keyed noise and source hashes are recorded in JSON.
- **Measured outcome:** Held-out VOI: 0 wrong claims / 50 claims, discovery recall 0.5, mean utility 7.020, mean oracle regret 1.313. Information gain: 4/50 wrong claims, mean utility 5.300; fixed model: 14/46, -0.657; threshold: 33/60, -7.160. Paired VOI minus information-gain mean utility +1.720, 95% episode bootstrap CI 0.213–3.697. Development information gain mean utility 7.300 exceeded VOI 7.063. Full denominators, other paired intervals, negative outcomes and caveats are in `docs/RESEARCH_RESULTS.md`.
- **Real-data status:** One official PDS APXS calibrated sol-46 CSV and PDS4 label downloaded 2026-11-14; 16 concentration rows pass provenance/schema checks. `qualitative_schema_only`; no real geology/fault labels or compatible synthetic-index likelihood. No real-world accuracy claim. Details and file hashes in `docs/REAL_DATA.md`.
- **Known scientific limitations and defects:** Small synthetic 10-seed-per-scenario held-out sample; arbitrary utility and priors; geology/fault identifiability limits; no fault-positive predictions for VOI at frozen threshold (fault F1 N/A, recall 0); outside-class F1 1.0 is generated-family-specific; whole-mission latency is not isolated planning time. No real-data model validation, no deployed system, and no executed CI. Generated results are local and ignored by Git. A larger preregistered study and a calibrated real-data observation model remain outstanding work, not claimed complete.
- **Material deviations / ADR IDs:** Approved keyed benchmark noise and approved `benchmark-2` scoring correction; no unapproved material deviation.
- **Final status:** READY_FOR_REVIEW
- **Final user acceptance:** User stated `I approve this stage` on 2026-11-14. No further stage is authorized or planned.

## Final research improvement — exactly two steps

### Step 1 — READY_FOR_REVIEW
- User authorized continuous diagnosis, corrections, harder development cases and tests, with no intermediate approval stages. Step 2 remains unstarted.
- Root causes: calibration erases pre-repair fault evidence; endpoint initial/active label mismatch; geology-only utility; coarse bins and restricted fault support; easy unknowns; legacy discovery denominator ceiling.
- Changes: added `research_model.py`, `research_mission.py`, `research_diagnostics.py`, audit dashboard, Step 1 config, 35 tests and source archive. Original core and benchmark-2 artifacts and BUG-002 are unchanged; preserved hashes verify true.
- Commands: `python -m uv run --extra dev python -m pytest -q` — 145 passed, 0 failed, 0 skipped; `python -m uv run --extra dev python -m pytest tests/regression -q` — 24 passed, 0 failed, 0 skipped; `python -m uv run --extra dev python -m ruff check .` — all checks passed; locked sync — 42 packages checked. New tests: 16 unit, 3 regression, 16 integration/parameterized cases. CI unexecuted; no Git repository or commit.
- Development-only diagnostic run: `python -m uv run --extra dev python -m aurora.research_diagnostics --output results/research_step1_diagnostics.json`; seeds 200–209, disjoint from all historical partitions. Source/config hashes and representative replays are in the artifact and `docs/RESEARCH_STEP1.md`.
- Matched six-preset initial fault recall 0/30 -> 21/30 (70%); F1 N/A -> 0.8077, FP 1/30. Correct conclusions 48/60 -> 50/60; utility 6.7333 -> 7.1567. This is not an isolated algorithm effect: reference information and cross-instrument verification differ from the original pipeline.
- Broader 14-case development run: unsupported-geology recall 46%, 27 wrong claims, initial fault recall 65.71%. Weak bias recall 0%; drift recall 20%; exact observational alias remains unidentifiable. These negative results and calibration/threshold diagnostics are documented.
- Reproduce audit UI: `python -m uv run --extra dev python -m streamlit run src/aurora/dashboard/research_app.py`.
- Limitations: finite synthetic model, reference transferability and perfect repair assumptions, quadrature approximation, no empirically calibrated threshold or real accuracy. Final matched comparisons, unseen scenarios, controlled ablations, final report and real-data review belong to Step 2.
- Explicit approval to start Step 2: `I approve step 1, go for the next step`.

### Step 2 — COMPLETE / READY_FOR_REVIEW
- Authorization: `I approve step 1, go for the next step`. Exactly two research-improvement steps were used; no additional approval stage was introduced.
- Frozen final protocol: `configs/research_final_v2.json`, version `research-final-2`; 20 scenario families, 50 independent seeds per family, five matched policies. Development excludes all six `unseen_*` families. Development, final and robustness partitions are disjoint from historical experiments.
- Matched policies share action contracts, budgets, acquisition horizon, pre-reset reference readings, perfect repair, paired per-case noise and two-instrument verification. Original binned VOI is explicitly labeled an adapter under those contracts. Untouched original VOI runs separately as a historical bridge, not a matched comparator. Benchmark-2 and BUG-002 hashes are unchanged.
- Sampling correction: the superseded `research-final-1` reused noise across cases while intervals assumed independent cases. Before inspecting its final aggregate scores, the run was stopped, preserved and superseded. V2 adds a stable case-name stream key and uses fresh untouched seeds: development 9000–9019; final 10000–10049; robustness 12000–12009. Policies, priors, thresholds and primary utilities were not retuned. Source/config snapshots and `research_final_v1_SUPERSEDED.md` disclose the correction.
- Completed experiments: 1,400 development + 5,000 final + 1,400 controlled ablation + 960 sensitivity + 300 untouched-original bridge = 9,060 missions in the corrected version. Main final set is 1,000 episodes per policy. Each complete suite has JSON/CSV outputs and a protected JSONL checkpoint under `results/research_*_v2.*`; no historical result was overwritten.
- Primary improved VOI: 594/1000 correct supported conclusions (59.4%), 180 wrong claims / 774 claims (23.26%, Wilson 95% CI 20.42–26.36%), 226 abstentions, mean utility 1.08845 (95% stratified bootstrap CI 0.84602–1.34186). Matched original VOI: 596/1000 correct, 291/887 wrong claims, utility -1.33590. Improved minus original paired utility +2.42435, 95% CI 2.10500–2.74472. Improved accuracy regressed by 0.20 percentage points; no accuracy-improvement claim is made.
- Initial fault diagnosis: precision 337/367 = 91.83%, recall 337/500 = 67.4%, F1 0.77739 (bootstrap 95% CI 0.75489–0.80092). The point target F1 >=0.8 is not met. Initial and active scoring remain separate; active instrument-time records are clustered by episode.
- Unsupported geology: precision 216/221 = 97.74%, recall 216/400 = 54.0%, F1 0.69565 (95% CI 0.66886–0.72240). Exact aliases and overlapping cases still fail. Supported sulfate recall is separately 100/100; legacy discovery metrics remain unchanged in benchmark-2.
- Resource/latency: all 5,000 matched final missions stayed within budgets. Improved mean energy/time use 5.726 Wh/3.926 h; actual selection-call median 0.04029 s, p95 0.05204 s on the recorded CPU, including terminal selection calls. These are host-dependent synthetic measurements.
- Negative controlled results: verification removal had utility 0.92675 versus nominal 0.78325 on 200 paired ablation episodes; this does not establish a utility benefit for the mandatory gate. High-noise unknown recall was 0% in the sensitivity suite. All ablations, prior/noise/severity/reward/quadrature sensitivity and unseen-family results appear in `docs/FINAL_RESEARCH_REPORT.md`.
- Real-data feasibility: existing official APXS analyte concentrations, statistical precision, label units, timestamps and hashes are preserved per row. No normalizing or synthetic-index mapping was applied. No independent fault/geology truth or calibrated physical likelihood is available; status `feasibility_only`, with no claimed real-world accuracy.
- Tests: `python -m uv run --extra dev python -m pytest -q` — 182 passed, 0 failed, 0 skipped; `python -m uv run --extra dev python -m pytest tests/regression -q` — 28 passed, 0 failed, 0 skipped. Step 2 added 37 checks (16 unit, 4 regression, 17 integration/parameterized), including BUG-004 sampling regression. All historical and Step 1 tests pass. Ruff passed; locked sync checked 42 packages. Fifteen saved held-out outcomes replayed across all five policies; actual final-result AppTest and truth toggle passed. Local server `/` returned HTTP 200 and health returned `ok`.
- Reproduce: `python -m uv run --extra dev python -m aurora.final_benchmark --suite final --output results/replay_final.json`. Other suite commands, report regeneration and final viewer launch are in README and the final report. Completed outputs refuse overwrite; resume requires identical source/config hashes.
- Source SHA-256: `2bdfe7cc4169037002fc5e64c04722cb1c4565d5ed503c1727e51b1f72269473`; config SHA-256: `90850fe3777d8f160cfef8afb5a9cc6eba5417d5c3095067cc71da86b4e7638d`. Verified source snapshot: `research_archive/research_final_v2_source.zip`. Original and Step 1 source archives are preserved. Per-artifact integrity hashes are in `results/research_final_integrity_v2.json`.
- Changed/added: final policy adapter, common mission runner, statistics, benchmark CLI, real-data feasibility module, final dashboard, tests, versioned manifests, report generator, protocol/report, README, status and source archives. No Git repository exists, no commit was created, and remote CI was not executed; the existing workflow remains configured.
- Remaining limits: synthetic reference transfer/perfect reset, finite fault support, quadrature and omitted calibration-reference value, prior sensitivity, weak-fault/unknown identifiability, imperfect high-noise behavior, fixed-family confidence intervals and unadjusted multiple comparisons. All negative outcomes are retained. No new final-set tuning, deployment or real-world accuracy claim.
- Final status: COMPLETE / READY_FOR_REVIEW. No further implementation step is automatically authorized.
