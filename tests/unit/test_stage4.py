from dataclasses import replace

import numpy as np
import pytest

from aurora.inference import STATES, default_prior, predictive_bins
from aurora.planning import (
    ACTION_BY_NAME,
    ACTIONS,
    VisibleState,
    action_value,
    best_terminal,
    calibrate_belief,
    choose,
    feasible,
    geology_probabilities,
    initial_state,
    terminal_utility,
)
from aurora.simulator import Condition, Geology, Observation


def test_s4_u01_action_contracts():
    assert len({a.name for a in ACTIONS}) == len(ACTIONS)
    assert all(a.energy_wh >= 0 and a.time_h >= 0 and a.communication >= 0 for a in ACTIONS)
    assert all(a.terminal == (not a.instruments) for a in ACTIONS)


def test_s4_u02_feasibility():
    state = initial_state(0, 0, 1)
    assert not feasible(ACTION_BY_NAME["measure_spectrometer"], state)
    assert feasible(ACTION_BY_NAME["abstain"], state)
    assert not feasible(ACTION_BY_NAME["escalate"], state)
    assert not feasible(ACTION_BY_NAME["cross_check"], initial_state())


def test_s4_u03_terminal_utility():
    prior = np.zeros(len(STATES))
    for i, s in enumerate(STATES):
        if s == (Geology.BASALT, Condition.HEALTHY, Condition.HEALTHY):
            prior[i] = 0.75
        if s == (Geology.CLAY, Condition.HEALTHY, Condition.HEALTHY):
            prior[i] = 0.25
    np.testing.assert_allclose(terminal_utility("conclude_basalt", prior), 2.5)
    assert terminal_utility("abstain", prior) == 0


def test_s4_u04_one_step_voi_toy():
    prior = np.zeros(len(STATES))
    for i, s in enumerate(STATES):
        if s in ((Geology.BASALT, Condition.HEALTHY, Condition.HEALTHY),
                 (Geology.SULFATE, Condition.HEALTHY, Condition.HEALTHY)):
            prior[i] = 0.5
    state = replace(initial_state(), belief=prior)
    # A single spectrometer reading almost perfectly separates the two means.
    value = action_value(ACTION_BY_NAME["measure_spectrometer"], state)
    np.testing.assert_allclose(value, 9.595709396406352, atol=1e-10)
    assert value > best_terminal(state)[1]


def test_s4_u05_predictive_sums():
    state = initial_state()
    np.testing.assert_allclose(predictive_bins(state.belief, "imager", 1.5).sum(), 1)


def test_s4_u06_cost_once():
    prior = np.zeros(len(STATES))
    prior[0] = 1
    state = replace(initial_state(), belief=prior)
    np.testing.assert_allclose(action_value(ACTION_BY_NAME["measure_spectrometer"], state), 9.6)
    np.testing.assert_allclose(action_value(ACTION_BY_NAME["calibrate_spectrometer"], state), 9.2)


def test_s4_u07_zero_budget():
    choice = choose(initial_state(0, 0))
    assert ACTION_BY_NAME[choice.action].terminal


def test_s4_u08_horizon():
    choice = choose(initial_state(12, 12, 0))
    assert ACTION_BY_NAME[choice.action].terminal


def test_s4_u09_tie_break():
    state = initial_state(0, 0, communication=0)
    assert choose(state).action == "abstain"
    assert "tie break" in choose(state).reason


def test_s4_u10_calibration_transition():
    belief = default_prior()
    calibrated = calibrate_belief(belief, "spectrometer")
    assert all(calibrated[i] == 0 for i, s in enumerate(STATES)
               if s[1] != Condition.HEALTHY)
    np.testing.assert_allclose(geology_probabilities(calibrated)["basalt"], 0.3)
    assert ACTION_BY_NAME["calibrate_spectrometer"].energy_wh == 4


def test_s4_u11_cross_check_independence():
    history = (Observation(1, 1, "spectrometer", 1, "index", 2, 1),)
    state = replace(initial_state(), history=history)
    assert feasible(ACTION_BY_NAME["cross_check"], state)
    assert ACTION_BY_NAME["cross_check"].instruments == ("imager",)


def test_s4_u12_unknown_abstention():
    belief = np.zeros(len(STATES))
    belief[27:] = 1 / (len(STATES) - 27)
    state = replace(initial_state(0, 0), belief=belief)
    assert best_terminal(state)[0] == "abstain"


def test_s4_u13_fixed_model_budget():
    state = initial_state(0, 0)
    choice = choose(state, "fixed_model")
    assert ACTION_BY_NAME[choice.action].terminal


def test_s4_u14_baseline_criteria():
    state = initial_state()
    assert choose(state, "information_gain").action in ACTION_BY_NAME
    confident = np.zeros(len(STATES))
    confident[0] = 1
    assert choose(replace(state, belief=confident), "threshold").action == "conclude_basalt"


def test_s4_u15_no_oracle_contract():
    assert "truth" not in VisibleState.__dataclass_fields__
    assert "truth" not in choose.__annotations__
    assert "oracle" not in ACTION_BY_NAME


def test_invalid_policy_and_state():
    with pytest.raises(ValueError):
        choose(initial_state(), "oracle")
    with pytest.raises(ValueError):
        initial_state(-1)
    with pytest.raises(ValueError):
        initial_state(float("nan"))
