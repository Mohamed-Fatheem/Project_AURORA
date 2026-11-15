"""Discrete joint belief over synthetic geology and two instrument conditions.

Continuous index observations are binned before inference. Known-state bin
probabilities integrate the Stage 1 Gaussian law; an explicit broad unknown
component assigns uniform mass to each bin. No simulator truth enters this API.
"""

import math
from dataclasses import dataclass
from itertools import product

import numpy as np

from aurora.simulator import MEANS, NOISE, SUPPORTED, AgentTrace, Condition, Geology, Observation

MODEL_VERSION = "joint-binned-1"
EDGES = (-math.inf, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, math.inf)
GEOLOGIES = (*SUPPORTED, Geology.OTHER)
CONDITIONS = tuple(Condition)
STATES = tuple(product(GEOLOGIES, CONDITIONS, CONDITIONS))
BIAS_INDEX = 1.2
DRIFT_INDEX_PER_H = 0.5
UNKNOWN_BIN_PROB = 1.0 / (len(EDGES) - 1)


def validate_prior(prior: np.ndarray) -> np.ndarray:
    values = np.asarray(prior, dtype=float)
    if (values.ndim != 1 or len(values) != len(STATES) or
            not np.all(np.isfinite(values)) or np.any(values < 0) or
            not np.isclose(values.sum(), 1.0, atol=1e-10)):
        raise ValueError("prior must be a finite nonnegative vector summing to one")
    return values.copy()


def default_prior() -> np.ndarray:
    geology = {Geology.BASALT: 0.30, Geology.CLAY: 0.30,
               Geology.SULFATE: 0.30, Geology.OTHER: 0.10}
    condition = {Condition.HEALTHY: 0.8, Condition.BIAS: 0.1, Condition.DRIFT: 0.1}
    return validate_prior(np.array([geology[g] * condition[a] * condition[b]
                                    for g, a, b in STATES]))


def bin_index(value: float) -> int:
    if not math.isfinite(value):
        raise ValueError("observation must be finite")
    return int(np.searchsorted(EDGES[1:-1], value, side="right"))


def _cdf(value: float, mean: float, sigma: float) -> float:
    return 0.5 * (1 + math.erf((value - mean) / (sigma * math.sqrt(2))))


def bin_probabilities(state: tuple, instrument: str, time_h: float,
                      noise_scale: float = 1.0) -> np.ndarray:
    if instrument not in MEANS or not math.isfinite(time_h) or time_h < 0:
        raise ValueError("invalid instrument or time")
    if not math.isfinite(noise_scale) or noise_scale <= 0:
        raise ValueError("noise scale must be positive for inference")
    if state not in STATES:
        raise ValueError("unsupported joint state")
    geology, spectrometer_condition, imager_condition = state
    if geology == Geology.OTHER:
        return np.full(len(EDGES) - 1, UNKNOWN_BIN_PROB)
    condition = spectrometer_condition if instrument == "spectrometer" else imager_condition
    offset = (BIAS_INDEX if condition == Condition.BIAS else
              DRIFT_INDEX_PER_H * time_h if condition == Condition.DRIFT else 0.0)
    mean = MEANS[instrument][geology] + offset
    sigma = NOISE[instrument] * noise_scale
    boundaries = np.array([0.0, *(_cdf(edge, mean, sigma) for edge in EDGES[1:-1]), 1.0])
    return np.diff(boundaries)


def log_bayes_update(prior: np.ndarray, log_likelihood: np.ndarray) -> np.ndarray:
    prior = validate_prior(prior)
    logs = np.asarray(log_likelihood, dtype=float)
    if logs.shape != prior.shape or np.any(np.isnan(logs)) or np.any(np.isposinf(logs)):
        raise ValueError("invalid log likelihood")
    with np.errstate(divide="ignore"):
        scores = np.log(prior) + logs
    maximum = np.max(scores)
    if not np.isfinite(maximum):
        raise ValueError("all likelihoods are zero under the prior")
    weights = np.exp(scores - maximum)
    return weights / weights.sum()


def bayes_update(prior: np.ndarray, likelihood: np.ndarray) -> np.ndarray:
    values = np.asarray(likelihood, dtype=float)
    if values.shape != (len(STATES),) or not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError("likelihood must be finite and nonnegative")
    with np.errstate(divide="ignore"):
        return log_bayes_update(prior, np.log(values))


def predictive_bins(prior: np.ndarray, instrument: str, time_h: float,
                    noise_scale: float = 1.0) -> np.ndarray:
    prior = validate_prior(prior)
    probabilities = np.stack([bin_probabilities(s, instrument, time_h, noise_scale)
                              for s in STATES])
    return prior @ probabilities


@dataclass(frozen=True)
class BeliefStep:
    step: int
    time_h: float
    instrument: str
    observed_bin: int
    predictive_probability: float
    geology: dict[str, float]
    spectrometer_fault_probability: float
    imager_fault_probability: float
    unknown_probability: float
    adequacy_warning: bool
    caution: str


def infer(observations: tuple[Observation, ...], noise_scale: float = 1.0,
          prior: np.ndarray | None = None) -> tuple[BeliefStep, ...]:
    """Sequential agent-only inference; warnings are diagnostics, not truth labels."""
    belief = default_prior() if prior is None else validate_prior(prior)
    result = []
    for observation in observations:
        index = bin_index(observation.value)
        predictive = predictive_bins(belief, observation.instrument, observation.time_h,
                                     noise_scale)
        likelihood = np.array([bin_probabilities(state, observation.instrument,
                                                  observation.time_h, noise_scale)[index]
                               for state in STATES])
        belief = bayes_update(belief, likelihood)
        geology = {g.value: float(sum(belief[i] for i, s in enumerate(STATES) if s[0] == g))
                   for g in GEOLOGIES}
        spectrometer_fault = float(sum(belief[i] for i, s in enumerate(STATES)
                                        if s[1] != Condition.HEALTHY))
        imager_fault = float(sum(belief[i] for i, s in enumerate(STATES)
                                  if s[2] != Condition.HEALTHY))
        unknown = geology[Geology.OTHER.value]
        # Low prior-predictive mass is an adequacy warning, not proof of unknown truth.
        warning = predictive[index] < 0.05 or unknown > 0.5
        result.append(BeliefStep(observation.step, observation.time_h,
                                 observation.instrument, index, float(predictive[index]),
                                 geology, spectrometer_fault, imager_fault, unknown,
                                 warning, "Ambiguous synthetic evidence; unknown and faults can overlap."))
    return tuple(result)


def infer_trace(trace: AgentTrace) -> tuple[BeliefStep, ...]:
    return infer(trace.observations, float(trace.public_config["noise_scale"]))
