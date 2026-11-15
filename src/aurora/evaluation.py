"""Offline metrics. Only this module consumes simulator evaluation truth."""

import math
from dataclasses import dataclass

import numpy as np

from aurora.inference import STATES, default_prior
from aurora.mission import Mission
from aurora.planning import (
    ENERGY_PENALTY,
    TIME_PENALTY,
    calibrate_belief,
    geology_probabilities,
    update_observation,
)
from aurora.simulator import Condition, Geology, PrivateTruth, Scenario


def rate(numerator: int, denominator: int) -> float | str:
    if numerator < 0 or denominator < 0 or numerator > denominator:
        raise ValueError("invalid rate counts")
    return "N/A" if denominator == 0 else numerator / denominator


def confusion(truth: list[bool], prediction: list[bool]) -> dict[str, int]:
    if len(truth) != len(prediction):
        raise ValueError("truth and prediction lengths differ")
    return {"tp": sum(t and p for t, p in zip(truth, prediction)),
            "fp": sum(not t and p for t, p in zip(truth, prediction)),
            "tn": sum(not t and not p for t, p in zip(truth, prediction)),
            "fn": sum(t and not p for t, p in zip(truth, prediction))}


def precision_recall_f1(counts: dict[str, int]) -> dict[str, float | str]:
    tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
    precision = rate(tp, tp + fp)
    recall = rate(tp, tp + fn)
    f1 = ("N/A" if isinstance(precision, str) or isinstance(recall, str) else
          0.0 if precision + recall == 0 else
          2 * precision * recall / (precision + recall))
    return {"precision": precision, "recall": recall, "f1": f1}


def brier(probabilities: list[float], truth: list[bool]) -> float | str:
    if len(probabilities) != len(truth) or any(
        not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities
    ):
        raise ValueError("invalid Brier inputs")
    return "N/A" if not truth else float(np.mean((np.array(probabilities) - truth) ** 2))


def calibration_bins(probabilities: list[float], truth: list[bool], bins: int = 5) -> list[dict]:
    if bins <= 0 or len(probabilities) != len(truth) or any(
        not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities
    ):
        raise ValueError("invalid calibration inputs")
    output = []
    for index in range(bins):
        members = [(p, y) for p, y in zip(probabilities, truth)
                   if min(int(p * bins), bins - 1) == index]
        output.append({"bin": index, "count": len(members),
                       "mean_probability": (sum(p for p, _ in members) / len(members)
                                            if members else "N/A"),
                       "event_fraction": (sum(y for _, y in members) / len(members)
                                          if members else "N/A")})
    return output


def latency_stats(seconds: list[float]) -> dict[str, float | str]:
    if any(not math.isfinite(x) or x < 0 for x in seconds):
        raise ValueError("invalid latency")
    return {"median_s": float(np.median(seconds)) if seconds else "N/A",
            "p95_s": float(np.percentile(seconds, 95)) if seconds else "N/A"}


def paired_bootstrap(differences: list[float], seed: int = 2026,
                     resamples: int = 1000) -> tuple[float, float] | str:
    if not differences or resamples <= 0 or any(not math.isfinite(x) for x in differences):
        return "N/A"
    rng = np.random.default_rng(seed)
    data = np.asarray(differences)
    draws = rng.integers(0, len(data), size=(resamples, len(data)))
    means = data[draws].mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def final_belief(mission: Mission, noise_scale: float = 1.0) -> np.ndarray:
    belief = default_prior()
    for event in mission.events:
        if event.action == "calibrate_spectrometer":
            belief = calibrate_belief(belief, "spectrometer")
        for observation in event.observations:
            belief = update_observation(belief, observation, noise_scale)
    return belief


def policy_scoring_belief(mission: Mission, noise_scale: float = 1.0) -> np.ndarray:
    """Apply each policy's declared reliability/adequacy assumptions offline."""
    belief = final_belief(mission, noise_scale)
    if mission.policy == "fixed_model" or mission.ablation == "no_fault":
        geology = geology_probabilities(belief)
        projected = np.zeros(len(STATES))
        for i, state in enumerate(STATES):
            if state[1] == Condition.HEALTHY and state[2] == Condition.HEALTHY:
                projected[i] = geology[state[0].value]
        belief = projected
    if mission.ablation == "no_adequacy":
        belief = belief.copy()
        for i, state in enumerate(STATES):
            if state[0] == Geology.OTHER:
                belief[i] = 0
        if belief.sum() == 0:
            belief = default_prior()
            belief[[i for i, state in enumerate(STATES) if state[0] == Geology.OTHER]] = 0
        belief /= belief.sum()
    return belief


