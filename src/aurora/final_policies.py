"""Matched-contract research policies; original core is imported, never edited."""

import math
from dataclasses import dataclass

import numpy as np

from aurora.inference import EDGES, bin_index, bin_probabilities, default_prior
from aurora.inference import STATES as OLD_STATES
from aurora.research_mission import ACTION_COSTS
from aurora.research_model import INSTRUMENTS, STATES, Belief
from aurora.simulator import NOISE, SUPPORTED, Condition

POLICIES = ("improved_voi", "original_voi", "information_gain", "fixed_model", "threshold")
ABLATIONS = ("no_reference", "no_fault", "no_unknown", "no_verification", "no_cost", "information_gain")


class LegacyBelief:
    """Stage 3 bins and priors, adapted to the shared reference/repair interface.

    Initial identities survive repair to avoid repeating the timing error.
    No continuous-model or expanded fault support is added to this comparator.
    """

    def __init__(self, noise_scale=1., fixed=False):
        self.weights = default_prior()
        if fixed:
            mask = np.array([a == b == Condition.HEALTHY for _, a, b in OLD_STATES])
            self.weights *= mask
            self.weights /= self.weights.sum()
        self.noise_scale = noise_scale
        self.repaired = [False, False]
        self.history = []

    def copy(self):
        other = LegacyBelief(self.noise_scale)
        other.weights = self.weights.copy()
        other.repaired = self.repaired.copy()
        other.history = self.history.copy()
        return other

    def likelihoods(self, instrument, kind, time_h):
        axis = INSTRUMENTS.index(instrument)
        output = []
        for state in OLD_STATES:
            modified = list(state)
            if self.repaired[axis]:
                modified[axis + 1] = Condition.HEALTHY
            if kind == "science":
                probabilities = bin_probabilities(tuple(modified), instrument, time_h, self.noise_scale)
            else:
                condition = modified[axis + 1]
                mean = 1.2 if condition == Condition.BIAS else .5 * time_h if condition == Condition.DRIFT else 0.
                sigma = NOISE[instrument] * self.noise_scale
                boundaries = [0., *(.5 * (1 + math.erf((edge - mean) / (sigma * math.sqrt(2))))
                                      for edge in EDGES[1:-1]), 1.]
                probabilities = np.diff(boundaries)
            output.append(probabilities)
        return np.array(output)

    def update(self, evidence):
        likelihood = self.likelihoods(evidence.instrument, evidence.kind, evidence.time_h)[:, bin_index(evidence.value)]
        posterior = self.weights * likelihood
        if posterior.sum() <= 0:
            raise ValueError("zero legacy predictive evidence")
        self.weights = posterior / posterior.sum()
        self.history.append(evidence)

    def calibrate(self, instrument):
        self.repaired[INSTRUMENTS.index(instrument)] = True

    def geology(self):
        return np.array([sum(self.weights[i] for i, s in enumerate(OLD_STATES) if s[0].value == label)
                         for label in ("basalt", "clay", "sulfate", "other")])

    def initial_fault(self, instrument):
        axis = INSTRUMENTS.index(instrument) + 1
        return float(sum(self.weights[i] for i, s in enumerate(OLD_STATES) if s[axis] != Condition.HEALTHY))

    def active_fault(self, instrument):
        return 0. if self.repaired[INSTRUMENTS.index(instrument)] else self.initial_fault(instrument)

    def any_fault(self):
        return float(sum(self.weights[i] for i, s in enumerate(OLD_STATES)
                         if s[1] != Condition.HEALTHY or s[2] != Condition.HEALTHY))

    def expected(self, instrument, kind, time_h, wrong=-20., information=False):
        joint = self.weights[:, None] * self.likelihoods(instrument, kind, time_h)
        predictive = joint.sum(axis=0)
        posteriors = np.divide(joint, predictive[None, :], out=np.zeros_like(joint), where=predictive[None, :] > 0)
        if information:
            return entropy(self.weights) - float(predictive @ np.array([entropy(p) for p in posteriors.T]))
        geology = np.stack([posteriors[np.array([s[0].value == name for s in OLD_STATES])].sum(axis=0)
                            for name in ("basalt", "clay", "sulfate")], axis=1)
        return float(predictive @ np.maximum(0, ((10 - wrong) * geology + wrong).max(axis=1)))


def entropy(weights):
    values = np.asarray(weights)
    values = values[values > 0]
    return -float(np.sum(values * np.log(values)))


