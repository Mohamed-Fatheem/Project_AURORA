"""Versioned paired synthetic benchmark CLI. No policy sees private truth."""

import argparse
import csv
import hashlib
import json
import platform
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from aurora.evaluation import Episode, paired_bootstrap, score_episode, summarize
from aurora.mission import run_mission
from aurora.planning import ENERGY_PENALTY, TIME_PENALTY
from aurora.planning import VERSION as POLICY_VERSION
from aurora.real_data import official_product_status
from aurora.simulator import scenarios

DEFAULT_MANIFEST = Path(__file__).resolve().parents[2] / "configs/benchmark_v2.json"
ABLATIONS = ("no_fault", "no_adequacy", "info_gain", "no_cost")


@dataclass(frozen=True)
class BenchmarkConfig:
    version: str
    scenarios: tuple[str, ...]
    policies: tuple[str, ...]
    train_seeds: tuple[int, ...]
    development_seeds: tuple[int, ...]
    heldout_seeds: tuple[int, ...]
    bootstrap_seed: int
    bootstrap_resamples: int
    noise_mode: str
    fault_threshold: float
    unknown_threshold: float
    discovery_positive_geologies: tuple[str, ...]
    reward_correct: float
    reward_wrong: float
    energy_penalty: float
    time_penalty: float
    abstain_reward: float
    escalate_reward: float

    def __post_init__(self) -> None:
        partitions = (set(self.train_seeds), set(self.development_seeds),
                      set(self.heldout_seeds))
        if any(len(partition) != len(raw) for partition, raw in zip(partitions, (
            self.train_seeds, self.development_seeds, self.heldout_seeds
        ))) or any(partitions[i] & partitions[j] for i, j in ((0, 1), (0, 2), (1, 2))):
            raise ValueError("benchmark seed partitions overlap or repeat")
        if any(not isinstance(seed, int) or seed < 0 or seed >= 2**64
               for partition in (self.train_seeds, self.development_seeds, self.heldout_seeds)
               for seed in partition):
            raise ValueError("benchmark seeds must be unsigned 64-bit integers")
        if not self.scenarios or not set(self.scenarios) <= set(scenarios()):
            raise ValueError("unknown or empty scenario set")
        if self.policies != ("voi", "fixed_model", "information_gain", "threshold"):
            raise ValueError("registered policy list changed")
        if self.noise_mode != "keyed" or self.bootstrap_resamples <= 0:
            raise ValueError("benchmark requires keyed noise and positive resamples")
        if (self.fault_threshold != 0.5 or self.unknown_threshold != 0.5 or
                self.discovery_positive_geologies != ("sulfate", "other")):
            raise ValueError("metric manifest differs from evaluator")
        if (self.reward_correct, self.reward_wrong, self.energy_penalty,
                self.time_penalty, self.abstain_reward, self.escalate_reward) != (
            10.0, -20.0, ENERGY_PENALTY, TIME_PENALTY, 0.0, 1.0
        ):
            raise ValueError("utility manifest differs from policy implementation")


def load_config(path: Path = DEFAULT_MANIFEST) -> tuple[BenchmarkConfig, str]:
    raw = path.read_bytes()
    data = json.loads(raw)
    for key in ("scenarios", "policies", "train_seeds", "development_seeds",
                "heldout_seeds", "discovery_positive_geologies"):
        data[key] = tuple(data[key])
    return BenchmarkConfig(**data), hashlib.sha256(raw).hexdigest()


def source_sha256() -> str:
    root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _run_one(config: BenchmarkConfig, scenario: str, seed: int, policy: str,
             ablation: str = "none") -> Episode:
    world = scenarios()[scenario]
    start = time.perf_counter()
    mission, truth = run_mission(world, seed, policy, noise_mode=config.noise_mode,
                                ablation=ablation)
    latency = time.perf_counter() - start
    return score_episode(mission, truth, world, latency)


