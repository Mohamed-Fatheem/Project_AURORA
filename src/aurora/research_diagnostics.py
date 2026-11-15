"""Step 1 development diagnostics, never a final benchmark or tuning runner."""

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from aurora.evaluation import brier, calibration_bins, confusion, precision_recall_f1, score_episode
from aurora.mission import run_mission
from aurora.research_mission import development_cases, run_audit
from aurora.research_model import INSTRUMENTS
from aurora.simulator import Condition, Geology, scenarios

ROOT = Path(__file__).resolve().parents[2]


def diagnostic_summary(rows):
    counts = confusion([r["initial_fault_truth"] for r in rows],
                       [r["initial_fault_predicted"] for r in rows])
    unknown = confusion([r["unknown_truth"] for r in rows], [r["unknown_predicted"] for r in rows])
    claims = sum(r["claimed"] for r in rows)
    correct = sum(r["correct"] for r in rows)
    sulfate = [r for r in rows if r["truth"] == "sulfate"]
    probability_metrics = {}
    if all("initial_fault_probability" in r for r in rows):
        probabilities = [r["initial_fault_probability"] for r in rows]
        truth = [r["initial_fault_truth"] for r in rows]
        probability_metrics = {"initial_fault_brier": brier(probabilities, truth),
                               "initial_fault_calibration": calibration_bins(probabilities, truth),
                               "unknown_brier": brier([r["unknown_probability"] for r in rows],
                                                       [r["unknown_truth"] for r in rows]),
                               "fault_threshold_sensitivity": {
                                   str(t): {**confusion(truth, [p >= t for p in probabilities]),
                                            **precision_recall_f1(confusion(truth, [p >= t for p in probabilities]))}
                                   for t in (.25, .5, .75)},
                               "post_action_instrument_counts": {
                                   key: sum(r["active_fault_counts"][key] for r in rows)
                                   for key in ("tp", "fp", "tn", "fn")},
                               "initial_faults_removed": sum(r["initial_faults_removed"] for r in rows)}
    return {"n": len(rows), "claims": claims, "correct": correct, **probability_metrics,
            "wrong_claims": claims - correct, "abstentions": len(rows) - claims,
            "accuracy": correct / len(rows), "mean_utility": float(np.mean([r["utility"] for r in rows])),
            "initial_fault": {**counts, **precision_recall_f1(counts)},
            "unsupported_geology": {**unknown, **precision_recall_f1(unknown)},
            "supported_sulfate_recall": (sum(r["correct"] for r in sulfate) / len(sulfate)
                                         if sulfate else "N/A")}


def run_diagnostics():
    path = ROOT / "configs/research_step1.json"
    config = json.loads(path.read_text())
    historic = json.loads((ROOT / "configs/benchmark_v2.json").read_text())
    reserved = set(historic["heldout_seeds"] + historic["development_seeds"] + historic["train_seeds"])
    if reserved.intersection(config["seeds"]):
        raise ValueError("diagnostic seeds overlap historical partitions")
    before, after = [], []
    replay = []
    for name, case in development_cases().items():
        world = case.config
        for seed in config["seeds"]:
            mission = run_audit(case, seed, config["unknown_prior"])
            last = mission.events[-1] if mission.events else None
            claimed = mission.terminal != "abstain"
            correct = claimed and mission.terminal == world.geology.value
            utility = (10 if correct else -20 if claimed else 0) - (
                .15 * (world.energy_wh - mission.energy_wh) + .1 * (world.time_h - mission.time_h))
            truth_fault = any(c != Condition.HEALTHY for c in world.conditions.values())
            row = {"case": name, "seed": seed, "truth": world.geology.value,
                   "claimed": claimed, "correct": correct, "utility": utility,
                   "terminal": mission.terminal, "initial_fault_truth": truth_fault,
                   "initial_fault_probability": last.initial_any_fault if last else .36,
                   "initial_fault_predicted": bool(last and last.initial_any_fault >= .5),
                   "unknown_truth": world.geology == Geology.OTHER,
                   "unknown_probability": last.geology[3] if last else .1,
                   "unknown_predicted": bool(last and last.geology[3] >= .5),
                   "energy_used_wh": world.energy_wh - mission.energy_wh,
                   "remaining_energy_wh": mission.energy_wh, "remaining_time_h": mission.time_h}
            active_truth, active_prediction = [], []
            repaired = set()
            for event in mission.events:
                if event.action == "calibrate_spectrometer":
                    repaired.add("spectrometer")
                for i, instrument in enumerate(INSTRUMENTS):
                    active_truth.append(world.conditions[instrument] != Condition.HEALTHY
                                        and instrument not in repaired)
                    active_prediction.append(event.active_fault[i] >= .5)
            row["active_fault_counts"] = confusion(active_truth, active_prediction)
            row["initial_faults_removed"] = sum(world.conditions[n] != Condition.HEALTHY
                                                  for n in repaired)
            after.append(row)
            if seed == config["seeds"][0]:
                replay.append({"case": name, "mission": asdict(mission)})
            if name in scenarios():
                old, truth = run_mission(world, seed, noise_mode="keyed")
                scored = score_episode(old, truth, world)
                before.append({"case": name, "seed": seed, "truth": world.geology.value,
                               "claimed": scored.claimed, "correct": scored.correct,
                               "utility": scored.utility, "initial_fault_truth": scored.fault_truth,
                               "initial_fault_predicted": scored.fault_predicted,
                               "unknown_truth": scored.unknown_truth,
                               "unknown_predicted": scored.unknown_predicted})
    matched = [r for r in after if r["case"] in scenarios()]
    hashes = json.loads((ROOT / "research_archive/preserved_hashes.json").read_text())
    preserved = all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == digest
                    for p, digest in hashes.items())
    source = hashlib.sha256()
    for module in sorted((ROOT / "src/aurora").rglob("*.py")):
        source.update(module.relative_to(ROOT).as_posix().encode())
        source.update(module.read_bytes())
    return {"version": config["version"], "partition": "development_only",
            "config_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "source_sha256": source.hexdigest(), "historical_artifacts_preserved": preserved,
            "before_matched": diagnostic_summary(before), "after_matched": diagnostic_summary(matched),
            "after_all": diagnostic_summary(after),
            "by_case": {name: diagnostic_summary([r for r in after if r["case"] == name])
                        for name in development_cases()},
            "rows": after, "representative_replays": replay,
            "caveats": ["reference observations add information; before/after is not an isolated algorithm effect",
                        "diagnostic development seeds only; no final claims",
                        "calibration score separates initial and active faults",
                        "supported discovery recall excludes unsupported geology; old metric is preserved",
                        "no empirically calibrated threshold claim"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_diagnostics()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps({k: result[k] for k in ("before_matched", "after_matched", "after_all")}, indent=2))


if __name__ == "__main__":
    main()
