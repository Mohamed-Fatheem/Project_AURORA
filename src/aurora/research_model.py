"""Continuous synthetic inference v1; initial fault identity survives interventions.

Unknown geology has persistent independent N(3, 2**2) sensor means integrated
analytically. Fault types/magnitudes are discrete nuisance variables, not truth.
"""

import math
from dataclasses import dataclass
from itertools import product

import numpy as np

from aurora.simulator import MEANS, NOISE, SUPPORTED

VERSION = "continuous-audit-1"
INSTRUMENTS = ("spectrometer", "imager")
# (constant index offset, slope index/hour); healthy then symmetric alternatives.
FAULTS = ((0., 0.), (-0.6, 0.), (0.6, 0.), (-1.5, 0.), (1.5, 0.),
          (0., -0.5), (0., 0.5))
STATES = np.array(list(product(range(4), range(7), range(7))), dtype=int)
OFFSETS = np.array(FAULTS)


@dataclass(frozen=True)
class Evidence:
    instrument: str
    kind: str
    time_h: float
    value: float

    def __post_init__(self):
        if (self.instrument not in INSTRUMENTS or self.kind not in ("science", "reference")
                or not math.isfinite(self.time_h) or self.time_h < 0
                or not math.isfinite(self.value)):
            raise ValueError("invalid evidence provenance or finite value")


class Belief:
    def __init__(self, noise_scale: float = 1.0, unknown_prior: float = 0.1):
        if not math.isfinite(noise_scale) or noise_scale <= 0 or not 0 < unknown_prior < 1:
            raise ValueError("positive finite noise and interior unknown prior required")
        self.noise_scale = noise_scale
        fault_prior = np.array([0.8, .0375, .0375, .0375, .0375, .025, .025])
        geological_prior = np.array([(1 - unknown_prior) / 3] * 3 + [unknown_prior])
        self.weights = geological_prior[STATES[:, 0]] * fault_prior[STATES[:, 1]] * fault_prior[STATES[:, 2]]
        self.means = np.array([[MEANS[name][SUPPORTED[g]] if g < 3 else 3.
                                for name in INSTRUMENTS] for g in STATES[:, 0]])
        self.variances = np.repeat(np.where(STATES[:, 0] == 3, 4., 0.)[:, None], 2, axis=1)
        self.repaired = [False, False]
        self.history: list[Evidence] = []
        self.log_predictive: list[float] = []

    def copy(self):
        other = Belief(self.noise_scale)
        other.weights = self.weights.copy()
        other.means = self.means.copy()
        other.variances = self.variances.copy()
        other.repaired = self.repaired.copy()
        other.history = self.history.copy()
        other.log_predictive = self.log_predictive.copy()
        return other

    def parameters(self, instrument: str, kind: str, time_h: float):
        Evidence(instrument, kind, time_h, 0.)
        axis = INSTRUMENTS.index(instrument)
        faults = OFFSETS[STATES[:, axis + 1]]
        offsets = np.zeros(len(STATES)) if self.repaired[axis] else faults[:, 0] + time_h * faults[:, 1]
        means = offsets + (self.means[:, axis] if kind == "science" else 0.)
        variance = (NOISE[instrument] * self.noise_scale) ** 2
        variances = variance + (self.variances[:, axis] if kind == "science"
                                else np.zeros(len(STATES)))
        return means, variances

    def posterior_samples(self, values, instrument, kind, time_h):
        means, variances = self.parameters(instrument, kind, time_h)
        values = np.asarray(values, dtype=float)
        if not np.all(np.isfinite(values)):
            raise ValueError("nonfinite sample")
        with np.errstate(divide="ignore"):
            logs = np.log(self.weights)[None, :] - 0.5 * (
                np.log(2 * np.pi * variances)[None, :] +
                (values[:, None] - means[None, :]) ** 2 / variances[None, :])
        maximum = logs.max(axis=1)
        if not np.all(np.isfinite(maximum)):
            raise ValueError("numerically unsupported evidence")
        scaled = np.exp(logs - maximum[:, None])
        normalizer = scaled.sum(axis=1)
        return scaled / normalizer[:, None], maximum + np.log(normalizer)

    def update(self, evidence: Evidence):
        posterior, log_probability = self.posterior_samples(
            [evidence.value], evidence.instrument, evidence.kind, evidence.time_h)
        if evidence.kind == "science":
            axis = INSTRUMENTS.index(evidence.instrument)
            means, variances = self.parameters(evidence.instrument, evidence.kind, evidence.time_h)
            gain = self.variances[:, axis] / variances
            self.means[:, axis] += gain * (evidence.value - means)
            self.variances[:, axis] *= 1 - gain
        self.weights = posterior[0]
        self.history.append(evidence)
        self.log_predictive.append(float(log_probability[0]))

    def calibrate(self, instrument: str):
        if instrument not in INSTRUMENTS:
            raise ValueError("unknown instrument")
        self.repaired[INSTRUMENTS.index(instrument)] = True

    def geology(self):
        return np.bincount(STATES[:, 0], weights=self.weights, minlength=4)

    def initial_fault(self, instrument: str):
        axis = INSTRUMENTS.index(instrument)
        return float(self.weights[STATES[:, axis + 1] != 0].sum())

    def active_fault(self, instrument: str):
        return 0. if self.repaired[INSTRUMENTS.index(instrument)] else self.initial_fault(instrument)

    def terminal(self):
        probabilities = self.geology()
        values = 30 * probabilities[:3] - 20  # Original +10 / -20 utility.
        index = int(np.argmax(values))
        return (SUPPORTED[index].value, float(values[index])) if values[index] > 0 else ("abstain", 0.)

    def expected_terminal(self, instrument: str, kind: str, time_h: float, nodes: int = 7):
        """Gauss-Hermite quadrature of continuous predictive mixture (approximate VOI)."""
        means, variances = self.parameters(instrument, kind, time_h)
        x, w = np.polynomial.hermite.hermgauss(nodes)
        samples = (means[:, None] + np.sqrt(2 * variances[:, None]) * x).ravel()
        probabilities = (self.weights[:, None] * w[None, :] / np.sqrt(np.pi)).ravel()
        posteriors, _ = self.posterior_samples(samples, instrument, kind, time_h)
        geology = np.stack([posteriors[:, STATES[:, 0] == i].sum(axis=1) for i in range(3)], axis=1)
        values = np.maximum(0., (30 * geology - 20).max(axis=1))
        return float(probabilities @ values)
