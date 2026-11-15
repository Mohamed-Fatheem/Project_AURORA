# AURORA — final research report (Step 2)

Version `research-final-2`. All results below are measured synthetic evidence. Official APXS data supports a feasibility demonstration only.

## 1. Problem and objectives

Distinguish supported geological evidence, instrument faults and unsupported geology while choosing feasible experiments. Correct the original initial/active fault timing error, test difficult unknowns and evaluate transparent tradeoffs without inventing performance improvements.

## 2. Architecture and algorithms

The original simulator/inference/planner remain intact. A separate continuous 196-state audit model integrates persistent unknown sensor means, uncertain signed bias/drift hypotheses, pre-reset reference evidence and repair masks. The matched runner shares budgets, action costs, keyed science/reference noise, reference access and two-instrument verification across all five policies. The adapted original VOI retains its seven-bin 36-state model. Exact binned enumeration and 7-node continuous quadrature score one-step terminal utility. Calibration scoring conservatively omits the reference-information bonus. Information gain ranks discrete latent-state entropy reduction; it does not integrate continuous unknown-mean entropy.

## 3. Original weaknesses and corrections

Calibration formerly erased fault beliefs before observation and endpoint scoring compared repaired state with initial truth. Initial identities now survive repair; active faults are scored before repair and after actions against contemporaneous truth. Reference readings decouple offset evidence from geology under the synthetic reference-transfer assumption. Signed fault support and continuous likelihoods retain more evidence. Supported sulfate recall is separated from unsupported-geology detection; the legacy metric and BUG-002 remain preserved.

## 4. Experimental methodology

Frozen manifest: `configs/research_final_v2.json`. Development: 14 families × 20 separate seeds × 5 policies = 1,400 rows. Final: 20 families × 50 seeds × 5 policies = 5,000 rows (1,000 per policy), including six families excluded from development. Ablations: 1,400 rows; sensitivity: 960 rows; untouched historical bridge: 300 rows. Total: 9,060 missions in the corrected version. An earlier v1 run reused noise across scenario families; it was preserved as superseded before final aggregate scores were inspected. V2 adds a case-name stream key and uses fresh untouched seed partitions, without changing policy parameters. No final-set tuning or threshold search was performed.

Primary utility stays +10 correct, −20 incorrect, 0 abstain, minus 0.15/Wh and 0.10/hour. All primary policies share 12 Wh, 12 h and five acquisition actions. Fault/unknown thresholds stay 0.5. Reward changes occur only in labeled sensitivity arms. Wilson 95% intervals describe episode proportions; case-stratified paired episode bootstrap uses 1,000 resamples, seed 42026, for means/F1/differences. Active-fault uncertainty resamples whole episode clusters. Multiple comparisons are exploratory and unadjusted. Latencies measure actual selection calls, including terminal calls.

## 5. Comparative results with uncertainty

The broader distribution includes 600 supported and 400 unsupported episodes per policy. Safe abstention is not counted as a correct supported conclusion, so the maximum conclusion-accuracy value is 60% on this mixture. This is the original correct-conclusions/all-episodes definition, not a standard four-class accuracy counting unknown abstentions as correct labels. Raw accuracy is therefore not directly comparable with the six-preset Stage 5 accuracy. Improved VOI correctly concluded 594/600 supported cases while still making 180 incorrect claims across all 1,000 episodes; a known-only percentage would hide those unsupported-case errors.

| Matched policy | Conclusion accuracy | Wrong / claims | False-conclusion proportion (95% CI) | Mean utility (95% CI) | Mean regret |
| --- | --- | --- | --- | --- | --- |
| fixed_model | 40.7% (407/1000) | 311/718 | 0.433 [0.397, 0.470] | -3.143 [-3.464, -2.816] | 9.143 |
| improved_voi | 59.4% (594/1000) | 180/774 | 0.233 [0.204, 0.264] | 1.088 [0.846, 1.342] | 4.912 |
| information_gain | 54.2% (542/1000) | 379/921 | 0.412 [0.380, 0.444] | -3.089 [-3.440, -2.755] | 9.089 |
| original_voi | 59.6% (596/1000) | 291/887 | 0.328 [0.298, 0.360] | -1.336 [-1.541, -1.091] | 7.336 |
| threshold | 49.4% (494/1000) | 395/889 | 0.444 [0.412, 0.477] | -4.044 [-4.417, -3.664] | 10.044 |

Explicit regression/tradeoff: improved VOI made 594 correct conclusions versus 596 for matched original VOI. Its accuracy difference is -0.20 percentage points. Improved VOI abstained in 226 episodes versus 113; higher utility and fewer false claims do not imply higher conclusion accuracy. It still made 180 wrong claims.

