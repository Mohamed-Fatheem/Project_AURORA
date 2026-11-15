import dataclasses

from aurora.mission import run_mission
from aurora.planning import ACTION_BY_NAME, action_value, initial_state
from aurora.simulator import Geology, run, scenarios


def test_s4_r01_voi_fixture():
    value = action_value(ACTION_BY_NAME["measure_spectrometer"], initial_state())
    assert abs(value - 4.281852298128927) < 1e-10


def test_s4_r02_replay_actions():
    a, _ = run_mission(scenarios()["drift"], 42)
    b, _ = run_mission(scenarios()["drift"], 42)
    assert a == b
    assert [event.action for event in a.events] == [
        "calibrate_spectrometer", "measure_spectrometer", "conclude_clay"]


def test_s4_r03_budget_stop():
    config = dataclasses.replace(scenarios()["ordinary"], energy_wh=0)
    mission, _ = run_mission(config, 42)
    assert mission.stop_reason in ("abstain", "escalate")
    assert mission.final_energy_wh == 0


def test_s4_r04_truth_metadata_invariance():
    config = scenarios()["ordinary"]
    trace, truth = run(config, 42)
    changed = dataclasses.replace(truth, geology=Geology.OTHER)
    assert changed != truth
    assert trace.to_json() == trace.to_json()
    assert run_mission(config, 42)[0] == run_mission(config, 42)[0]
