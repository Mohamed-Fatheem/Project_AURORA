# AURORA Stage 5 exploratory results

Measured 2026-11-14 on Windows, Python 3.14.0, CPU reported as
`Intel64 Family 6 Model 140 Stepping 1, GenuineIntel`. This report describes
**synthetic simulator results**, not verified planetary discoveries.

## Frozen method and provenance

The final manifest is `configs/benchmark_v2.json`, version `benchmark-2`,
SHA-256 prefix `740ec9df4cf5`; source SHA-256 prefix `43f894937f19`.
Ten development seeds (100–109) and ten held-out seeds (1000–1009) are
disjoint from the training seed partition (0–9). No policy tuning was done
between the development and held-out runs. All six registered scenarios were
run for each seed and each of four policies: **60 episodes per policy and
240 paired-policy rows per split**. Four ablations add 60 episodes each per
split. `results/benchmark_development.json` and
`results/benchmark_heldout.json` hold per-episode rows, denominators, metrics,
paired intervals, configuration and source hashes; adjacent CSV files hold
compact per-scenario summaries. The files are generated locally and ignored
by Git. Regenerate them with the commands in `README.md`.

All policies had the same initial budgets, horizon, action contracts and
utility. Keyed NumPy `SeedSequence` noise shares the *k*th exogenous noise
draw for each instrument across divergent policy paths. Faults and geology
are fixed per scenario. Utility is +10 for a correct known-geology conclusion,
-20 for a wrong one, 0 for abstention, minus 0.15 per Wh and 0.10 per hour.
The privileged oracle is an offline upper reference (10 for known truth, 0
for outside-family truth), never a deployable comparator. Paired utility
differences use 1,000 episode-level bootstrap resamples, seed 2026,
percentile 2.5/97.5 intervals.

## Held-out outcome

| Policy | Wrong claims / claims | False conclusion proportion | Discovery recall | Mean utility | Mean oracle regret | Median whole-mission latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| VOI | 0 / 50 | 0.000 | 0.500 | 7.020 | 1.313 | 0.132 s |
| Fixed model | 14 / 46 | 0.304 | 0.500 | -0.657 | 8.990 | 0.112 s |
| Information gain | 4 / 50 | 0.080 | 0.500 | 5.300 | 3.033 | 0.153 s |
| Threshold | 33 / 60 | 0.550 | 0.500 | -7.160 | 15.493 | 0.005 s |

Discovery-positive truth includes sulfate and outside-family episodes (20 of
60 per policy). There is no valid supported-class claim for outside-family
truth, so the maximum recall under this metric is 0.5. The small sample and
synthetic design do not establish a general false-conclusion reduction.
The paired mean utility difference, VOI minus comparator, was +7.677
(95% CI 4.484 to 10.937) versus fixed model, +1.720 (0.213 to 3.697)
versus information gain, and +14.180 (10.597 to 17.442) versus threshold.
These intervals cover this synthetic scenario distribution only.

Unknown-state F1 was 1.0 for VOI, fixed model and information gain on the
10 outside-family episodes, but the simulator places their values far from
most supported means. This result does not imply real unknown-geology
detection. **Fault F1 for VOI, fixed model and information gain is N/A:**
each made zero positive fault predictions at the frozen 0.5 threshold while
30 of 60 episodes had an initial fault. VOI fault recall was 0.0.
Threshold fault F1 was 0.182. The benchmark's endpoint fault score is also
confounded by calibration, which can remove a fault before scoring.
VOI unknown-state Brier score was 0.000260 on this constructed binary event.
Latency is whole-mission wall time on this host, not isolated planner latency;
the Stage 5 planning target cannot be claimed from it.

## Development and ablations

Development mean utility was VOI 7.063, information gain 7.300, fixed model
1.352 and threshold -5.293. Information gain slightly exceeded VOI in
development; this negative comparison was not tuned away. Held-out ablation
mean utilities were no fault -0.657, no adequacy 3.053, information gain
5.300 and no resource penalty 6.100. Their false-conclusion proportions
were 0.304, 0.200, 0.080 and 0.000 respectively. Removing resource penalties
changes the ranking objective while feasibility remains fixed, so its score
does not isolate resource constraints. These are coupled policy effects,
not causal estimates of individual components.

## Versioned scoring correction

An initial `benchmark-1` run mistakenly credited the fixed-model baseline
with fault predictions from the joint posterior, contrary to its declared
healthy-instrument assumption. The user approved a versioned correction.
The original development and held-out JSON files are preserved as
`results/benchmark_v1_superseded_*.json`; do not use them for claims.
`benchmark-2` projects the fixed-model belief onto healthy-instrument states
for offline detection scoring. A targeted regression test (`BUG-002`) covers
this case. Action sequences and utility definitions were unchanged. The
final outputs were rerun from the versioned manifest after the correction.

## Real-product feasibility and limits

One [official PDS APXS calibrated product](https://pds-geosciences.wustl.edu/missions/msl/apxs.htm)
was downloaded with its PDS4 label and parsed: 16 oxide/element concentrations
and uncertainties in weight percent. The check validates provenance, schema,
units and finite values; details and hashes are in `docs/REAL_DATA.md`.
The result status is `qualitative_schema_only`. These measurements are not
mapped into AURORA's dimensionless synthetic likelihood. The product supplies
no independent geological class or instrument fault labels, so **no real-world
geology, fault or autonomy accuracy has been measured**.

## Threats to validity

The six scenario presets, priors, unknown model, fault magnitudes and rewards
are synthetic and narrow. Binning loses information. A +1.5 conflict bias
differs from the model's +1.2 assumption. Only ten held-out seeds per preset
make rate estimates imprecise; no confidence interval was computed for false
conclusion proportions. All policies share the same simulator family, though
their assumptions differ. No human utility elicitation, real fault ground
truth, or deployment study exists. Some benchmark comparisons look favorable
while the fault-detection target fails; both are reported here.
