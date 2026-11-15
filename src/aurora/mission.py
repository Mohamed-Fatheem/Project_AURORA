"""Bounded synthetic mission execution. Planning receives only VisibleState."""

from dataclasses import dataclass, replace

import numpy as np

from aurora.planning import (
    ACTION_BY_NAME,
    VERSION,
    Choice,
    VisibleState,
    calibrate_belief,
    choose,
    initial_state,
    update_observation,
)
from aurora.simulator import COST, Condition, Observation, PrivateTruth, Scenario, observe


@dataclass(frozen=True)
class MissionEvent:
    action: str
    choice: Choice
    observations: tuple[Observation, ...]
    energy_wh: float
    time_h: float


@dataclass(frozen=True)
class Mission:
    version: str
    seed: int
    scenario_name: str
    policy: str
    noise_mode: str
    ablation: str
    events: tuple[MissionEvent, ...]
    stop_reason: str
    final_energy_wh: float
    final_time_h: float


def run_mission(config: Scenario, seed: int, policy: str = "voi",
                communication: int = 0, noise_mode: str = "sequential",
                ablation: str = "none") -> tuple[Mission, PrivateTruth]:
    if not isinstance(seed, int) or not 0 <= seed < 2**64:
        raise ValueError("invalid seed")
    if noise_mode not in ("sequential", "keyed"):
        raise ValueError("unknown noise mode")
    rng = np.random.default_rng(seed)
    state = initial_state(config.energy_wh, config.time_h, config.horizon,
                          communication, config.noise_scale)
    world = config
    events = []
    instrument_counts = {name: 0 for name in COST}
    while True:
        choice = choose(state, policy, ablation)
        action = ACTION_BY_NAME[choice.action]
        observations = []
        if action.terminal:
            events.append(MissionEvent(action.name, choice, (), state.energy_wh, state.time_h))
            reason = action.name
            break
        belief = state.belief
        elapsed = state.elapsed_h + action.time_h - sum(COST[name][1]
                                                        for name in action.instruments)
        if action.calibrates:
            conditions = dict(world.conditions)
            conditions[action.calibrates] = Condition.HEALTHY
            world = replace(world, conditions=conditions)
            belief = calibrate_belief(belief, action.calibrates)
        for instrument in action.instruments:
            elapsed += COST[instrument][1]
            e_cost, t_cost = COST[instrument]
            instrument_counts[instrument] += 1
            measurement_rng = (np.random.default_rng(np.random.SeedSequence(
                [seed, list(COST).index(instrument), instrument_counts[instrument]]))
                if noise_mode == "keyed" else rng)
            observation = Observation(len(state.history) + len(observations) + 1, elapsed,
                                      instrument, observe(world, instrument, elapsed,
                                                          measurement_rng),
                                      "index", e_cost, t_cost)
            observations.append(observation)
            belief = update_observation(belief, observation, config.noise_scale)
        energy = state.energy_wh - action.energy_wh
        time = state.time_h - action.time_h
        events.append(MissionEvent(action.name, choice, tuple(observations), energy, time))
        state = VisibleState(belief, energy, time, state.communication,
                             state.steps_left - len(observations), elapsed,
                             state.history + tuple(observations), state.available,
                             state.noise_scale)
    mission = Mission(VERSION, seed, config.name, policy, noise_mode, ablation, tuple(events), reason,
                      state.energy_wh, state.time_h)
    return mission, PrivateTruth(config.geology, dict(config.conditions))
