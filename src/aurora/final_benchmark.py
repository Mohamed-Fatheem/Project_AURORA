"""Research final-1: immutable manifests, paired missions and resumable artifacts."""

import argparse
import csv
import hashlib
import json
import platform
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

from aurora.evaluation import score_episode
from aurora.final_experiments import case_catalog, run_episode
from aurora.final_policies import ABLATIONS, POLICIES, Settings
from aurora.final_real_data import feasibility_report
from aurora.final_statistics import paired, summarize
from aurora.mission import run_mission
from aurora.research_mission import ACTION_COSTS
from aurora.simulator import scenarios

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "configs/research_final_v2.json"


def source_hash():
    digest = hashlib.sha256()
    for path in sorted((ROOT / "src/aurora").rglob("*.py")):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def load_manifest(path=MANIFEST):
    raw = path.read_bytes()
    config = json.loads(raw)
    partitions = [set(config[key]) for key in ("development_seeds", "final_seeds", "robustness_seeds")]
    historic = json.loads((ROOT / "configs/benchmark_v2.json").read_text())
    reserved = set(historic["train_seeds"] + historic["development_seeds"] + historic["heldout_seeds"] + list(range(200, 210)))
    prior = json.loads((ROOT / "configs/research_final_v1.json").read_text())
    reserved.update(prior["development_seeds"] + prior["final_seeds"] + prior["robustness_seeds"])
    if any(p & reserved for p in partitions) or any(partitions[i] & partitions[j] for i, j in ((0, 1), (0, 2), (1, 2))):
        raise ValueError("evaluation seed leakage")
    if any(len(config[key]) != len(set(config[key])) or not config[key]
           or any(not isinstance(s, int) or s < 0 or s >= 2**64 for s in config[key])
           for key in ("development_seeds", "final_seeds", "robustness_seeds")):
        raise ValueError("invalid or repeated seeds")
    if config["policies"] != list(POLICIES) or config["ablations"] != list(ABLATIONS):
        raise ValueError("policy manifest mismatch")
    if config["primary_settings"] != asdict(Settings()) or config["action_costs"] != {k: list(v) for k, v in ACTION_COSTS.items()}:
        raise ValueError("policy settings/action contract changed after freeze")
    if config.get("independent_case_noise") is not True:
        raise ValueError("independent case noise required for stratified intervals")
    if json.loads(json.dumps({name: asdict(case) for name, case in case_catalog().items()})) != config["cases"]:
        raise ValueError("scenario catalog changed after freeze")
    if config["primary_utility"] != {"correct": 10, "wrong": -20, "abstain": 0, "energy": .15, "time": .1}:
        raise ValueError("utility changed")
    return config, hashlib.sha256(raw).hexdigest()


def jobs(config, suite, limit=None):
    cases = case_catalog()
    if suite in ("development", "final"):
        seeds = config[suite + "_seeds"][:limit]
        for name, case in cases.items():
            if suite == "development" and name.startswith("unseen_"):
                continue
            for seed in seeds:
                for policy in POLICIES:
                    yield name, case, seed, Settings(policy=policy), policy
    elif suite == "ablations":
        for name, case in cases.items():
            for seed in config["robustness_seeds"][:limit]:
                for variant in ("none", *ABLATIONS):
                    yield name, case, seed, Settings(ablation=variant), variant
    elif suite == "robustness":
        for variant in config["robustness_variants"]:
            for name in config["robustness_cases"]:
                case = cases[name]
                changes = variant.get("world", {})
                case = replace(case, config=replace(case.config, **changes))
                settings = Settings(**variant.get("settings", {}))
                for seed in config["robustness_seeds"][:limit]:
                    yield name, case, seed, settings, variant["name"]
    else:
        raise ValueError("unknown experiment suite")


