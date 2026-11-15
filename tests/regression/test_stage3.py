import dataclasses

import numpy as np

from aurora.inference import STATES, bayes_update, infer_trace
from aurora.simulator import Geology, PrivateTruth, run, scenarios


def test_s3_r01_analytic_fixture():
    prior = np.zeros(len(STATES))
    prior[:2] = [0.5, 0.5]
    likelihood = np.zeros(len(STATES))
    likelihood[:2] = [0.8, 0.2]
    np.testing.assert_allclose(bayes_update(prior, likelihood)[:2], [0.8, 0.2])


def test_s3_r02_healthy_fault_trajectory():
    ordinary, _ = run(scenarios()["ordinary"], 42)
    bias, _ = run(scenarios()["bias"], 42)
    a = infer_trace(ordinary)
    b = infer_trace(bias)
    assert len(a) == len(b) == 5
    np.testing.assert_allclose([s.geology["basalt"] for s in a],
                               [0.857138, 0.967057, 0.990351, 0.997222, 0.999204], atol=1e-6)
    np.testing.assert_allclose([s.spectrometer_fault_probability for s in b],
                               [0.154790, 0.359135, 0.337343, 0.288080, 0.657510], atol=1e-6)
    assert [s.observed_bin for s in a] != [s.observed_bin for s in b]


def test_s3_r03_outside_adequacy():
    trace, _ = run(scenarios()["outside"], 42, ("spectrometer", "imager") * 2)
    assert any(s.adequacy_warning for s in infer_trace(trace))


def test_s3_r04_private_metadata_invariance():
    trace, truth = run(scenarios()["ordinary"], 42)
    changed = dataclasses.replace(truth, geology=Geology.SULFATE)
    assert isinstance(changed, PrivateTruth)
    assert infer_trace(trace) == infer_trace(trace)