def run_benchmark(config: BenchmarkConfig, config_hash: str, split: str = "heldout",
                  limit: int | None = None, ablations: bool = True) -> dict:
    if split not in ("development", "heldout"):
        raise ValueError("split must be development or heldout")
    seeds = getattr(config, f"{split}_seeds")
    if limit is not None:
        if limit <= 0:
            raise ValueError("limit must be positive")
        seeds = seeds[:limit]
    episodes = [_run_one(config, scenario, seed, policy)
                for scenario in config.scenarios for seed in seeds for policy in config.policies]
    by_policy = {policy: summarize([e for e in episodes if e.policy == policy])
                 for policy in config.policies}
    by_scenario = {scenario: {policy: summarize([e for e in episodes if e.scenario == scenario
                                               and e.policy == policy]) for policy in config.policies}
                   for scenario in config.scenarios}
    by_key = {(e.scenario, e.seed, e.policy): e for e in episodes}
    paired = {}
    for baseline in config.policies[1:]:
        differences = [by_key[(scenario, seed, "voi")].utility -
                       by_key[(scenario, seed, baseline)].utility
                       for scenario in config.scenarios for seed in seeds]
        paired[baseline] = {"n": len(differences), "mean_utility_difference":
                            float(np.mean(differences)),
                            "ci95": paired_bootstrap(differences, config.bootstrap_seed,
                                                     config.bootstrap_resamples)}
    ablation_rows = {}
    if ablations:
        for ablation in ABLATIONS:
            rows = [_run_one(config, scenario, seed, "voi", ablation)
                    for scenario in config.scenarios for seed in seeds]
            ablation_rows[ablation] = summarize(rows)
    return {"schema_version": "benchmark-result-1", "config_version": config.version,
            "config_sha256": config_hash, "policy_version": POLICY_VERSION,
            "code_revision": "unversioned-workspace", "source_sha256": source_sha256(),
            "noise_mode": config.noise_mode,
            "split": split, "seeds": list(seeds), "scenarios": list(config.scenarios),
            "policies": list(config.policies), "sample_size": len(episodes),
            "bootstrap": {"seed": config.bootstrap_seed,
                          "resamples": config.bootstrap_resamples,
                          "method": "paired episode bootstrap, percentile 2.5/97.5"},
            "runtime": {"python": platform.python_version(), "cpu": platform.processor(),
                        "latency_scope": "whole mission wall time, exploratory"},
            "summary": by_policy, "by_scenario": by_scenario, "paired": paired,
            "ablations": ablation_rows,
            "episodes": [asdict(e) for e in episodes],
            "real_data": official_product_status(),
            "caveats": ["synthetic truth and utility only", "small exploratory sample",
                        "unknown/fault identifiability limited",
                        "real APXS schema check is not model validation"]}


def main() -> None:
    parser = argparse.ArgumentParser(description="AURORA synthetic paired benchmark")
    parser.add_argument("--config", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--split", choices=("development", "heldout"), default="heldout")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--no-ablations", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config, digest = load_config(args.config)
    result = run_benchmark(config, digest, args.split, args.limit, not args.no_ablations)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf8")
    csv_path = args.output.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("policy", "scenario", "n", "claims",
                                                  "correct_claims", "false_discovery_proportion",
                                                  "discovery_recall", "mean_utility", "mean_regret"))
        writer.writeheader()
        for scenario, policy_rows in result["by_scenario"].items():
            for policy, row in policy_rows.items():
                writer.writerow({"policy": policy, "scenario": scenario, "n": row["n"],
                                 "claims": row["denominators"]["claims"],
                                 "correct_claims": row["denominators"]["correct_claims"],
                                 "false_discovery_proportion": row["false_discovery_proportion"],
                                 "discovery_recall": row["discovery_recall"],
                                 "mean_utility": row["mean_utility"],
                                 "mean_regret": row["mean_regret"]})
    print(f"Wrote {result['sample_size']} paired-policy episode rows to {args.output}")


if __name__ == "__main__":
    main()
