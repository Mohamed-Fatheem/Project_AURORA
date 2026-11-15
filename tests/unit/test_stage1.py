import dataclasses
import json

import numpy as np
import pytest

from aurora.simulator import (
    MEANS,
    NOISE,
    SUPPORTED,
    AgentTrace,
    Geology,
    Observation,
    Scenario,
    expected_value,
    observe,
    run,
    scenarios,
)


def test_s1_u01_schemas():
    c = scenarios()["ordinary"]
    assert c.geology in SUPPORTED
    assert Observation(1, 1, "imager", 2, "index", 1, 1.5).unit == "index"
    with pytest.raises(ValueError):
        Scenario("bad", "unknown", c.conditions)
    with pytest.raises(ValueError):
        Observation(1, 1, "imager", 2, "meters", 1, 1.5)


def test_s1_u02_invalid_inputs():
    c = scenarios()["ordinary"]
    for kwargs in ({"energy_wh": -1}, {"noise_scale": float("nan")},
                   {"noise_scale": -1}, {"horizon": 0}, {"time_h": -1}):
        with pytest.raises(ValueError):
            dataclasses.replace(c, **kwargs)
    for seed in (-1, 2**64, 1.5):
        with pytest.raises(ValueError):
            run(c, seed)


def test_s1_u03_seed_replay():
    c = scenarios()["ordinary"]
    assert run(c, 42)[0].to_json() == run(c, 42)[0].to_json()


def test_s1_u04_seed_variation():
    c = scenarios()["ordinary"]
    values = {run(c, seed)[0].observations[0].value for seed in range(8)}
    assert len(values) >= 6


def test_s1_u05_healthy_law():
    c = scenarios()["ordinary"]
    rng = np.random.default_rng(123)
    samples = np.array([observe(c, "spectrometer", 1, rng) for _ in range(20000)])
    np.testing.assert_allclose(samples.mean(), MEANS["spectrometer"][c.geology], atol=0.01)
    np.testing.assert_allclose(samples.var(), NOISE["spectrometer"] ** 2, atol=0.003)


def test_s1_u06_bias():
    c = scenarios()["bias"]
    assert expected_value(c, "spectrometer", 1) == 2.2
    assert run(c, 1)[1].geology == Geology.BASALT


def test_s1_u07_drift():
    c = scenarios()["drift"]
    np.testing.assert_allclose(expected_value(c, "spectrometer", 3) -
                               expected_value(c, "spectrometer", 1), 1.0)
    assert expected_value(c, "imager", 3) == expected_value(c, "imager", 1)


def test_s1_u08_instruments():
    c = scenarios()["ordinary"]
    assert expected_value(c, "spectrometer", 1) != expected_value(c, "imager", 1)
    assert NOISE["spectrometer"] != NOISE["imager"]


def test_s1_u09_budget():
    c = dataclasses.replace(scenarios()["ordinary"], energy_wh=2, time_h=1)
    trace, _ = run(c, 42, ("spectrometer", "spectrometer"))
    assert len(trace.observations) == 1
    assert (trace.remaining_energy_wh, trace.remaining_time_h) == (0, 0)
    assert trace.stop_reason == "budget_exhausted"


def test_s1_u10_horizon():
    c = dataclasses.replace(scenarios()["ordinary"], horizon=1)
    trace, _ = run(c, 42, ("imager", "imager"))
    assert len(trace.observations) == 1
    assert trace.stop_reason == "horizon_exhausted"


def test_s1_u11_outside_family():
    trace, truth = run(scenarios()["outside"], 42)
    assert truth.geology == Geology.OTHER and truth.geology not in SUPPORTED
    assert "other" not in trace.to_json()


def test_s1_u12_no_leakage():
    trace, _ = run(scenarios()["bias"], 42)
    assert "geology" not in trace.to_json() and "conditions" not in trace.to_json()
    assert "bias" in trace.to_json()  # Public scenario name, not private condition.
    assert not set(dataclasses.asdict(trace)) & {"geology", "conditions", "truth"}


def test_observation_validation_and_action_validation():
    with pytest.raises(ValueError):
        Observation(1, 1, "imager", float("nan"), "index", 1, 1)
    with pytest.raises(ValueError):
        run(scenarios()["ordinary"], 1, ("bogus",))
    with pytest.raises(ValueError):
        expected_value(scenarios()["ordinary"], "imager", -1)


def test_trace_import_rejects_private_fields():
    trace, _ = run(scenarios()["ordinary"], 1)
    payload = json.loads(trace.to_json())
    payload["truth"] = "secret"
    with pytest.raises(ValueError):
        AgentTrace.from_json(json.dumps(payload))
