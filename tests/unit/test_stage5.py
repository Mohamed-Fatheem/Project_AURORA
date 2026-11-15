from dataclasses import replace
from datetime import datetime

import numpy as np
import pytest

from aurora.benchmark import ABLATIONS, load_config, run_benchmark
from aurora.evaluation import (
    brier,
    calibration_bins,
    confusion,
    latency_stats,
    paired_bootstrap,
    precision_recall_f1,
    rate,
    score_episode,
    summarize,
)
from aurora.mission import run_mission
from aurora.planning import VisibleState, choose, initial_state
from aurora.real_data import PDSRecord
from aurora.simulator import scenarios


def sample_episode(**changes):
    config = scenarios()["ordinary"]
    mission, truth = run_mission(config, 42, "threshold", noise_mode="keyed")
    return replace(score_episode(mission, truth, config), **changes)


def test_s5_u01_false_discovery_denominator():
    good = sample_episode(claimed=True, correct=True)
    bad = sample_episode(claimed=True, correct=False)
    assert summarize([good, bad])["false_discovery_proportion"] == 0.5


def test_s5_u02_discovery_recall_and_miss():
    rows = [sample_episode(truth_geology="sulfate", correct=True,
                           terminal="conclude_sulfate"),
            sample_episode(truth_geology="other", correct=False, terminal="abstain",
                           claimed=False)]
    assert summarize(rows)["discovery_recall"] == 0.5
    assert summarize(rows)["miss_rate"] == 0.5


def test_s5_u03_fault_confusion():
    counts = confusion([True, True, False, False], [True, False, True, False])
    assert counts == {"tp": 1, "fp": 1, "tn": 1, "fn": 1}
    assert precision_recall_f1(counts) == {"precision": 0.5, "recall": 0.5, "f1": 0.5}


def test_s5_u04_unknown_confusion():
    rows = [sample_episode(unknown_truth=True, unknown_predicted=True),
            sample_episode(unknown_truth=False, unknown_predicted=True),
            sample_episode(unknown_truth=True, unknown_predicted=False)]
    assert summarize(rows)["unknown"]["tp"] == 1
    assert summarize(rows)["unknown"]["fp"] == 1
    assert summarize(rows)["unknown"]["fn"] == 1


def test_s5_u05_undefined_rates():
    assert rate(0, 0) == "N/A"
    assert precision_recall_f1(confusion([False], [False])) == {
        "precision": "N/A", "recall": "N/A", "f1": "N/A"}
    assert precision_recall_f1(confusion([True], [False]))["precision"] == "N/A"


def test_s5_u06_abstention_coverage_accuracy():
    rows = [sample_episode(claimed=True, correct=True, abstained=False),
            sample_episode(claimed=False, correct=False, abstained=True)]
    summary = summarize(rows)
    assert summary["abstention_fraction"] == 0.5
    assert summary["coverage"] == summary["decision_accuracy"] == 0.5
    assert summary["selective_accuracy"] == 1


def test_s5_u07_resource_per_correct():
    rows = [sample_episode(correct=True, claimed=True, energy_used_wh=2, time_used_h=1),
            sample_episode(correct=False, claimed=False, energy_used_wh=8, time_used_h=7)]
    assert summarize(rows)["energy_wh_per_correct"] == 2
    assert summarize(rows)["time_h_per_correct"] == 1
    assert summarize(rows[1:])["energy_wh_per_correct"] == "N/A"


def test_s5_u08_oracle_regret():
    episode = sample_episode()
    np.testing.assert_allclose(episode.regret, episode.oracle_utility - episode.utility)
    assert episode.oracle_utility == 10


def test_s5_u09_brier_and_bins():
    assert brier([0, 0.5, 1], [False, True, True]) == pytest.approx(1 / 12)
    bins = calibration_bins([0.1, 0.9], [False, True], 2)
    assert bins[0]["event_fraction"] == 0 and bins[1]["event_fraction"] == 1


def test_s5_u10_latency_stats():
    stats = latency_stats([1, 2, 3, 4])
    assert stats["median_s"] == 2.5
    assert stats["p95_s"] == pytest.approx(3.85)


def test_s5_u11_bootstrap_repeatability():
    a = paired_bootstrap([1, 2, 3], seed=7, resamples=100)
    assert a == paired_bootstrap([1, 2, 3], seed=7, resamples=100)
    assert a[0] <= 2 <= a[1]


def test_s5_u12_seed_partition_rejection():
    config, _ = load_config()
    with pytest.raises(ValueError):
        replace(config, heldout_seeds=(config.development_seeds[0],))


def test_s5_u13_no_policy_truth_access():
    assert "truth" not in VisibleState.__dataclass_fields__
    assert "truth" not in choose.__annotations__
    config, _ = load_config()
    assert "oracle" not in config.policies


def test_s5_u14_ablations():
    assert set(ABLATIONS) == {"no_fault", "no_adequacy", "info_gain", "no_cost"}
    for ablation in ABLATIONS:
        assert choose(initial_state(0, 0), ablation=ablation).action in (
            "abstain", "conclude_basalt", "conclude_clay", "conclude_sulfate")


def test_s5_u15_real_adapter_validation():
    record = PDSRecord("urn:nasa:pds:example", "https://pds-geosciences.wustl.edu/example",
                       "APXS", "2020-01-01T00:00:00Z", 5.0, "wt_pct", True, "good")
    assert record.unit == "wt_pct" and datetime.fromisoformat(record.timestamp_utc)
    for change in ({"unit": "index"}, {"quality_flag": ""}, {"timestamp_utc": "bad"},
                   {"source_url": "https://example.com/x"}, {"value": -1},
                   {"calibrated": "yes"}):
        with pytest.raises(ValueError):
            replace(record, **change)


def test_s5_u16_result_provenance():
    config, digest = load_config()
    result = run_benchmark(replace(config, scenarios=("ordinary",)), digest,
                           "development", 1, False)
    assert result["sample_size"] == 4
    assert result["config_sha256"] == digest and result["bootstrap"]["seed"] == 2026
    assert result["summary"]["voi"]["n"] == 1 and result["caveats"]
    assert len(result["source_sha256"]) == 64
    assert result["summary"]["voi"]["denominators"]["episodes"] == 1
