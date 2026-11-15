from dataclasses import replace

import numpy as np

from aurora.benchmark import load_config, run_benchmark
from aurora.dashboard.service import benchmark_rows
from aurora.evaluation import confusion, paired_bootstrap, precision_recall_f1, score_episode
from aurora.mission import run_mission
from aurora.real_data import PDSRecord
from aurora.simulator import scenarios


def test_s5_r01_confusion_fixture():
    counts = confusion([True, True, False, False], [True, False, True, False])
    assert precision_recall_f1(counts) == {"precision": 0.5, "recall": 0.5, "f1": 0.5}


def test_s5_r02_small_benchmark_fixture():
    config, digest = load_config()
    config = replace(config, scenarios=("ordinary",))
    result = run_benchmark(config, digest, "development", 1, False)
    assert result["sample_size"] == 4
    assert result["summary"]["voi"]["n"] == 1
    assert result["episodes"][0]["scenario"] == "ordinary"
    np.testing.assert_allclose([e["utility"] for e in result["episodes"]],
                               [8.8, 8.9, 9.2, 9.6], atol=1e-12)


def test_s5_r03_paired_ci_fixture():
    interval = paired_bootstrap([1, 2, 3], seed=7, resamples=100)
    np.testing.assert_allclose(interval, [4 / 3, 3], atol=1e-12)


def test_s5_r04_adapter_roundtrip():
    record = PDSRecord("urn:nasa:pds:example", "https://pds-geosciences.wustl.edu/example",
                       "APXS", "2020-01-01T00:00:00Z", 5.0, "wt_pct", True, "good")
    data = record.to_dict()
    assert data.pop("simulator_truth_labels") is None
    assert PDSRecord(**data) == record


def test_s5_r05_dashboard_uses_result_data():
    first = {"schema_version": "benchmark-result-1", "policies": ["voi"],
             "summary": {"voi": {"n": 2, "mean_utility": 1.5,
                                  "false_discovery_proportion": 0.5,
                                  "discovery_recall": 0.25}}}
    assert benchmark_rows(first)[0]["mean_utility"] == 1.5
    first["summary"]["voi"]["mean_utility"] = -2
    assert benchmark_rows(first)[0]["mean_utility"] == -2


def test_bug_002_fixed_model_fault_scoring():
    world = scenarios()["bias"]
    mission, truth = run_mission(world, 42, "fixed_model", noise_mode="keyed")
    episode = score_episode(mission, truth, world)
    assert episode.fault_truth
    assert not episode.fault_predicted
