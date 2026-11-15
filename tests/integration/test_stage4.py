from pathlib import Path

from streamlit.testing.v1 import AppTest

from aurora.mission import run_mission
from aurora.planning import ACTION_BY_NAME
from aurora.simulator import scenarios

APP = Path(__file__).resolve().parents[2] / "src/aurora/dashboard/app.py"


def test_s4_i01_bounded_mission():
    mission, _ = run_mission(scenarios()["drift"], 42)
    assert ACTION_BY_NAME[mission.stop_reason].terminal
    assert len(mission.events) <= scenarios()["drift"].horizon + 1


def test_s4_i02_baselines_contracts():
    for policy in ("voi", "fixed_model", "information_gain", "threshold"):
        mission, _ = run_mission(scenarios()["ordinary"], 42, policy)
        assert all(event.action in ACTION_BY_NAME for event in mission.events)
        assert mission.final_energy_wh >= 0 and mission.final_time_h >= 0


def test_s4_i03_dashboard_replay():
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.button[0].click().run()
    next(item for item in app.toggle if item.label == "Autoplay autonomous mission").set_value(True).run()
    assert not app.exception
    assert any("Autonomous mission replay" in item.value for item in app.subheader)
    assert len(app.slider) == 1


def test_s4_i04_full_replay():
    mission, _ = run_mission(scenarios()["drift"], 42)
    replay, _ = run_mission(scenarios()["drift"], 42)
    assert mission == replay
    assert [(e.action, e.energy_wh, e.time_h) for e in mission.events] == [
        (e.action, e.energy_wh, e.time_h) for e in replay.events]
