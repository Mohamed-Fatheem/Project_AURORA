"""Frozen matched-contract missions and out-of-development scenario catalog."""

import hashlib
import time
from dataclasses import asdict, replace

import numpy as np

from aurora.final_policies import LegacyBelief, Settings, make_belief, select
from aurora.research_mission import ACTION_COSTS, Case, development_cases
from aurora.research_model import INSTRUMENTS, STATES, Evidence
from aurora.simulator import MEANS, NOISE, Condition, Geology


def case_catalog():
    cases = development_cases()
    healthy = cases["ordinary"].config
    outside = cases["outside"].config
    bias = cases["bias"].config
    cases.update({
        "unseen_unknown_mixed": Case(replace(outside, name="unseen_unknown_mixed"), (4.3, 3.3)),
        "unseen_unknown_near_clay": Case(replace(outside, name="unseen_unknown_near_clay"), (2.7, 2.5)),
        "unseen_unknown_negative_fault": Case(replace(outside, name="unseen_unknown_negative_fault",
                                                      bias=-.9, conditions=bias.conditions), (3.7, 3.6)),
        "unseen_sulfate_drift": Case(replace(cases["drift"].config, name="unseen_sulfate_drift",
                                             geology=Geology.SULFATE, drift_per_hour=-.3)),
        "unseen_imager_fault": Case(replace(healthy, name="unseen_imager_fault", bias=-1.1,
                                             conditions={"spectrometer": Condition.HEALTHY,
                                                         "imager": Condition.BIAS})),
        "unseen_noisy_clay": Case(replace(cases["drift"].config, name="unseen_noisy_clay",
                                           conditions=healthy.conditions, noise_scale=1.5)),
    })
    return cases


def any_fault(belief):
    if isinstance(belief, LegacyBelief):
        return belief.any_fault()
    return float(belief.weights[(STATES[:, 1:] != 0).any(axis=1)].sum())


def run_episode(case: Case, seed: int, settings: Settings | None = None, trace=False,
                independent_case_noise=False):
    """Private world used only to generate evidence and score after policy selection."""
    settings = Settings() if settings is None else settings
    if not isinstance(seed, int) or not 0 <= seed < 2**64:
        raise ValueError("invalid seed")
    world = case.config
    belief = make_belief(world.noise_scale, settings)
    energy, remaining_time, elapsed = world.energy_wh, world.time_h, 0.
    repaired, counts, events = set(), {}, []
    latencies = []
    active_counts = {key: 0 for key in ("tp", "fp", "tn", "fn")}

    def generate(instrument, kind, timestamp):
        key = (instrument, kind)
        counts[key] = counts.get(key, 0) + 1
        stream_key = [seed, INSTRUMENTS.index(instrument), counts[key], int(kind == "reference")]
        if independent_case_noise:
            stream_key.extend(np.frombuffer(hashlib.sha256(world.name.encode()).digest()[:16], dtype="<u4").tolist())
        rng = np.random.default_rng(np.random.SeedSequence(stream_key))
        condition = Condition.HEALTHY if instrument in repaired else world.conditions[instrument]
        offset = world.bias if condition == Condition.BIAS else world.drift_per_hour * timestamp if condition == Condition.DRIFT else 0.
        mean = (case.private_means[INSTRUMENTS.index(instrument)] if case.private_means else
                MEANS[instrument][world.geology]) if kind == "science" else 0.
        return Evidence(instrument, kind, timestamp, float(rng.normal(mean + offset,
                                                                     NOISE[instrument] * world.noise_scale)))

    def active_score():
        for name in INSTRUMENTS:
            actual = world.conditions[name] != Condition.HEALTHY and name not in repaired
            predicted = belief.active_fault(name) >= .5
            key = "tp" if actual and predicted else "fn" if actual else "fp" if predicted else "tn"
            active_counts[key] += 1

    start = time.perf_counter()
    decision = "abstain"
    for step in range(world.horizon + 1):
        tick = time.perf_counter()
        action, values = select(belief, energy, remaining_time, world.horizon - step, elapsed, settings)
        latencies.append(time.perf_counter() - tick)
        if action not in ACTION_COSTS:
            decision = action
            break
        instrument = "spectrometer" if action.endswith("spectrometer") else "imager"
        e_cost, t_cost = ACTION_COSTS[action]
        readings = []
        if action.startswith("calibrate"):
            reference = generate(instrument, "reference", elapsed + 1.)
            readings.append(reference)
            if settings.ablation != "no_reference":
                belief.update(reference)
            active_score()  # Score before destructive repair, at its actual prediction time.
            repaired.add(instrument)
            belief.calibrate(instrument)
        kind = "reference" if action.startswith("check") else "science"
        reading = generate(instrument, kind, elapsed + t_cost)
        readings.append(reading)
        if kind != "reference" or settings.ablation != "no_reference":
            belief.update(reading)
        energy -= e_cost
        remaining_time -= t_cost
        elapsed += t_cost
        active_score()
        if trace:
            events.append({"action": action, "evidence": [asdict(e) for e in readings],
                           "values": values, "energy_wh": energy, "time_h": remaining_time,
                           "geology": belief.geology().tolist(), "initial_fault": any_fault(belief),
                           "active_fault": {n: belief.active_fault(n) for n in INSTRUMENTS}})
    mission_latency = time.perf_counter() - start
    claimed = decision != "abstain"
    correct = claimed and decision == world.geology.value
    fault_truth = any(c != Condition.HEALTHY for c in world.conditions.values())
    fault_probability = any_fault(belief)
    unknown = float(belief.geology()[3])
    energy_used, time_used = world.energy_wh - energy, world.time_h - remaining_time
    utility = (10. if correct else settings.wrong_reward if claimed else 0.) - .15 * energy_used - .1 * time_used
    return {"case": world.name, "seed": seed, "policy": settings.policy, "ablation": settings.ablation,
            "terminal": decision, "claimed": claimed, "correct": correct,
            "initial_fault_truth": fault_truth, "initial_fault_probability": fault_probability,
            "initial_fault_predicted": fault_probability >= .5,
            "unknown_truth": world.geology == Geology.OTHER, "unknown_probability": unknown,
            "unknown_predicted": unknown >= .5, "truth_geology": world.geology.value,
            "utility": utility, "regret": (10 if world.geology != Geology.OTHER else 0) - utility,
            "energy_used_wh": energy_used, "time_used_h": time_used,
            "within_budget": energy >= 0 and remaining_time >= 0,
            "actions": step, "faults_removed": sum(world.conditions[n] != Condition.HEALTHY for n in repaired),
            "active_instrument_time_counts": active_counts,
            "mission_latency_s": mission_latency, "decision_latencies_s": latencies,
            "trace": events}
