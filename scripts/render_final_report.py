"""Regenerate the final report strictly from complete frozen experiment artifacts."""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aurora.final_benchmark import load_manifest, source_hash


def number(value, digits=3):
    return value if isinstance(value, str) else f"{value:.{digits}f}"


def proportion(record):
    value = record["value"]
    return "N/A" if isinstance(value, str) else f"{100 * value:.1f}% ({record['numerator']}/{record['denominator']})"


def interval(record):
    return f"{number(record['mean'])} [{number(record['ci95'][0])}, {number(record['ci95'][1])}]"


def main():
    config, digest = load_manifest()
    freeze = json.loads((ROOT / "research_archive/research_final_v2_freeze.json").read_text())
    if source_hash() != freeze["source_sha256"] or digest != freeze["config_sha256"]:
        raise ValueError("source/config differs from frozen evaluation")
    expected_counts = {"development": 1400, "final": 5000, "ablations": 1400, "robustness": 960}
    artifacts = {}
    integrity = {}
    for suite, expected in expected_counts.items():
        path = ROOT / f"results/research_{suite}_v2.json"
        result = json.loads(path.read_text(encoding="utf8"))
        if (result["partial"] or result["n_episode_rows"] != expected
                or result["config_sha256"] != digest or result["source_sha256"] != source_hash()):
            raise ValueError(f"incomplete or incompatible {suite} result")
        artifacts[suite] = result
        integrity[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    bridge_path = ROOT / "results/research_legacy_bridge_v2.json"
    bridge = json.loads(bridge_path.read_text(encoding="utf8"))
    if len(bridge["rows"]) != 300 or bridge["source_sha256"] != source_hash():
        raise ValueError("invalid untouched legacy bridge")
    preserved = json.loads((ROOT / "research_archive/preserved_hashes.json").read_text())
    for path, expected in preserved.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError(f"historical artifact changed: {path}")
    original = json.loads((ROOT / "results/benchmark_heldout.json").read_text())
    final, development, ablations, robustness = (artifacts[k] for k in ("final", "development", "ablations", "robustness"))
    lines = ["# AURORA — final research report (Step 2)", "",
             "Version `research-final-2`. All results below are measured synthetic evidence. Official APXS data supports a feasibility demonstration only.", "",
             "## 1. Problem and objectives", "",
             "Distinguish supported geological evidence, instrument faults and unsupported geology while choosing feasible experiments. Correct the original initial/active fault timing error, test difficult unknowns and evaluate transparent tradeoffs without inventing performance improvements.", "",
             "## 2. Architecture and algorithms", "",
             "The original simulator/inference/planner remain intact. A separate continuous 196-state audit model integrates persistent unknown sensor means, uncertain signed bias/drift hypotheses, pre-reset reference evidence and repair masks. The matched runner shares budgets, action costs, keyed science/reference noise, reference access and two-instrument verification across all five policies. The adapted original VOI retains its seven-bin 36-state model. Exact binned enumeration and 7-node continuous quadrature score one-step terminal utility. Calibration scoring conservatively omits the reference-information bonus. Information gain ranks discrete latent-state entropy reduction; it does not integrate continuous unknown-mean entropy.", "",
             "## 3. Original weaknesses and corrections", "",
             "Calibration formerly erased fault beliefs before observation and endpoint scoring compared repaired state with initial truth. Initial identities now survive repair; active faults are scored before repair and after actions against contemporaneous truth. Reference readings decouple offset evidence from geology under the synthetic reference-transfer assumption. Signed fault support and continuous likelihoods retain more evidence. Supported sulfate recall is separated from unsupported-geology detection; the legacy metric and BUG-002 remain preserved.", "",
             "## 4. Experimental methodology", "",
             "Frozen manifest: `configs/research_final_v2.json`. Development: 14 families × 20 separate seeds × 5 policies = 1,400 rows. Final: 20 families × 50 seeds × 5 policies = 5,000 rows (1,000 per policy), including six families excluded from development. Ablations: 1,400 rows; sensitivity: 960 rows; untouched historical bridge: 300 rows. Total: 9,060 missions in the corrected version. An earlier v1 run reused noise across scenario families; it was preserved as superseded before final aggregate scores were inspected. V2 adds a case-name stream key and uses fresh untouched seed partitions, without changing policy parameters. No final-set tuning or threshold search was performed.", "",
             "Primary utility stays +10 correct, −20 incorrect, 0 abstain, minus 0.15/Wh and 0.10/hour. All primary policies share 12 Wh, 12 h and five acquisition actions. Fault/unknown thresholds stay 0.5. Reward changes occur only in labeled sensitivity arms. Wilson 95% intervals describe episode proportions; case-stratified paired episode bootstrap uses 1,000 resamples, seed 42026, for means/F1/differences. Active-fault uncertainty resamples whole episode clusters. Multiple comparisons are exploratory and unadjusted. Latencies measure actual selection calls, including terminal calls.", "",
             "## 5. Comparative results with uncertainty", "",
             "The broader distribution includes 600 supported and 400 unsupported episodes per policy. Safe abstention is not counted as a correct supported conclusion, so the maximum conclusion-accuracy value is 60% on this mixture. This is the original correct-conclusions/all-episodes definition, not a standard four-class accuracy counting unknown abstentions as correct labels. Raw accuracy is therefore not directly comparable with the six-preset Stage 5 accuracy. Improved VOI correctly concluded 594/600 supported cases while still making 180 incorrect claims across all 1,000 episodes; a known-only percentage would hide those unsupported-case errors.", "",
             "| Matched policy | Conclusion accuracy | Wrong / claims | False-conclusion proportion (95% CI) | Mean utility (95% CI) | Mean regret |",
             "| --- | --- | --- | --- | --- | --- |"]
    for policy, summary in final["summary"].items():
        fdp = summary["false_conclusion_proportion"]
        ci = fdp["ci95"]
        lines.append(f"| {policy} | {proportion(summary['accuracy'])} | {fdp['numerator']}/{fdp['denominator']} | {number(fdp['value'])} [{number(ci[0])}, {number(ci[1])}] | {interval(summary['utility'])} | {number(summary['regret']['mean'])} |")
    improved, comparator = final["summary"]["improved_voi"], final["summary"]["original_voi"]
    lines += ["", f"Explicit regression/tradeoff: improved VOI made {improved['accuracy']['numerator']} correct conclusions versus {comparator['accuracy']['numerator']} for matched original VOI. Its accuracy difference is {100 * (improved['accuracy']['value'] - comparator['accuracy']['value']):.2f} percentage points. Improved VOI abstained in {improved['abstention']['numerator']} episodes versus {comparator['abstention']['numerator']}; higher utility and fewer false claims do not imply higher conclusion accuracy. It still made {improved['false_conclusion_proportion']['numerator']} wrong claims."]
    lines += ["", "| Policy | Initial fault P / R / F1 | Unknown P / R / F1 | Coverage | Supported sulfate recall |", "| --- | --- | --- | --- | --- |"]
    for policy, summary in final["summary"].items():
        f, u = summary["initial_fault"], summary["unknown"]
        lines.append(f"| {policy} | {' / '.join(number(f[k]['value']) for k in ('precision','recall','f1'))} | {' / '.join(number(u[k]['value']) for k in ('precision','recall','f1'))} | {proportion(summary['coverage'])} | {proportion(summary['supported_discovery_recall'])} |")
    initial_f1 = improved["initial_fault"]["f1"]
    unknown_f1 = improved["unknown"]["f1"]
    lines += ["", f"Improved initial-fault F1 is {number(initial_f1['value'])}, 95% bootstrap CI [{number(initial_f1['ci95'][0])}, {number(initial_f1['ci95'][1])}]; a point target of 0.8 is not met. Unknown F1 is {number(unknown_f1['value'])} [{number(unknown_f1['ci95'][0])}, {number(unknown_f1['ci95'][1])}] on the harder distribution, replacing the earlier easy-case impression of perfect detection."]
    lines += ["", "Full confusion counts, Wilson intervals for precision/recall, bootstrap F1 intervals, Brier scores and active instrument-time counts are in the JSON; active readings are not independent episode observations.", "",
              "| Policy | Energy / time used, mean | Selection median / p95 | Within budget |", "| --- | --- | --- | --- |"]
    for policy, summary in final["summary"].items():
        latency = summary["decision_latency"]
        lines.append(f"| {policy} | {number(summary['energy_used_wh']['mean'])} Wh / {number(summary['time_used_h']['mean'])} h | {number(latency['median_s'],4)} / {number(latency['p95_s'],4)} s | {proportion(summary['within_budget'])} |")
    lines += ["", "Paired utility differences are improved VOI minus comparator:", "", "| Comparator | Mean difference | 95% paired CI |", "| --- | --- | --- |"]
    for policy, values in final["paired"].items():
        lines.append(f"| {policy} | {number(values['mean_utility_difference'])} | [{number(values['ci95'][0])}, {number(values['ci95'][1])}] |")
    lines += ["", "Original Stage 5, preserved and not a matched comparison:", "", "| Original policy | Wrong / claims | Mean utility |", "| --- | --- | --- |"]
    for policy, summary in original["summary"].items():
        counts = summary["denominators"]
        lines.append(f"| {policy} | {counts['false_claims']}/{counts['claims']} | {number(summary['mean_utility'])} |")
    old_rows = bridge["rows"]
    lines += ["", f"Untouched original VOI bridge on 300 new episodes from the original six presets: {sum(r['correct'] for r in old_rows)}/300 correct conclusions, {sum(r['claimed'] and not r['correct'] for r in old_rows)} wrong claims, mean utility {number(sum(r['utility'] for r in old_rows)/len(old_rows))}. Its original action/information/scoring contract differs from the matched runner. Thus neither this bridge nor benchmark-2 is evidence of an isolated policy improvement.", "",
              "Matched six-preset subset under the new shared contract:", "", "| Policy | Correct / episodes | Wrong claims | Mean utility |", "| --- | --- | --- | --- |"]
    for policy in config["policies"]:
        rows = [r for r in final["rows"] if r["policy"] == policy and r["case"] in ("ordinary","unusual","bias","drift","conflict","outside")]
        lines.append(f"| {policy} | {sum(r['correct'] for r in rows)}/{len(rows)} | {sum(r['claimed'] and not r['correct'] for r in rows)} | {number(sum(r['utility'] for r in rows)/len(rows))} |")
    lines += ["", "## 6. Ablations, robustness and unseen scenarios", "",
              "Each ablation changes only its named component while keeping exogenous worlds, costs and scoring fixed. No-reference masks inference updates while preserving generated readings. Gate removal changes policy admissibility; no-cost changes ranking, not physical resource constraints.", "",
              "| Ablation | Mean utility | Accuracy | Fault recall | Unknown recall | Nominal minus arm utility (95% CI) |", "| --- | --- | --- | --- | --- | --- |"]
    for variant, summary in ablations["summary"].items():
        difference = ablations["paired"].get(variant)
        delta = "reference" if difference is None else f"{number(difference['mean_utility_difference'])} [{number(difference['ci95'][0])}, {number(difference['ci95'][1])}]"
        lines.append(f"| {variant} | {number(summary['utility']['mean'])} | {proportion(summary['accuracy'])} | {number(summary['initial_fault']['recall']['value'])} | {number(summary['unknown']['recall']['value'])} | {delta} |")
    lines += ["", f"Component limitation: the verification-removal arm has mean utility {number(ablations['summary']['no_verification']['utility']['mean'])} versus nominal {number(ablations['summary']['none']['utility']['mean'])}. This experiment does not establish that mandatory cross-instrument verification improves utility. The table reports that result even though verification was introduced as a safety criterion in Step 1."]
    lines += ["", "Sensitivity arms (separate seeds, six development families, 60 episodes per arm):", "", "| Variant | Mean utility | Accuracy | Fault recall | Unknown recall |", "| --- | --- | --- | --- | --- |"]
    for variant, summary in robustness["summary"].items():
        lines.append(f"| {variant} | {number(summary['utility']['mean'])} | {proportion(summary['accuracy'])} | {number(summary['initial_fault']['recall']['value'])} | {number(summary['unknown']['recall']['value'])} |")
    lines += ["", f"Noise failure: the high-noise arm has unknown recall {number(robustness['summary']['noise_high']['unknown']['recall']['value'])}, versus nominal {number(robustness['summary']['nominal']['unknown']['recall']['value'])}. The model is not robust to these noisy overlapping unknowns. The 15-node arm has mean utility {number(robustness['summary']['quadrature_15']['utility']['mean'])}, compared with 7-node nominal {number(robustness['summary']['nominal']['utility']['mean'])}; this limited resolution check is not a proof of general quadrature convergence."]
    lines += ["", "These sensitivity scores retain their own declared reward setting. Scores from changed rewards are not ranked as primary-policy improvements. Parameters were not retuned after viewing them.", "",
              "Generalization to six held-out scenario families (300 episodes per policy):", "", "| Policy | Accuracy | Unknown recall | Fault recall | Utility |", "| --- | --- | --- | --- | --- |"]
    for policy, summary in final["generalization"].items():
        lines.append(f"| {policy} | {proportion(summary['accuracy'])} | {number(summary['unknown']['recall']['value'])} | {number(summary['initial_fault']['recall']['value'])} | {number(summary['utility']['mean'])} |")
    lines += ["", "Development means (reported, not used for final tuning): " + "; ".join(f"{p}: {number(s['utility']['mean'])}" for p,s in development["summary"].items()) + ".", "",
              "Improved VOI failures by final case:", "", "| Case | Correct / episodes | Wrong claims | Unknown recall | Fault recall |", "| --- | --- | --- | --- | --- |"]
    for name, policies in final["by_case"].items():
        summary = policies["improved_voi"]
        lines.append(f"| {name} | {summary['accuracy']['numerator']}/{summary['n']} | {summary['false_conclusion_proportion']['numerator']} | {number(summary['unknown']['recall']['value'])} | {number(summary['initial_fault']['recall']['value'])} |")
    lines += ["", "## 7. Real-data feasibility", "",
              "The existing official [PDS APXS product](https://pds-geosciences.wustl.edu/missions/msl/apxs.htm) contributes 16 analyte concentration/precision pairs, kept in their PDS4 label's weight-percent units with original timestamps and hashes. No normalization or mapping into synthetic indices is applied. The [official APXS tutorial](https://pds-geosciences.wustl.edu/workshops/DPS_2020_Presentations/2020-1027-DPS-APXS-Tutorial.pdf) distinguishes reported precision from accuracy and warns that exports may use different units for trace elements. This loader follows the specific product label rather than mixing export formats. Covariance, systematic accuracy and ground-truth failure/geology labels remain unavailable in this product. Consequently no defensible real-world classification, fault F1 or autonomy utility is computed. Status: feasibility_only.", "",
              "## 8. Remaining limitations and negative results", "",
              "Exact observational aliases cannot be identified from these sensors. Overlapping unknowns, weak drift and faults outside the finite hypothesis support can still yield confident incorrect claims. Reference transferability and perfect reset are synthetic assumptions. The unknown prior has independent instrument means; quadrature and omitted calibration-reference value are approximations. Verification costs resources and can force abstention. Fault diagnosis still has no direct utility reward. An apparent synthetic improvement does not establish real-spacecraft validity. Case-balanced confidence intervals do not cover all possible geology; multiple-comparison effects are unadjusted. No test target is declared passed solely from a favorable point estimate.", "",
              "## 9. Future work", "",
              "Acquire independent reference/repair and geology labels; construct physically calibrated multi-instrument likelihoods; model imperfect repair and correlated measurement uncertainty; study longer-horizon experiment value and utility elicitation; evaluate additional unseen distributions with a new preregistration. Do not tune on this final set.", "",
              "## 10. Reproduction and integrity", "",
              "```powershell", "python -m uv sync --locked --extra dev", "python -m uv run --extra dev python -m pytest -q", "python -m uv run --extra dev python -m ruff check .",
              "python -m uv run --extra dev python -m aurora.final_benchmark --suite development --output results/replay_development.json",
              "python -m uv run --extra dev python -m aurora.final_benchmark --suite final --output results/replay_final.json",
              "python -m uv run --extra dev python -m aurora.final_benchmark --suite ablations --output results/replay_ablations.json",
              "python -m uv run --extra dev python -m aurora.final_benchmark --suite robustness --output results/replay_robustness.json",
              "python -m uv run --extra dev python -m aurora.final_benchmark --suite legacy_bridge --output results/replay_bridge.json",
              "python -m uv run --extra dev python -m streamlit run src/aurora/dashboard/final_app.py", "```", "",
              "Replays must use new output names; completed artifacts are not overwritten. In a clean workspace without results, use canonical `research_development_v2.json`, `research_final_v2.json`, `research_ablations_v2.json`, `research_robustness_v2.json` and `research_legacy_bridge_v2.json` names instead of replay names to regenerate this report. Resume interrupted JSONL checkpoints with --resume under the same source/config. Timing can differ while deterministic actions/outcomes replay. Run `python -m uv run --extra dev python scripts/render_final_report.py` after all canonical outputs exist.", "",
              f"Config SHA-256: `{digest}`. Source SHA-256: `{source_hash()}`. Source snapshot: `research_archive/research_final_v2_source.zip`. Step 1 and original source snapshots are preserved separately. No Git commit or executed remote CI is claimed; this workspace has no Git repository.", "",
              f"Test gate on the frozen scientific source: {freeze['test_gate']}. Locked dependency sync passed. The actual final result viewer and sampled held-out outcome replays are also checked during handoff. No real-world accuracy test is claimed.", "",
              f"Runtime metadata: `{json.dumps(final['runtime'])}`. All four canonical result artifacts have complete planned counts, matching source/config hashes, and unchanged historical artifact hashes. Individual result hashes are recorded in `results/research_final_integrity_v2.json`."]
    (ROOT / "docs/FINAL_RESEARCH_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    for path in (ROOT / "docs/FINAL_RESEARCH_REPORT.md", Path(__file__).resolve()):
        integrity[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    (ROOT / "results/research_final_integrity_v2.json").write_text(json.dumps(integrity, indent=2), encoding="utf8")
    print("Generated docs/FINAL_RESEARCH_REPORT.md from complete verified artifacts")


if __name__ == "__main__":
    main()
