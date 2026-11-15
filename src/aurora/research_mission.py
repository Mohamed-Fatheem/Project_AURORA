"""Versioned Step 1 mission; private world is excluded from policy inputs."""

import math
from dataclasses import dataclass, replace

import numpy as np

from aurora.research_model import INSTRUMENTS, STATES, Belief, Evidence
from aurora.simulator import MEANS, NOISE, Condition, Scenario, scenarios

# Calibration cost already includes one hour of reference work and one science reading.
ACTION_COSTS = {"measure_spectrometer": (2., 1.), "measure_imager": (1., 1.5),
                "check_spectrometer": (1., 1.), "check_imager": (1., 1.),
                "calibrate_spectrometer": (4., 2.)}


@dataclass(frozen=True)
class Case:
    config: Scenario
    private_means: tuple[float, float] | None = None

    def __post_init__(self):
        if self.private_means is not None and (len(self.private_means) != 2 or
                not all(math.isfinite(x) for x in self.private_means)):
            raise ValueError("invalid private generating means")


def development_cases():
    cases = {name: Case(config) for name, config in scenarios().items()}
    ordinary = scenarios()["ordinary"]
    outside = scenarios()["outside"]
    cases.update({
        "unknown_overlap": Case(replace(outside, name="unknown_overlap"), (1.4, 3.5)),
        "unknown_boundary": Case(replace(outside, name="unknown_boundary"), (3.25, 2.0)),
        "unknown_alias": Case(replace(outside, name="unknown_alias"), (1., 4.)),
        "unknown_fault": Case(replace(outside, name="unknown_fault", bias=1.2,
                                       conditions=scenarios()["bias"].conditions), (2.8, 3.8)),
        "high_noise": Case(replace(ordinary, name="high_noise", noise_scale=2.)),
        "weak_bias": Case(replace(scenarios()["bias"], name="weak_bias", bias=0.3)),
        "negative_bias": Case(replace(scenarios()["bias"], name="negative_bias", bias=-0.8)),
        "both_faults": Case(replace(scenarios()["bias"], name="both_faults",
                                     conditions={n: Condition.BIAS for n in INSTRUMENTS})),
    })
    return cases


def select_action(belief: Belief, energy: float, time: float, steps_left: int,
                  elapsed: float, available: frozenset[str] = frozenset(INSTRUMENTS)):
    if (not all(math.isfinite(x) and x >= 0 for x in (energy, time, elapsed)) or
            not isinstance(steps_left, int) or steps_left < 0 or
            not available <= frozenset(INSTRUMENTS)):
        raise ValueError("invalid planning resources")
    terminal, utility = belief.terminal()
    measured = {e.instrument for e in belief.history if e.kind == "science"}
    missing = set(INSTRUMENTS) - measured
    if missing:
        terminal, utility = "abstain", 0.
    values = {terminal: utility}
    if steps_left:
        for name, (e_cost, t_cost) in ACTION_COSTS.items():
            instrument = "spectrometer" if name.endswith("spectrometer") else "imager"
            # A supported geology claim requires independent cross-instrument evidence.
            if measured and missing and instrument not in missing:
                continue
            if e_cost > energy or t_cost > time or instrument not in available:
                continue
            predicted = belief.copy()
            if name.startswith("calibrate"):
                predicted.calibrate(instrument)
            kind = "reference" if name.startswith("check") else "science"
            values[name] = (predicted.expected_terminal(instrument, kind, elapsed + t_cost)
                            - 0.15 * e_cost - 0.10 * t_cost)
    # Terminal first breaks nonpositive VOI ties safely; utilities are unchanged.
    return max(values, key=values.get), values


@dataclass(frozen=True)
class AuditEvent:
    action: str
    evidence: tuple[Evidence, ...]
    initial_fault: tuple[float, float]
    active_fault: tuple[float, float]
    initial_any_fault: float
    geology: tuple[float, ...]
    energy_wh: float
    time_h: float
    values: dict[str, float]


@dataclass(frozen=True)
class AuditMission:
    version: str
    events: tuple[AuditEvent, ...]
    terminal: str
    energy_wh: float
    time_h: float


def run_audit(case: Case, seed: int, unknown_prior: float = 0.1,
              assumed_noise_scale: float | None = None):
    if not isinstance(seed, int) or not 0 <= seed < 2**64:
        raise ValueError("invalid seed")
    world = case.config
    belief = Belief(world.noise_scale if assumed_noise_scale is None else assumed_noise_scale,
                    unknown_prior)
    energy, time, elapsed = world.energy_wh, world.time_h, 0.
    counts = {}
    events = []
    repaired = set()
    terminal = "abstain"

    def generate(instrument, kind, timestamp):
        # Separate keyed science/reference streams. Policies never see these parameters.
        key = (instrument, kind)
        counts[key] = counts.get(key, 0) + 1
        rng = np.random.default_rng(np.random.SeedSequence(
            [seed, INSTRUMENTS.index(instrument), counts[key], int(kind == "reference")]))
        condition = Condition.HEALTHY if instrument in repaired else world.conditions[instrument]
        offset = (world.bias if condition == Condition.BIAS else
                  world.drift_per_hour * timestamp if condition == Condition.DRIFT else 0.)
        mean = (case.private_means[INSTRUMENTS.index(instrument)] if case.private_means else
                MEANS[instrument][world.geology]) if kind == "science" else 0.
        return Evidence(instrument, kind, timestamp,
                        float(rng.normal(mean + offset, NOISE[instrument] * world.noise_scale)))

    for step in range(world.horizon + 1):
        action, values = select_action(belief, energy, time, world.horizon - step, elapsed)
        if action not in ACTION_COSTS:
            terminal = action
            break
        instrument = "spectrometer" if action.endswith("spectrometer") else "imager"
        e_cost, t_cost = ACTION_COSTS[action]
        readings = []
        if action.startswith("calibrate"):
            # Audit BEFORE reset. Initial latent identity remains in the posterior.
            reference = generate(instrument, "reference", elapsed + 1.)
            readings.append(reference)
            belief.update(reference)
            repaired.add(instrument)
            belief.calibrate(instrument)
        kind = "reference" if action.startswith("check") else "science"
        reading = generate(instrument, kind, elapsed + t_cost)
        readings.append(reading)
        belief.update(reading)
        energy -= e_cost
        time -= t_cost
        elapsed += t_cost
        events.append(AuditEvent(action, tuple(readings),
                                tuple(belief.initial_fault(n) for n in INSTRUMENTS),
                                tuple(belief.active_fault(n) for n in INSTRUMENTS),
                                float(belief.weights[(STATES[:, 1:] != 0).any(axis=1)].sum()),
                                tuple(float(x) for x in belief.geology()), energy, time, values))
    return AuditMission("audit-mission-1", tuple(events), terminal, energy, time)


def replay(events: tuple[AuditEvent, ...], noise_scale: float = 1.):
    belief = Belief(noise_scale)
    for event in events:
        for index, reading in enumerate(event.evidence):
            belief.update(reading)
            if event.action.startswith("calibrate") and index == 0:
                belief.calibrate(reading.instrument)
    return belief
