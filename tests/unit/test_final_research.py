import json

import numpy as np
import pytest

from aurora.final_benchmark import MANIFEST, jobs, load_manifest
from aurora.final_policies import LegacyBelief, Settings, expected, make_belief, select
from aurora.final_statistics import binary_metrics, bootstrap_indices, rate_record, wilson
from aurora.research_model import STATES, Belief, Evidence


def test_final_reference_identifies_initial_not_repaired_fault():
    belief = LegacyBelief()
    belief.update(Evidence("spectrometer", "reference", 1, 1.5))
    initial = belief.initial_fault("spectrometer")
    belief.calibrate("spectrometer")
    assert belief.initial_fault("spectrometer") == initial
    assert belief.active_fault("spectrometer") == 0


def test_final_fixed_model_never_predicts_fault_bug002():
    belief = LegacyBelief(fixed=True)
    belief.update(Evidence("spectrometer", "reference", 1, 2.))
    assert belief.any_fault() == 0


def test_final_likelihoods_normalized():
    belief = LegacyBelief()
    for instrument in ("spectrometer", "imager"):
        for kind in ("science", "reference"):
            values = belief.likelihoods(instrument, kind, 2)
            assert np.all(values >= 0)
            np.testing.assert_allclose(values.sum(axis=1), 1, atol=1e-12)


def test_final_matched_verification_and_zero_budget():
    for policy in ("improved_voi", "original_voi", "information_gain", "fixed_model", "threshold"):
        settings = Settings(policy=policy)
        belief = make_belief(1, settings)
        assert select(belief, 0, 0, 0, 0, settings)[0] == "abstain"
        belief.update(Evidence("spectrometer", "science", 1, 1.))
        action, values = select(belief, 10, 10, 3, 1, settings)
        assert action == "abstain" or action.endswith("imager")
        assert "basalt" not in values


def test_final_continuous_expected_matches_step1():
    belief = Belief()
    np.testing.assert_allclose(expected(belief, "imager", "science", 1.5),
                               belief.expected_terminal("imager", "science", 1.5))


def test_final_controlled_prior_ablations():
    no_fault = make_belief(1, Settings(ablation="no_fault"))
    assert no_fault.weights[(STATES[:, 1:] != 0).any(axis=1)].sum() == 0
    no_unknown = make_belief(1, Settings(ablation="no_unknown"))
    assert no_unknown.weights[STATES[:, 0] == 3].sum() == 0
    changed = make_belief(1, Settings(fault_healthy_prior=.95))
    np.testing.assert_allclose(changed.initial_fault("spectrometer"), .05)
    assert changed.noise_scale == 1


@pytest.mark.parametrize("changes", [{"policy": "oracle"}, {"nodes": 0}, {"unknown_prior": 0},
                                      {"fault_healthy_prior": 1}, {"wrong_reward": 0},
                                      {"assumed_noise": float("nan")}])
def test_final_invalid_settings(changes):
    with pytest.raises(ValueError):
        Settings(**changes)


def test_final_untouched_generalization_partition():
    config, digest = load_manifest()
    development = list(jobs(config, "development", 1))
    final = list(jobs(config, "final", 1))
    assert len(development) == 14 * 5 and len(final) == 20 * 5
    assert not any(name.startswith("unseen_") for name, *_ in development)
    assert len(digest) == 64


def test_final_manifest_rejects_leakage(tmp_path):
    config = json.loads(MANIFEST.read_text())
    config["final_seeds"][0] = config["development_seeds"][0]
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="leakage"):
        load_manifest(path)


def test_final_zero_errors_have_nonzero_confidence_bound():
    assert wilson(0, 50)[1] > .05
    assert rate_record(0, 0)["value"] == "N/A"
    np.testing.assert_allclose(wilson(25, 50)[0], 1 - wilson(25, 50)[1])


def test_final_stratified_episode_bootstrap():
    rows = [{"case": "a"}, {"case": "a"}, {"case": "b"}]
    indices = bootstrap_indices(rows, seed=1, resamples=20)
    assert indices.shape == (20, 3)
    assert np.all(indices[:, :2] < 2) and np.all(indices[:, 2] == 2)
    metrics = binary_metrics([True, False, True], [True, False, False], indices)
    assert metrics["tp"] == 1 and metrics["fn"] == 1
    assert metrics["recall"]["value"] == .5
