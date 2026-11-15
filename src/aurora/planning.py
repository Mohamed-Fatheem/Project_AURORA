"""Stage 4 small exact one-step decision model; no simulator truth in policies."""

import math
from dataclasses import dataclass

import numpy as np

from aurora.inference import (
    STATES,
    bayes_update,
    bin_index,
    bin_probabilities,
    default_prior,
    predictive_bins,
    validate_prior,
)
from aurora.simulator import COST, Condition, Geology, Observation

VERSION = "voi-1"
ENERGY_PENALTY = 0.15  # utility / Wh
TIME_PENALTY = 0.10  # utility / h
CORRECT_REWARD = 10.0
WRONG_REWARD = -20.0


@dataclass(frozen=True)
class Action:
    name: str
    instruments: tuple[str, ...]
    energy_wh: float
    time_h: float
    communication: int = 0
    terminal: bool = False
    calibrates: str | None = None
    requires_crosscheck: bool = False


ACTIONS = (
    Action("measure_spectrometer", ("spectrometer",), *COST["spectrometer"]),
    Action("measure_imager", ("imager",), *COST["imager"]),
    Action("cross_check", ("imager",), *COST["imager"], requires_crosscheck=True),
    Action("calibrate_spectrometer", ("spectrometer",), 4.0, 2.0,
           calibrates="spectrometer"),
    Action("discriminate", ("spectrometer", "imager"), 3.0, 2.5),
    Action("conclude_basalt", (), 0, 0, terminal=True),
    Action("conclude_clay", (), 0, 0, terminal=True),
    Action("conclude_sulfate", (), 0, 0, terminal=True),
    Action("abstain", (), 0, 0, terminal=True),
    Action("escalate", (), 0, 0, communication=1, terminal=True),
)
ACTION_BY_NAME = {a.name: a for a in ACTIONS}


@dataclass(frozen=True)
class VisibleState:
    belief: np.ndarray
    energy_wh: float
    time_h: float
    communication: int
    steps_left: int
    elapsed_h: float
    history: tuple[Observation, ...] = ()
    available: frozenset[str] = frozenset(COST)
    noise_scale: float = 1.0

    def __post_init__(self) -> None:
        validate_prior(self.belief)
        values = (self.energy_wh, self.time_h, self.elapsed_h, self.noise_scale)
        if (not all(math.isfinite(x) for x in values) or
                min(self.energy_wh, self.time_h, self.communication,
                    self.steps_left, self.elapsed_h) < 0 or self.noise_scale <= 0 or
                not isinstance(self.steps_left, int) or not isinstance(self.communication, int)
                or not self.available <= frozenset(COST)):
            raise ValueError("invalid resources or noise")


def feasible(action: Action, state: VisibleState) -> bool:
    if action.energy_wh > state.energy_wh or action.time_h > state.time_h or (
        action.communication > state.communication
    ):
        return False
    if action.terminal:
        return True
    if state.steps_left < len(action.instruments) or not set(action.instruments) <= state.available:
        return False
    return not (action.requires_crosscheck and not any(
        o.instrument == "spectrometer" for o in state.history
    ))


def geology_probabilities(belief: np.ndarray) -> dict[str, float]:
    belief = validate_prior(belief)
    return {g.value: float(sum(belief[i] for i, s in enumerate(STATES) if s[0] == g))
            for g in Geology}


def terminal_utility(name: str, belief: np.ndarray, communication: int = 0) -> float:
    geology = geology_probabilities(belief)
    if name == "abstain":
        return 0.0
    if name == "escalate":
        return 1.0 if communication > 0 else -np.inf
    if name.startswith("conclude_") and name[9:] in geology:
        probability = geology[name[9:]]
        return CORRECT_REWARD * probability + WRONG_REWARD * (1 - probability)
    raise ValueError("unknown terminal decision")


def best_terminal(state: VisibleState) -> tuple[str, float]:
    choices = [(a.name, terminal_utility(a.name, state.belief, state.communication))
               for a in ACTIONS if a.terminal and feasible(a, state)]
    return max(choices, key=lambda item: item[1])


def calibrate_belief(belief: np.ndarray, instrument: str) -> np.ndarray:
    if instrument not in COST:
        raise ValueError("unknown calibration instrument")
    axis = 1 if instrument == "spectrometer" else 2
    result = np.zeros(len(STATES))
    index_by_state = {state: i for i, state in enumerate(STATES)}
    for i, state in enumerate(STATES):
        target = list(state)
        target[axis] = Condition.HEALTHY
        result[index_by_state[tuple(target)]] += belief[i]
    return validate_prior(result)


def _posterior_for_bin(belief: np.ndarray, instrument: str, time_h: float,
                       index: int, noise_scale: float) -> np.ndarray:
    likelihood = np.array([bin_probabilities(s, instrument, time_h, noise_scale)[index]
                           for s in STATES])
    return bayes_update(belief, likelihood)