def terminal(belief, wrong=-20.):
    values = (10 - wrong) * belief.geology()[:3] + wrong
    index = int(np.argmax(values))
    return (SUPPORTED[index].value, float(values[index])) if values[index] > 0 else ("abstain", 0.)


def expected(belief, instrument, kind, time_h, wrong=-20., nodes=7, information=False):
    if isinstance(belief, LegacyBelief):
        return belief.expected(instrument, kind, time_h, wrong, information)
    means, variances = belief.parameters(instrument, kind, time_h)
    x, w = np.polynomial.hermite.hermgauss(nodes)
    samples = (means[:, None] + np.sqrt(2 * variances[:, None]) * x).ravel()
    probabilities = (belief.weights[:, None] * w / np.sqrt(np.pi)).ravel()
    posteriors, _ = belief.posterior_samples(samples, instrument, kind, time_h)
    if information:
        terms = np.zeros_like(posteriors)
        positive = posteriors > 0
        terms[positive] = posteriors[positive] * np.log(posteriors[positive])
        return entropy(belief.weights) + float(probabilities @ terms.sum(axis=1))
    geology = np.stack([posteriors[:, STATES[:, 0] == i].sum(axis=1) for i in range(3)], axis=1)
    return float(probabilities @ np.maximum(0., ((10 - wrong) * geology + wrong).max(axis=1)))


@dataclass(frozen=True)
class Settings:
    policy: str = "improved_voi"
    ablation: str = "none"
    unknown_prior: float = .1
    fault_healthy_prior: float = .8
    assumed_noise: float | None = None
    wrong_reward: float = -20.
    nodes: int = 7

    def __post_init__(self):
        if (self.policy not in POLICIES or self.ablation not in ("none", *ABLATIONS)
                or not 0 < self.unknown_prior < 1 or not 0 < self.fault_healthy_prior < 1 or not math.isfinite(self.wrong_reward)
                or self.wrong_reward >= 0 or self.nodes not in (7, 15)
                or (self.assumed_noise is not None and (not math.isfinite(self.assumed_noise) or self.assumed_noise <= 0))):
            raise ValueError("invalid frozen policy settings")


def make_belief(noise, settings):
    noise = settings.assumed_noise if settings.assumed_noise is not None else noise
    if settings.policy != "improved_voi":
        return LegacyBelief(noise, settings.policy == "fixed_model")
    belief = Belief(noise, settings.unknown_prior)
    for axis in (1, 2):
        belief.weights *= np.where(STATES[:, axis] == 0, settings.fault_healthy_prior / .8,
                                    (1 - settings.fault_healthy_prior) / .2)
    if settings.ablation == "no_fault":
        belief.weights *= (STATES[:, 1:] == 0).all(axis=1)
    if settings.ablation == "no_unknown":
        belief.weights *= STATES[:, 0] != 3
    belief.weights /= belief.weights.sum()
    return belief


def select(belief, energy, time, steps, elapsed, settings):
    decision, value = terminal(belief, settings.wrong_reward)
    measured = {e.instrument for e in belief.history if e.kind == "science"}
    missing = set(INSTRUMENTS) - measured
    verify = settings.ablation != "no_verification"
    if missing and verify:
        decision, value = "abstain", 0.
    values = {decision: value}
    if steps > 0:
        for action, (e_cost, t_cost) in ACTION_COSTS.items():
            instrument = "spectrometer" if action.endswith("spectrometer") else "imager"
            if e_cost > energy or t_cost > time or (verify and measured and missing and instrument not in missing):
                continue
            predicted = belief.copy()
            if action.startswith("calibrate"):
                predicted.calibrate(instrument)
            kind = "reference" if action.startswith("check") else "science"
            information = settings.policy == "information_gain" or settings.ablation == "information_gain"
            raw = expected(predicted, instrument, kind, elapsed + t_cost,
                           settings.wrong_reward, settings.nodes, information)
            values[action] = raw if information else raw - (
                0. if settings.ablation == "no_cost" else .15 * e_cost + .1 * t_cost)
    if settings.policy == "threshold":
        # Same legacy 0.85 threshold, shared verification and feasibility fallback.
        if not missing and max(belief.geology()[:3]) >= .85:
            return decision, values
        candidates = [a for a in values if a in ACTION_COSTS and not a.startswith("check")]
        preferred = "measure_imager" if measured and "imager" in missing else "measure_spectrometer"
        return (preferred if preferred in candidates else candidates[0] if candidates else decision), values
    return max(values, key=values.get), values
