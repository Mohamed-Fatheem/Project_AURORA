import dataclasses

import numpy as np

from aurora.simulator import AgentTrace, run, scenarios


def test_s1_r01_ordinary_snapshot():
    trace, _ = run(scenarios()["ordinary"], 42)
    assert [o.instrument for o in trace.observations] == ["spectrometer"] * 5
    np.testing.assert_allclose([o.value for o in trace.observations],
                               [1.0914151239263294, 0.6880047681278514,
                                1.2251353587419371, 1.282169414917364,
                                0.41468944340384283], atol=1e-14)
    assert trace.remaining_energy_wh == 2


def test_s1_r02_fault_snapshots():
    bias, _ = run(scenarios()["bias"], 42)
    drift, _ = run(scenarios()["drift"], 42)
    np.testing.assert_allclose([o.value for o in bias.observations],
                               [o.value + 1.2 for o in run(scenarios()["ordinary"], 42)[0].observations])
    np.testing.assert_allclose([o.value for o in drift.observations],
                               [2.5 + 0.5 * o.time_h + (b.value - 1.0)
                                for o, b in zip(drift.observations,
                                                run(scenarios()["ordinary"], 42)[0].observations)])


def test_s1_r03_budget_snapshot():
    c = dataclasses.replace(scenarios()["ordinary"], energy_wh=1)
    trace, _ = run(c, 42)
    assert (len(trace.observations), trace.stop_reason, trace.remaining_energy_wh) == (
        0, "budget_exhausted", 1)


def test_s1_r04_json_roundtrip():
    trace, _ = run(scenarios()["bias"], 42)
    assert trace.public_config == {"noise_scale": 1.0, "horizon": 5}
    assert AgentTrace.from_json(trace.to_json()) == trace
    assert AgentTrace.from_json(trace.to_json()).to_json() == trace.to_json()