def _outcomes(action: Action, state: VisibleState):
    belief = state.belief
    if action.calibrates:
        belief = calibrate_belief(belief, action.calibrates)
    outcomes = [(1.0, belief)]
    elapsed = state.elapsed_h + action.time_h - sum(COST[name][1]
                                                    for name in action.instruments)
    for instrument in action.instruments:
        elapsed += COST[instrument][1]
        next_outcomes = []
        for path_probability, path_belief in outcomes:
            probabilities = predictive_bins(path_belief, instrument, elapsed, state.noise_scale)
            for index, probability in enumerate(probabilities):
                if probability > 0:
                    updated = _posterior_for_bin(path_belief, instrument, elapsed,
                                                 index, state.noise_scale)
                    next_outcomes.append((path_probability * float(probability), updated))
        outcomes = next_outcomes
    return outcomes


def action_value(action: Action, state: VisibleState, cost_penalty: bool = True) -> float:
    if not feasible(action, state):
        return -np.inf
    if action.terminal:
        return terminal_utility(action.name, state.belief, state.communication)
    continuation = 0.0
    for probability, belief in _outcomes(action, state):
        next_state = VisibleState(belief, state.energy_wh - action.energy_wh,
                                  state.time_h - action.time_h, state.communication,
                                  state.steps_left - len(action.instruments),
                                  state.elapsed_h + action.time_h, state.history,
                                  state.available, state.noise_scale)
        continuation += probability * best_terminal(next_state)[1]
    return continuation - (ENERGY_PENALTY * action.energy_wh + TIME_PENALTY * action.time_h
                           if cost_penalty else 0.0)


@dataclass(frozen=True)
class Choice:
    action: str
    value: float
    values: dict[str, float]
    reason: str


def choose(state: VisibleState, policy: str = "voi", ablation: str = "none") -> Choice:
    if policy not in ("voi", "fixed_model", "information_gain", "threshold"):
        raise ValueError("unknown policy")
    if ablation not in ("none", "no_fault", "no_adequacy", "info_gain", "no_cost"):
        raise ValueError("unknown ablation")
    if ablation == "no_fault":
        policy = "fixed_model"
    if ablation == "info_gain":
        policy = "information_gain"
    if policy == "threshold":
        geology = geology_probabilities(state.belief)
        strongest = max((g for g in geology if g != "other"), key=geology.get)
        proposed = "conclude_" + strongest if geology[strongest] >= 0.85 else "measure_spectrometer"
        if not feasible(ACTION_BY_NAME[proposed], state):
            proposed = best_terminal(state)[0]
        return Choice(proposed, action_value(ACTION_BY_NAME[proposed], state), {},
                      "Threshold rule; terminal fallback when observation is infeasible.")
    planning_state = state
    if ablation == "no_adequacy":
        belief = state.belief.copy()
        for i, s in enumerate(STATES):
            if s[0] == Geology.OTHER:
                belief[i] = 0
        if belief.sum() == 0:
            belief = default_prior()
            belief[[i for i, s in enumerate(STATES) if s[0] == Geology.OTHER]] = 0
        belief /= belief.sum()
        planning_state = VisibleState(belief, state.energy_wh, state.time_h,
                                      state.communication, state.steps_left, state.elapsed_h,
                                      state.history, state.available, state.noise_scale)
    if policy == "fixed_model":
        belief = np.zeros(len(STATES))
        geology = geology_probabilities(state.belief)
        for i, s in enumerate(STATES):
            if s[1] == Condition.HEALTHY and s[2] == Condition.HEALTHY:
                belief[i] = geology[s[0].value]
        planning_state = VisibleState(belief, state.energy_wh, state.time_h,
                                      state.communication, state.steps_left, state.elapsed_h,
                                      state.history, state.available, state.noise_scale)
    values = {a.name: action_value(a, planning_state, ablation != "no_cost")
              for a in ACTIONS if feasible(a, state)}
    if policy == "information_gain":
        base = state.belief
        entropy = lambda p: -float(np.sum(p[p > 0] * np.log(p[p > 0])))
        for action in ACTIONS:
            if action.name in values and not action.terminal:
                values[action.name] = entropy(base) - sum(p * entropy(b)
                                                          for p, b in _outcomes(action, state))
    winner = max(values, key=values.get)  # ACTIONS order is stable tie-break.
    return Choice(winner, float(values[winner]), values,
                  f"{policy} ranking; exact binned outcomes; stable listed-order tie break.")


def update_observation(belief: np.ndarray, observation: Observation,
                       noise_scale: float = 1.0) -> np.ndarray:
    return _posterior_for_bin(belief, observation.instrument, observation.time_h,
                              bin_index(observation.value), noise_scale)


def initial_state(energy_wh: float = 12.0, time_h: float = 12.0,
                  steps: int = 5, communication: int = 0,
                  noise_scale: float = 1.0) -> VisibleState:
    return VisibleState(default_prior(), energy_wh, time_h, communication,
                        steps, 0.0, (), frozenset(COST), noise_scale)