| Policy | Initial fault P / R / F1 | Unknown P / R / F1 | Coverage | Supported sulfate recall |
| --- | --- | --- | --- | --- |
| fixed_model | N/A / 0.000 / N/A | 0.545 / 0.378 / 0.446 | 71.8% (718/1000) | 92.0% (92/100) |
| improved_voi | 0.918 / 0.674 / 0.777 | 0.977 / 0.540 / 0.696 | 77.4% (774/1000) | 100.0% (100/100) |
| information_gain | 0.733 / 0.422 / 0.536 | 0.823 / 0.163 / 0.271 | 92.1% (921/1000) | 100.0% (100/100) |
| original_voi | 0.856 / 0.440 / 0.581 | 0.961 / 0.245 / 0.390 | 88.7% (887/1000) | 100.0% (100/100) |
| threshold | 0.755 / 0.406 / 0.528 | 0.791 / 0.133 / 0.227 | 88.9% (889/1000) | 99.0% (99/100) |

Improved initial-fault F1 is 0.777, 95% bootstrap CI [0.755, 0.801]; a point target of 0.8 is not met. Unknown F1 is 0.696 [0.669, 0.722] on the harder distribution, replacing the earlier easy-case impression of perfect detection.

Full confusion counts, Wilson intervals for precision/recall, bootstrap F1 intervals, Brier scores and active instrument-time counts are in the JSON; active readings are not independent episode observations.

| Policy | Energy / time used, mean | Selection median / p95 | Within budget |
| --- | --- | --- | --- |
| fixed_model | 4.458 Wh / 3.241 h | 0.0019 / 0.0024 s | 100.0% (1000/1000) |
| improved_voi | 5.726 Wh / 3.926 h | 0.0403 / 0.0520 s | 100.0% (1000/1000) |
| information_gain | 4.067 Wh / 3.186 h | 0.0018 / 0.0024 s | 100.0% (1000/1000) |
| original_voi | 6.879 Wh / 4.441 h | 0.0018 / 0.0025 s | 100.0% (1000/1000) |
| threshold | 4.920 Wh / 3.460 h | 0.0019 / 0.0026 s | 100.0% (1000/1000) |

Paired utility differences are improved VOI minus comparator:

| Comparator | Mean difference | 95% paired CI |
| --- | --- | --- |
| fixed_model | 4.231 | [3.851, 4.623] |
| information_gain | 4.177 | [3.808, 4.573] |
| original_voi | 2.424 | [2.105, 2.745] |
| threshold | 5.132 | [4.699, 5.589] |

Original Stage 5, preserved and not a matched comparison:

| Original policy | Wrong / claims | Mean utility |
| --- | --- | --- |
| fixed_model | 14/46 | -0.657 |
| information_gain | 4/50 | 5.300 |
| threshold | 33/60 | -7.160 |
| voi | 0/50 | 7.020 |

Untouched original VOI bridge on 300 new episodes from the original six presets: 250/300 correct conclusions, 0 wrong claims, mean utility 7.107. Its original action/information/scoring contract differs from the matched runner. Thus neither this bridge nor benchmark-2 is evidence of an isolated policy improvement.

Matched six-preset subset under the new shared contract:

| Policy | Correct / episodes | Wrong claims | Mean utility |
| --- | --- | --- | --- |
| improved_voi | 248/300 | 0 | 7.175 |
| original_voi | 249/300 | 0 | 7.048 |
| information_gain | 209/300 | 41 | 3.270 |
| fixed_model | 128/300 | 65 | -1.046 |
| threshold | 170/300 | 62 | 0.355 |

## 6. Ablations, robustness and unseen scenarios

Each ablation changes only its named component while keeping exogenous worlds, costs and scoring fixed. No-reference masks inference updates while preserving generated readings. Gate removal changes policy admissibility; no-cost changes ranking, not physical resource constraints.

| Ablation | Mean utility | Accuracy | Fault recall | Unknown recall | Nominal minus arm utility (95% CI) |
| --- | --- | --- | --- | --- | --- |
| information_gain | -1.200 | 56.0% (112/200) | 0.580 | 0.325 | 1.983 [1.244, 2.819] |
| no_cost | 0.678 | 60.0% (120/200) | 0.690 | 0.562 | 0.106 [-0.301, 0.517] |
| no_fault | -0.872 | 37.0% (74/200) | 0.000 | 0.562 | 1.655 [1.100, 2.229] |
| no_reference | 0.035 | 60.0% (120/200) | 0.260 | 0.325 | 0.748 [0.343, 1.247] |
| no_unknown | -2.348 | 11.0% (22/200) | 0.720 | 0.000 | 3.131 [2.329, 4.051] |
| no_verification | 0.927 | 60.0% (120/200) | 0.630 | 0.500 | -0.144 [-0.167, -0.117] |
| none | 0.783 | 60.0% (120/200) | 0.640 | 0.500 | reference |

