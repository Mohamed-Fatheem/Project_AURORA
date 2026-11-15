import csv
import io
import json

import numpy as np
import pytest

from aurora.dashboard.service import (
    TRUTH_LABEL,
    Controls,
    csv_export,
    event_rows,
    observation_rows,
    resource_rows,
    simulate,
)
from aurora.simulator import AgentTrace, PrivateTruth


def test_s2_u01_controls():
    assert Controls().scenario == "ordinary"
    for change in ({"scenario": "bogus"}, {"seed": -1}, {"steps": 0},
                   {"steps": 101}, {"energy_wh": -1}, {"time_h": float("nan")},
                   {"instrument": "bogus"}):
        with pytest.raises(ValueError):
            Controls(**change)


def test_s2_u02_observation_axis():
    trace = simulate(Controls())
    rows = observation_rows(trace)
    assert [r["time_h"] for r in rows] == sorted(r["time_h"] for r in rows)
    np.testing.assert_allclose([r["value"] for r in rows],
                               [o.value for o in trace.observations])


def test_s2_u03_instrument_association():
    rows = observation_rows(simulate(Controls(steps=4)))
    assert [r["instrument"] for r in rows] == ["spectrometer", "imager"] * 2
    assert all(r["unit"] == "index" for r in rows)
    assert rows[0]["noise_sd_index"] != rows[1]["noise_sd_index"]


def test_s2_u04_resource_plot():
    trace = simulate(Controls(steps=4))
    rows = resource_rows(trace)
    assert rows[0]["energy_wh"] == trace.initial_energy_wh
    assert rows[-1]["energy_wh"] == trace.remaining_energy_wh
    assert rows[-1]["remaining_time_h"] == trace.remaining_time_h
    assert all(r["energy_wh"] >= 0 and r["remaining_time_h"] >= 0 for r in rows)


def test_s2_u05_events():
    trace = simulate(Controls())
    for row, obs in zip(event_rows(trace), trace.observations):
        assert (row["action"], row["instrument"], row["time_h"]) == (
            "measure", obs.instrument, obs.time_h)


def test_s2_u06_agent_view_no_truth():
    trace = simulate(Controls(scenario="bias"))
    for output in (trace.to_json(), csv_export(trace), str(observation_rows(trace)),
                   str(event_rows(trace))):
        assert "PrivateTruth" not in output
        assert "conditions" not in output and "geology" not in output
    assert PrivateTruth.__name__ not in AgentTrace.__annotations__


def test_s2_u07_truth_opt_in_contract():
    assert "NOT AVAILABLE TO AGENT" in TRUTH_LABEL
    assert "truth" not in Controls.__dataclass_fields__
    assert "truth" not in AgentTrace.__dataclass_fields__


def test_s2_u08_exports():
    trace = simulate(Controls(seed=7, steps=3))
    assert AgentTrace.from_json(trace.to_json()) == trace
    rows = list(csv.DictReader(io.StringIO(csv_export(trace))))
    assert [int(r["step"]) for r in rows] == [1, 2, 3]
    assert all(r["seed"] == "7" and r["schema_version"] == "1.0"
               and r["scenario"] == "ordinary" and r["horizon"] == "3" for r in rows)


def test_s2_u09_empty_and_long_traces():
    empty = simulate(Controls(energy_wh=0))
    assert observation_rows(empty) == [] and event_rows(empty) == []
    assert len(resource_rows(empty)) == 1
    assert len(observation_rows(simulate(Controls(steps=1)))) == 1
    long = simulate(Controls(steps=100, energy_wh=200, time_h=200))
    assert len(observation_rows(long)) == 100
    assert json.loads(long.to_json())["stop_reason"] == "horizon_exhausted"
