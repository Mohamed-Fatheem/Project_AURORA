import dataclasses

import numpy as np
import pytest

from aurora.inference import (
    STATES,
    bayes_update,
    bin_probabilities,
    default_prior,
    infer,
    infer_trace,
    log_bayes_update,
    predictive_bins,
    validate_prior,
)
from aurora.simulator import Condition, Geology, Observation, run, scenarios


def test_s3_u01_prior_validation():
    assert np.isclose(default_prior().sum(), 1)
    for bad in (np.zeros(len(STATES)), np.full(len(STATES), -1.0),
                np.full(len(STATES), np.nan), np.ones(2)):
        with pytest.raises(ValueError):
            validate_prior(bad)


def test_s3_u02_likelihood_normalization():
    for state in STATES:
        for instrument in ("spectrometer", "imager"):
            probabilities = bin_probabilities(state, instrument, 2)
            assert np.all(probabilities >= 0) and np.all(np.isfinite(probabilities))
            np.testing.assert_allclose(probabilities.sum(), 1, atol=1e-14)


def test_s3_u03_hand_bayes():
    prior = np.zeros(len(STATES))
    prior[:2] = [0.5, 0.5]
    likelihood = np.zeros(len(STATES))
    likelihood[:2] = [0.8, 0.2]
    np.testing.assert_allclose(bayes_update(prior, likelihood)[:2], [0.8, 0.2])


def test_s3_u04_sequential_batch_equivalent():
    prior = default_prior()
    a = np.linspace(0.1, 0.9, len(STATES))
    b = np.linspace(0.9, 0.1, len(STATES))
    np.testing.assert_allclose(bayes_update(bayes_update(prior, a), b),
                               bayes_update(prior, a * b))


def test_s3_u05_normalized_posterior():
    trace, _ = run(scenarios()["ordinary"], 42)
    for step in infer_trace(trace):
        np.testing.assert_allclose(sum(step.geology.values()), 1, atol=1e-12)
        assert all(np.isfinite(list(step.geology.values())))


def test_s3_u06_zero_likelihood():
    with pytest.raises(ValueError):
        bayes_update(default_prior(), np.zeros(len(STATES)))


def test_s3_u07_log_stability():
    log_likelihood = np.full(len(STATES), -10000.0)
    log_likelihood[0] = -9990.0
    posterior = log_bayes_update(default_prior(), log_likelihood)
    assert posterior[0] > default_prior()[0]
    np.testing.assert_allclose(posterior.sum(), 1)


def test_s3_u08_healthy_evidence():
    trace, _ = run(scenarios()["ordinary"], 42, ("spectrometer", "imager") * 2)
    final = infer_trace(trace)[-1]
    assert final.geology["basalt"] > final.geology["clay"]


def test_s3_u09_fault_evidence():
    evidence = (Observation(1, 1, "imager", 4.0, "index", 1, 1.5),
                Observation(2, 2, "spectrometer", 2.2, "index", 2, 1),
                Observation(3, 3, "spectrometer", 2.2, "index", 2, 1))
    steps = infer(evidence)
    assert steps[-1].spectrometer_fault_probability > steps[0].spectrometer_fault_probability


def test_s3_u10_conflict_uncertainty():
    trace, _ = run(scenarios()["conflict"], 42, ("spectrometer", "imager"))
    final = infer_trace(trace)[-1]
    assert max(final.geology.values()) < 0.999999


def test_s3_u11_unknown_warning_and_false_alarm_control():
    strange = (Observation(1, 1, "spectrometer", 9, "index", 2, 1),)
    normal = (Observation(1, 1, "spectrometer", 1, "index", 2, 1),)
    assert infer(strange)[0].adequacy_warning
    assert not infer(normal)[0].adequacy_warning


def test_s3_u12_predictive_normalization():
    probs = predictive_bins(default_prior(), "imager", 1)
    assert np.all(probs >= 0)
    np.testing.assert_allclose(probs.sum(), 1, atol=1e-12)


def test_s3_u13_provenance_and_boundary():
    trace, _ = run(scenarios()["ordinary"], 42)
    step = infer_trace(trace)[0]
    assert (step.step, step.time_h, step.instrument) == (1, 1, "spectrometer")
    assert 0 <= step.unknown_probability <= 1 and step.caution
    assert "truth" not in dataclasses.asdict(step)
    assert "truth" not in infer.__annotations__


def test_invalid_likelihood_model_inputs():
    with pytest.raises(ValueError):
        bin_probabilities(STATES[0], "invalid", 1)
    with pytest.raises(ValueError):
        bin_probabilities(STATES[0], "imager", 1, 0)
    with pytest.raises(ValueError):
        bin_probabilities((Geology.BASALT, Condition.HEALTHY), "imager", 1)
