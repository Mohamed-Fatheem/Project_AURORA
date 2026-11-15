"""Versioned, synthetic, scalar observation model. Values are dimensionless indices.

Noise is independent Gaussian with standard deviation in index units. The two
instruments have different means and noise. These are illustrative rather than
calibrated planetary instruments. Drift is linear in elapsed mission hours.
"""

import json
import math
from dataclasses import asdict, dataclass
from enum import Enum

import numpy as np

SCHEMA_VERSION = "1.0"
MODEL_VERSION = "synthetic-1"


class Geology(str, Enum):
    BASALT = "basalt"
    CLAY = "clay"
    SULFATE = "sulfate"
    OTHER = "other"  # Generator only; outside the supported hypothesis family.


SUPPORTED = (Geology.BASALT, Geology.CLAY, Geology.SULFATE)


class Condition(str, Enum):
    HEALTHY = "healthy"
    BIAS = "bias"
    DRIFT = "drift"


MEANS = {
    "spectrometer": {Geology.BASALT: 1.0, Geology.CLAY: 2.5,
                     Geology.SULFATE: 4.0, Geology.OTHER: 5.5},
    "imager": {Geology.BASALT: 4.0, Geology.CLAY: 2.8,
               Geology.SULFATE: 1.2, Geology.OTHER: 5.0},
}
NOISE = {"spectrometer": 0.3, "imager": 0.45}
COST = {"spectrometer": (2.0, 1.0), "imager": (1.0, 1.5)}  # energy Wh, time h


@dataclass(frozen=True)
class Scenario:
    name: str
    geology: Geology
    conditions: dict[str, Condition]
    bias: float = 0.0
    drift_per_hour: float = 0.0
    noise_scale: float = 1.0
    energy_wh: float = 12.0
    time_h: float = 12.0
    horizon: int = 5

    def __post_init__(self) -> None:
        if not isinstance(self.geology, Geology) or not all(
            k in MEANS and isinstance(v, Condition) for k, v in self.conditions.items()
        ) or set(self.conditions) != set(MEANS):
            raise ValueError("invalid geology or instrument condition")
        if not self.name or not isinstance(self.horizon, int) or self.horizon <= 0:
            raise ValueError("name and positive integer horizon required")
        if any(not math.isfinite(x) for x in (
            self.bias, self.drift_per_hour, self.noise_scale, self.energy_wh, self.time_h
        )) or self.noise_scale < 0 or self.energy_wh < 0 or self.time_h < 0:
            raise ValueError("finite nonnegative noise and budgets required")


@dataclass(frozen=True)
class Observation:
    step: int
    time_h: float
    instrument: str
    value: float
    unit: str
    energy_cost_wh: float
    time_cost_h: float

    def __post_init__(self) -> None:
        if self.instrument not in MEANS or self.unit != "index" or self.step < 1:
            raise ValueError("invalid observation provenance or unit")
        if any(not math.isfinite(x) for x in (
            self.time_h, self.value, self.energy_cost_wh, self.time_cost_h
        )) or min(self.time_h, self.energy_cost_wh, self.time_cost_h) < 0:
            raise ValueError("invalid observation value, time or cost")


@dataclass(frozen=True)
class AgentTrace:
    schema_version: str
    model_version: str
    scenario: str
    seed: int
    public_config: dict[str, float | int]
    initial_energy_wh: float
    initial_time_h: float
    remaining_energy_wh: float
    remaining_time_h: float
    observations: tuple[Observation, ...]
    stop_reason: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), allow_nan=False)

    @classmethod
    def from_json(cls, raw: str) -> "AgentTrace":
        data = json.loads(raw)
        if set(data) != set(cls.__dataclass_fields__) or data["schema_version"] != SCHEMA_VERSION:
            raise ValueError("incompatible or non-agent trace")
        data["observations"] = tuple(Observation(**item) for item in data["observations"])
        return cls(**data)


@dataclass(frozen=True)
class PrivateTruth:
    geology: Geology
    conditions: dict[str, Condition]


def scenarios() -> dict[str, Scenario]:
    healthy = {key: Condition.HEALTHY for key in MEANS}
    return {
        "ordinary": Scenario("ordinary", Geology.BASALT, healthy),
        "unusual": Scenario("unusual", Geology.SULFATE, healthy),
        "bias": Scenario("bias", Geology.BASALT,
                         {"spectrometer": Condition.BIAS, "imager": Condition.HEALTHY}, bias=1.2),
        "drift": Scenario("drift", Geology.CLAY,
                          {"spectrometer": Condition.DRIFT, "imager": Condition.HEALTHY},
                          drift_per_hour=0.5),
        "conflict": Scenario("conflict", Geology.CLAY,
                             {"spectrometer": Condition.BIAS, "imager": Condition.HEALTHY}, bias=1.5),
        "outside": Scenario("outside", Geology.OTHER, healthy),
    }


def expected_value(config: Scenario, instrument: str, time_h: float) -> float:
    if instrument not in MEANS or not math.isfinite(time_h) or time_h < 0:
        raise ValueError("invalid instrument or elapsed time")
    condition = config.conditions[instrument]
    offset = config.bias if condition == Condition.BIAS else (
        config.drift_per_hour * time_h if condition == Condition.DRIFT else 0.0
    )
    return MEANS[instrument][config.geology] + offset


def observe(config: Scenario, instrument: str, time_h: float, rng: np.random.Generator) -> float:
    return float(rng.normal(expected_value(config, instrument, time_h),
                            NOISE[instrument] * config.noise_scale))


def run(config: Scenario, seed: int, actions: tuple[str, ...] | None = None) -> tuple[AgentTrace, PrivateTruth]:
    if not isinstance(seed, int) or not 0 <= seed < 2**64:
        raise ValueError("seed must be an unsigned 64-bit integer")
    rng = np.random.default_rng(seed)
    actions = actions if actions is not None else tuple(MEANS)[0:1] * config.horizon
    energy, time = config.energy_wh, config.time_h
    elapsed = 0.0
    observations: list[Observation] = []
    reason = "actions_complete"
    for instrument in actions:
        if len(observations) >= config.horizon:
            reason = "horizon_exhausted"
            break
        if instrument not in COST:
            raise ValueError(f"unknown instrument: {instrument}")
        e_cost, t_cost = COST[instrument]
        if energy < e_cost or time < t_cost:
            reason = "budget_exhausted"
            break
        energy -= e_cost
        time -= t_cost
        elapsed += t_cost
        observations.append(Observation(len(observations) + 1, elapsed, instrument,
                                        observe(config, instrument, elapsed, rng), "index",
                                        e_cost, t_cost))
    else:
        if len(observations) == config.horizon:
            reason = "horizon_exhausted"
    public_config = {"noise_scale": config.noise_scale, "horizon": config.horizon}
    trace = AgentTrace(SCHEMA_VERSION, MODEL_VERSION, config.name, seed, public_config, config.energy_wh,
                       config.time_h, energy, time, tuple(observations), reason)
    return trace, PrivateTruth(config.geology, dict(config.conditions))