Component limitation: the verification-removal arm has mean utility 0.927 versus nominal 0.783. This experiment does not establish that mandatory cross-instrument verification improves utility. The table reports that result even though verification was introduced as a safety criterion in Step 1.

Sensitivity arms (separate seeds, six development families, 60 episodes per arm):

| Variant | Mean utility | Accuracy | Fault recall | Unknown recall |
| --- | --- | --- | --- | --- |
| bias_strong | -2.933 | 50.0% (30/60) | 0.800 | 0.333 |
| bias_weak | -2.933 | 50.0% (30/60) | 0.367 | 0.333 |
| drift_fast | -2.933 | 50.0% (30/60) | 0.933 | 0.333 |
| drift_slow | -2.933 | 50.0% (30/60) | 0.700 | 0.333 |
| healthy_prior_high | -1.623 | 50.0% (30/60) | 0.633 | 0.467 |
| healthy_prior_low | -2.940 | 50.0% (30/60) | 0.933 | 0.300 |
| noise_high | -5.968 | 50.0% (30/60) | 0.467 | 0.000 |
| noise_low | 2.802 | 50.0% (30/60) | 0.967 | 0.900 |
| noise_overestimated | -4.873 | 50.0% (30/60) | 0.367 | 0.000 |
| noise_underestimated | -2.876 | 45.0% (27/60) | 0.800 | 0.400 |
| nominal | -2.933 | 50.0% (30/60) | 0.800 | 0.333 |
| quadrature_15 | -2.933 | 50.0% (30/60) | 0.800 | 0.333 |
| unknown_prior_high | -0.145 | 48.3% (29/60) | 0.800 | 0.633 |
| unknown_prior_low | -3.714 | 50.0% (30/60) | 0.800 | 0.267 |
| wrong_penalty_high | -5.668 | 50.0% (30/60) | 0.800 | 0.500 |
| wrong_penalty_low | 0.440 | 50.0% (30/60) | 0.800 | 0.333 |

Noise failure: the high-noise arm has unknown recall 0.000, versus nominal 0.333. The model is not robust to these noisy overlapping unknowns. The 15-node arm has mean utility -2.933, compared with 7-node nominal -2.933; this limited resolution check is not a proof of general quadrature convergence.

These sensitivity scores retain their own declared reward setting. Scores from changed rewards are not ranked as primary-policy improvements. Parameters were not retuned after viewing them.

Generalization to six held-out scenario families (300 episodes per policy):

| Policy | Accuracy | Unknown recall | Fault recall | Utility |
| --- | --- | --- | --- | --- |
| improved_voi | 49.3% (148/300) | 0.660 | 0.487 | 0.304 |
| original_voi | 50.0% (150/300) | 0.293 | 0.247 | -3.501 |
| information_gain | 49.7% (149/300) | 0.027 | 0.127 | -5.768 |
| fixed_model | 47.3% (142/300) | 0.340 | 0.000 | -2.772 |
| threshold | 49.0% (147/300) | 0.020 | 0.073 | -5.640 |

Development means (reported, not used for final tuning): fixed_model: -3.579; improved_voi: 1.314; information_gain: -2.042; original_voi: -0.440; threshold: -3.629.

Improved VOI failures by final case:

| Case | Correct / episodes | Wrong claims | Unknown recall | Fault recall |
| --- | --- | --- | --- | --- |
| bias | 50/50 | 0 | N/A | 0.960 |
| both_faults | 49/50 | 0 | N/A | 1.000 |
| conflict | 50/50 | 0 | N/A | 1.000 |
| drift | 50/50 | 0 | N/A | 0.500 |
| high_noise | 49/50 | 0 | N/A | N/A |
| negative_bias | 50/50 | 0 | N/A | 0.680 |
| ordinary | 48/50 | 0 | N/A | N/A |
| outside | 0/50 | 0 | 1.000 | N/A |
| unknown_alias | 0/50 | 49 | 0.020 | N/A |
| unknown_boundary | 0/50 | 15 | 0.660 | N/A |
| unknown_fault | 0/50 | 31 | 0.380 | 1.000 |
| unknown_overlap | 0/50 | 35 | 0.280 | N/A |
| unseen_imager_fault | 49/50 | 0 | N/A | 0.560 |
| unseen_noisy_clay | 49/50 | 0 | N/A | N/A |
| unseen_sulfate_drift | 50/50 | 0 | N/A | 0.140 |
| unseen_unknown_mixed | 0/50 | 3 | 0.940 | N/A |
| unseen_unknown_near_clay | 0/50 | 46 | 0.060 | N/A |
| unseen_unknown_negative_fault | 0/50 | 1 | 0.980 | 0.760 |
| unusual | 50/50 | 0 | N/A | N/A |
| weak_bias | 50/50 | 0 | N/A | 0.140 |