@dataclass(frozen=True)
class Episode:
    scenario: str
    seed: int
    policy: str
    terminal: str
    truth_geology: str
    correct: bool
    claimed: bool
    abstained: bool
    fault_truth: bool
    fault_predicted: bool
    unknown_truth: bool
    unknown_probability: float
    unknown_predicted: bool
    energy_used_wh: float
    time_used_h: float
    utility: float
    oracle_utility: float
    regret: float
    latency_s: float
    within_budget: bool


def score_episode(mission: Mission, truth: PrivateTruth, config: Scenario,
                  latency_s: float = 0.0) -> Episode:
    """Privileged offline scoring; policy has already terminated."""
    terminal = mission.stop_reason
    claimed = terminal.startswith("conclude_")
    correct = claimed and terminal[9:] == truth.geology.value
    reward = 10.0 if correct else -20.0 if claimed else 1.0 if terminal == "escalate" else 0.0
    energy = config.energy_wh - mission.final_energy_wh
    time = config.time_h - mission.final_time_h
    utility = reward - ENERGY_PENALTY * energy - TIME_PENALTY * time
    oracle = 10.0 if truth.geology != Geology.OTHER else 0.0
    belief = policy_scoring_belief(mission, config.noise_scale)
    geology = geology_probabilities(belief)
    fault_probability = float(sum(belief[i] for i, state in enumerate(STATES)
                                  if state[1] != Condition.HEALTHY or
                                  state[2] != Condition.HEALTHY))
    fault_truth = any(condition != Condition.HEALTHY for condition in truth.conditions.values())
    unknown_truth = truth.geology == Geology.OTHER
    return Episode(config.name, mission.seed, mission.policy, terminal, truth.geology.value,
                   correct, claimed, terminal == "abstain", fault_truth,
                   fault_probability >= 0.5, unknown_truth, geology["other"],
                   geology["other"] >= 0.5, energy, time, utility, oracle,
                   oracle - utility, latency_s,
                   0 <= mission.final_energy_wh <= config.energy_wh and
                   0 <= mission.final_time_h <= config.time_h)


def summarize(episodes: list[Episode]) -> dict:
    n = len(episodes)
    claims = [e for e in episodes if e.claimed]
    correct = [e for e in claims if e.correct]
    positives = [e for e in episodes if e.truth_geology in ("sulfate", "other")]
    discoveries = [e for e in episodes if e.correct and e.terminal == "conclude_sulfate"]
    fault_counts = confusion([e.fault_truth for e in episodes],
                             [e.fault_predicted for e in episodes])
    unknown_counts = confusion([e.unknown_truth for e in episodes],
                               [e.unknown_predicted for e in episodes])
    negatives = [e for e in episodes if e.truth_geology in ("basalt", "clay")]
    false_claims = len(claims) - len(correct)
    return {"n": n, "false_discovery_proportion": rate(len(claims) - len(correct), len(claims)),
            "denominators": {"episodes": n, "claims": len(claims), "correct_claims": len(correct),
                             "false_claims": false_claims, "positive_truth": len(positives),
                             "negative_truth": len(negatives),
                             "false_claims_on_negative": sum(e.claimed and not e.correct
                                                              for e in negatives)},
            "false_positive_episode_rate": rate(sum(e.claimed and not e.correct for e in negatives),
                                                len(negatives)),
            "discovery_recall": rate(len(discoveries), len(positives)),
            "miss_rate": rate(len(positives) - len(discoveries), len(positives)),
            "abstention_fraction": rate(sum(e.abstained for e in episodes), n),
            "decision_accuracy": rate(len(correct), n),
            "coverage": rate(len(claims), n),
            "selective_accuracy": rate(len(correct), len(claims)),
            "fault": {**fault_counts, **precision_recall_f1(fault_counts)},
            "unknown": {**unknown_counts, **precision_recall_f1(unknown_counts)},
            "unknown_brier": brier([e.unknown_probability for e in episodes],
                                   [e.unknown_truth for e in episodes]),
            "unknown_calibration": calibration_bins([e.unknown_probability for e in episodes],
                                                     [e.unknown_truth for e in episodes]),
            "energy_wh_per_correct": (sum(e.energy_used_wh for e in correct) / len(correct)
                                      if correct else "N/A"),
            "time_h_per_correct": (sum(e.time_used_h for e in correct) / len(correct)
                                   if correct else "N/A"),
            "mean_utility": float(np.mean([e.utility for e in episodes])) if n else "N/A",
            "mean_regret": float(np.mean([e.regret for e in episodes])) if n else "N/A",
            "within_budget_fraction": rate(sum(e.within_budget for e in episodes), n),
            "latency": latency_stats([e.latency_s for e in episodes])}
