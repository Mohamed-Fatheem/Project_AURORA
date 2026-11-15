"""Pure UI adapter. No inference or private truth is accepted here."""

import csv
import io
import math
from dataclasses import dataclass, replace

from aurora.inference import infer_trace
from aurora.simulator import NOISE, AgentTrace, Scenario, run, scenarios

TRUTH_LABEL = "SIMULATOR TRUTH—NOT AVAILABLE TO AGENT"
INSTRUMENT_CHOICES = ("spectrometer", "imager", "alternate")


@dataclass(frozen=True)
class Controls:
    scenario: str = "ordinary"
    seed: int = 42
    energy_wh: float = 12.0
    time_h: float = 12.0
    steps: int = 5
    instrument: str = "alternate"

    def __post_init__(self) -> None:
        if self.scenario not in scenarios():
            raise ValueError("unknown scenario")
        if not isinstance(self.seed, int) or not 0 <= self.seed < 2**64:
            raise ValueError("seed must be an unsigned 64-bit integer")
        if not isinstance(self.steps, int) or not 1 <= self.steps <= 100:
            raise ValueError("steps must be between 1 and 100")
        if self.instrument not in INSTRUMENT_CHOICES:
            raise ValueError("unknown instrument choice")
        if any(not math.isfinite(x) or x < 0 for x in (self.energy_wh, self.time_h)):
            raise ValueError("budgets must be finite and nonnegative")


def build_config(controls: Controls) -> tuple[Scenario, tuple[str, ...]]:
    config = replace(scenarios()[controls.scenario], energy_wh=controls.energy_wh,
                     time_h=controls.time_h, horizon=controls.steps)
    if controls.instrument == "alternate":
        actions = tuple("spectrometer" if i % 2 == 0 else "imager"
                        for i in range(controls.steps))
    else:
        actions = (controls.instrument,) * controls.steps
    return config, actions


def simulate(controls: Controls) -> AgentTrace:
    config, actions = build_config(controls)
    return run(config, controls.seed, actions)[0]


def observation_rows(trace: AgentTrace) -> list[dict]:
    return [{"step": o.step, "time_h": o.time_h, "instrument": o.instrument,
             "value": o.value, "unit": o.unit,
             "noise_sd_index": NOISE[o.instrument] * trace.public_config["noise_scale"]}
            for o in trace.observations]


def resource_rows(trace: AgentTrace) -> list[dict]:
    rows = [{"step": 0, "time_h": 0.0, "energy_wh": trace.initial_energy_wh,
             "remaining_time_h": trace.initial_time_h}]
    energy, time = trace.initial_energy_wh, trace.initial_time_h
    for o in trace.observations:
        energy -= o.energy_cost_wh
        time -= o.time_cost_h
        rows.append({"step": o.step, "time_h": o.time_h, "energy_wh": energy,
                     "remaining_time_h": time})
    return rows


def event_rows(trace: AgentTrace) -> list[dict]:
    return [{"step": o.step, "time_h": o.time_h, "action": "measure",
             "instrument": o.instrument, "value_index": o.value,
             "energy_cost_wh": o.energy_cost_wh, "time_cost_h": o.time_cost_h}
            for o in trace.observations]


def belief_rows(trace: AgentTrace) -> list[dict]:
    return [{"step": item.step, "time_h": item.time_h, "instrument": item.instrument,
             "predictive_probability": item.predictive_probability,
             "unknown_probability": item.unknown_probability,
             "spectrometer_fault_probability": item.spectrometer_fault_probability,
             "imager_fault_probability": item.imager_fault_probability,
             "adequacy_warning": item.adequacy_warning, **item.geology}
            for item in infer_trace(trace)]


def benchmark_rows(result: dict) -> list[dict]:
    if result.get("schema_version") != "benchmark-result-1":
        raise ValueError("unsupported benchmark result")
    return [{"policy": name, "episodes": result["summary"][name]["n"],
             "mean_utility": result["summary"][name]["mean_utility"],
             "false_discovery_proportion": result["summary"][name]["false_discovery_proportion"],
             "discovery_recall": result["summary"][name]["discovery_recall"]}
            for name in result["policies"]]


def csv_export(trace: AgentTrace) -> str:
    stream = io.StringIO(newline="")
    fields = ["schema_version", "model_version", "scenario", "seed", "horizon",
              "noise_scale", "initial_energy_wh", "initial_time_h", "stop_reason",
              "step", "time_h", "instrument", "value", "unit", "energy_cost_wh",
              "time_cost_h"]
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for o in trace.observations:
        writer.writerow({"schema_version": trace.schema_version,
                         "model_version": trace.model_version, "scenario": trace.scenario,
                         "seed": trace.seed, "horizon": trace.public_config["horizon"],
                         "noise_scale": trace.public_config["noise_scale"],
                         "initial_energy_wh": trace.initial_energy_wh,
                         "initial_time_h": trace.initial_time_h, "stop_reason": trace.stop_reason,
                         "step": o.step, "time_h": o.time_h, "instrument": o.instrument,
                         "value": o.value, "unit": o.unit,
                         "energy_cost_wh": o.energy_cost_wh, "time_cost_h": o.time_cost_h})
    return stream.getvalue()