## 7. Real-data feasibility

The existing official [PDS APXS product](https://pds-geosciences.wustl.edu/missions/msl/apxs.htm) contributes 16 analyte concentration/precision pairs, kept in their PDS4 label's weight-percent units with original timestamps and hashes. No normalization or mapping into synthetic indices is applied. The [official APXS tutorial](https://pds-geosciences.wustl.edu/workshops/DPS_2020_Presentations/2020-1027-DPS-APXS-Tutorial.pdf) distinguishes reported precision from accuracy and warns that exports may use different units for trace elements. This loader follows the specific product label rather than mixing export formats. Covariance, systematic accuracy and ground-truth failure/geology labels remain unavailable in this product. Consequently no defensible real-world classification, fault F1 or autonomy utility is computed. Status: feasibility_only.

## 8. Remaining limitations and negative results

Exact observational aliases cannot be identified from these sensors. Overlapping unknowns, weak drift and faults outside the finite hypothesis support can still yield confident incorrect claims. Reference transferability and perfect reset are synthetic assumptions. The unknown prior has independent instrument means; quadrature and omitted calibration-reference value are approximations. Verification costs resources and can force abstention. Fault diagnosis still has no direct utility reward. An apparent synthetic improvement does not establish real-spacecraft validity. Case-balanced confidence intervals do not cover all possible geology; multiple-comparison effects are unadjusted. No test target is declared passed solely from a favorable point estimate.

## 9. Future work

Acquire independent reference/repair and geology labels; construct physically calibrated multi-instrument likelihoods; model imperfect repair and correlated measurement uncertainty; study longer-horizon experiment value and utility elicitation; evaluate additional unseen distributions with a new preregistration. Do not tune on this final set.

## 10. Reproduction and integrity

```powershell
python -m uv sync --locked --extra dev
python -m uv run --extra dev python -m pytest -q
python -m uv run --extra dev python -m ruff check .
python -m uv run --extra dev python -m aurora.final_benchmark --suite development --output results/replay_development.json
python -m uv run --extra dev python -m aurora.final_benchmark --suite final --output results/replay_final.json
python -m uv run --extra dev python -m aurora.final_benchmark --suite ablations --output results/replay_ablations.json
python -m uv run --extra dev python -m aurora.final_benchmark --suite robustness --output results/replay_robustness.json
python -m uv run --extra dev python -m aurora.final_benchmark --suite legacy_bridge --output results/replay_bridge.json
python -m uv run --extra dev python -m streamlit run src/aurora/dashboard/final_app.py
```

Replays must use new output names; completed artifacts are not overwritten. In a clean workspace without results, use canonical `research_development_v2.json`, `research_final_v2.json`, `research_ablations_v2.json`, `research_robustness_v2.json` and `research_legacy_bridge_v2.json` names instead of replay names to regenerate this report. Resume interrupted JSONL checkpoints with --resume under the same source/config. Timing can differ while deterministic actions/outcomes replay. Run `python -m uv run --extra dev python scripts/render_final_report.py` after all canonical outputs exist.

Config SHA-256: `90850fe3777d8f160cfef8afb5a9cc6eba5417d5c3095067cc71da86b4e7638d`. Source SHA-256: `2bdfe7cc4169037002fc5e64c04722cb1c4565d5ed503c1727e51b1f72269473`. Source snapshot: `research_archive/research_final_v2_source.zip`. Step 1 and original source snapshots are preserved separately. No Git commit or executed remote CI is claimed; this workspace has no Git repository.

Test gate on the frozen scientific source: 182 passed; 28 regression passed; ruff clean. Locked dependency sync passed. The actual final result viewer and sampled held-out outcome replays are also checked during handoff. No real-world accuracy test is claimed.

Runtime metadata: `{"python": "3.14.0", "numpy": "2.5.4", "cpu": "Intel64 Family 6 Model 140 Stepping 1, GenuineIntel"}`. All four canonical result artifacts have complete planned counts, matching source/config hashes, and unchanged historical artifact hashes. Individual result hashes are recorded in `results/research_final_integrity_v2.json`.