def run_suite(config, digest, suite, output: Path, limit=None, resume=False):
    if output.exists():
        raise FileExistsError("refusing to overwrite a completed result; choose a new output path")
    output.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = output.with_suffix(".jsonl")
    provenance = {"type": "metadata", "version": config["version"], "config_sha256": digest,
                  "source_sha256": source_hash(), "suite": suite, "limit": limit}
    rows = []
    if checkpoint.exists():
        if not resume:
            raise FileExistsError("checkpoint exists; use --resume with identical code/config")
        lines = checkpoint.read_text(encoding="utf8").splitlines()
        if json.loads(lines[0]) != provenance:
            raise ValueError("resume source/config mismatch")
        rows = [json.loads(line) for line in lines[1:]]
    else:
        checkpoint.write_text(json.dumps(provenance) + "\n", encoding="utf8")
    seen = {(r["case"], r["seed"], r["variant"]) for r in rows}
    with checkpoint.open("a", encoding="utf8") as stream:
        for name, case, seed, settings, variant in jobs(config, suite, limit):
            if (name, seed, variant) in seen:
                continue
            row = run_episode(case, seed, settings, independent_case_noise=True)
            row["variant"] = variant
            rows.append(row)
            stream.write(json.dumps(row) + "\n")
            stream.flush()
            if len(rows) % 100 == 0:
                print(f"{suite}: {len(rows)} episodes", flush=True)
    groups = {}
    for variant in sorted({r["variant"] for r in rows}):
        subset = [r for r in rows if r["variant"] == variant]
        groups[variant] = summarize(subset, config["bootstrap_resamples"])
    by_case = {name: {variant: summarize([r for r in rows if r["case"] == name and r["variant"] == variant],
                                       config["bootstrap_resamples"])
                      for variant in sorted({r["variant"] for r in rows if r["case"] == name})}
               for name in sorted({r["case"] for r in rows})}
    result = {**provenance, "manifest": config, "schema": "research-final-result-1", "n_episode_rows": len(rows),
              "partial": limit is not None, "summary": groups, "by_case": by_case,
              "paired": paired(rows, resamples=config["bootstrap_resamples"]) if suite in ("development", "final") else {},
              "generalization": {policy: summarize([r for r in rows if r["policy"] == policy and r["case"].startswith("unseen_")],
                                                     config["bootstrap_resamples"])
                                 for policy in POLICIES} if suite == "final" else {},
              "runtime": {"python": platform.python_version(), "numpy": np.__version__, "cpu": platform.processor()},
              "uncertainty": "Wilson intervals for episode proportions; case-stratified paired episode bootstrap for means/F1; clustered episode bootstrap for active faults",
              "rows": rows, "real_data": feasibility_report()}
    if suite == "ablations":
        reference = [dict(r, policy="improved_voi") for r in rows if r["variant"] == "none"]
        comparators = [dict(r, policy=r["variant"]) for r in rows if r["variant"] != "none"]
        result["paired"] = paired(reference + comparators, resamples=config["bootstrap_resamples"])
    output.write_text(json.dumps(result, indent=2), encoding="utf8")
    with output.with_suffix(".csv").open("w", newline="", encoding="utf8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["variant", "n", "correct", "claims", "accuracy", "false_conclusion_proportion", "utility", "initial_fault_recall", "unknown_recall"])
        for variant, summary in groups.items():
            writer.writerow([variant, summary["n"], summary["accuracy"]["numerator"], summary["coverage"]["numerator"],
                             summary["accuracy"]["value"], summary["false_conclusion_proportion"]["value"],
                             summary["utility"]["mean"], summary["initial_fault"]["recall"]["value"],
                             summary["unknown"]["recall"]["value"]])
    print(f"Saved {output} ({len(rows)} rows)", flush=True)
    return result


def legacy_bridge(config, output, limit=None):
    if output.exists():
        raise FileExistsError("historical bridge output already exists")
    rows = []
    for world in scenarios().values():
        for seed in config["final_seeds"][:limit]:
            mission, truth = run_mission(world, seed, noise_mode="keyed")
            rows.append(asdict(score_episode(mission, truth, world)))
    result = {"contract": "untouched original VOI and scoring; not a matched-contract ranking",
              "source_sha256": source_hash(), "rows": rows}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=("development", "final", "ablations", "robustness", "legacy_bridge"), required=True)
    parser.add_argument("--config", type=Path, default=MANIFEST)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.limit is not None and args.limit <= 0:
        parser.error("limit must be positive")
    config, digest = load_manifest(args.config)
    if args.suite == "legacy_bridge":
        legacy_bridge(config, args.output, args.limit)
    else:
        run_suite(config, digest, args.suite, args.output, args.limit, args.resume)


if __name__ == "__main__":
    main()
