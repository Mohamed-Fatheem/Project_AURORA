from dataclasses import replace

import numpy as np
import pytest

from aurora.research_diagnostics import diagnostic_summary
from aurora.research_mission import Case, development_cases, run_audit, select_action
from aurora.research_model import Belief, Evidence


@pytest.mark.parametrize("noise,prior", [(0, .1), (float("nan"), .1), (1, 0), (1, 1)])
def test_research_invalid_model(noise, prior):
    with pytest.raises(ValueError):
        Belief(noise, prior)


def test_research_prior_and_healthy_reference():
    belief = Belief()
    np.testing.assert_allclose(belief.weights.sum(), 1)
    np.testing.assert_allclose(belief.initial_fault("spectrometer"), .2)
    belief.update(Evidence("spectrometer", "reference", 1, 0))
    assert belief.initial_fault("spectrometer") < .2


def test_research_reference_separates_geology_and_fault():
    belief = Belief()
    original = belief.geology()
    belief.update(Evidence("spectrometer", "reference", 1, 1.5))
    assert belief.initial_fault("spectrometer") > .9
    np.testing.assert_allclose(belief.geology(), original, atol=1e-12)


def test_bug_003_initial_fault_not_erased_by_calibration():
    belief = Belief()
    belief.update(Evidence("spectrometer", "reference", 1, 1.5))
    before = belief.initial_fault("spectrometer")
    belief.calibrate("spectrometer")
    assert belief.initial_fault("spectrometer") == before
    assert belief.active_fault("spectrometer") == 0
    belief.update(Evidence("spectrometer", "science", 2, 1.))
    assert belief.initial_fault("spectrometer") > .9


def test_research_unknown_persistent_mean_not_iid_flat_tail():
    belief = Belief()
    belief.update(Evidence("spectrometer", "science", 1, 6))
    belief.update(Evidence("imager", "science", 2, 6))
    assert belief.geology()[3] > .9
    assert belief.terminal()[0] == "abstain"
    assert np.all(belief.variances >= 0)


def test_research_extreme_log_stability():
    belief = Belief()
    belief.update(Evidence("spectrometer", "science", 1, 100.))
    assert np.all(np.isfinite(belief.weights))
    np.testing.assert_allclose(belief.weights.sum(), 1)


def test_research_sequential_reference_order_invariance():
    a, b = Belief(), Belief()
    readings = [Evidence("spectrometer", "reference", 1, .8),
                Evidence("imager", "reference", 2, -.2)]
    for reading in readings:
        a.update(reading)
    for reading in reversed(readings):
        b.update(reading)
    np.testing.assert_allclose(a.weights, b.weights, atol=1e-12)


def test_research_drift_reference_time_effect():
    early, late = Belief(), Belief()
    early.update(Evidence("spectrometer", "reference", 1, .5))
    late.update(Evidence("spectrometer", "reference", 4, 2.))
    assert late.initial_fault("spectrometer") > early.initial_fault("spectrometer")


def test_research_quadrature_bound_and_resolution():
    belief = Belief()
    a = belief.expected_terminal("spectrometer", "science", 1, 7)
    b = belief.expected_terminal("spectrometer", "science", 1, 15)
    assert 0 <= a <= 10 and abs(a - b) < 1


def test_research_invalid_evidence():
    for args in (("x", "science", 1, 1), ("imager", "x", 1, 1),
                 ("imager", "science", -1, 1), ("imager", "science", 1, float("nan"))):
        with pytest.raises(ValueError):
            Evidence(*args)


def test_research_terminal_verification_and_budget():
    belief = Belief()
    assert select_action(belief, 0, 0, 0, 0)[0] == "abstain"
    assert select_action(belief, 12, 12, 5, 0, frozenset())[0] == "abstain"
    with pytest.raises(ValueError):
        select_action(belief, -1, 0, 0, 0)


def test_research_discovery_denominator():
    rows = [{"truth": "sulfate", "initial_fault_truth": False,
             "initial_fault_predicted": False, "unknown_truth": False,
             "unknown_predicted": False, "claimed": True, "correct": True, "utility": 10},
            {"truth": "other", "initial_fault_truth": False,
             "initial_fault_predicted": False, "unknown_truth": True,
             "unknown_predicted": True, "claimed": False, "correct": False, "utility": 0}]
    assert diagnostic_summary(rows)["supported_sulfate_recall"] == 1


def test_research_world_input_validation():
    case = development_cases()["ordinary"]
    with pytest.raises(ValueError):
        Case(case.config, (float("nan"), 1))
    with pytest.raises(ValueError):
        run_audit(case, -1)
    empty = run_audit(Case(replace(case.config, energy_wh=0)), 200)
    assert empty.terminal == "abstain" and not empty.events
