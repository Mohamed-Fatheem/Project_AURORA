from pathlib import Path

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from aurora.research_mission import development_cases, replay, run_audit


@pytest.mark.parametrize("name", list(development_cases()))
def test_research_bounded_scenarios_and_replay(name):
    case = development_cases()[name]
    mission = run_audit(case, 200)
    assert 0 <= mission.energy_wh <= case.config.energy_wh
    assert 0 <= mission.time_h <= case.config.time_h
    assert len(mission.events) <= case.config.horizon
    posterior = replay(mission.events, case.config.noise_scale)
    if mission.events:
        np.testing.assert_allclose(posterior.geology(), mission.events[-1].geology)
        assert all(posterior.initial_fault(n) == mission.events[-1].initial_fault[i]
                   for i, n in enumerate(("spectrometer", "imager")))
    assert mission == run_audit(case, 200)


def test_research_recovery_keeps_initial_fault_and_no_active_fault():
    mission = run_audit(development_cases()["bias"], 200)
    event = mission.events[0]
    assert event.action == "calibrate_spectrometer"
    assert event.evidence[0].kind == "reference"
    assert event.initial_fault[0] > .9 and event.active_fault[0] == 0


def test_research_audit_dashboard_no_truth_default():
    path = Path(__file__).resolve().parents[2] / "src/aurora/dashboard/research_app.py"
    app = AppTest.from_file(path, default_timeout=30).run()
    app.button[0].click().run()
    assert not app.exception and not app.warning
    app.toggle[0].set_value(True).run()
    assert any("NOT AVAILABLE TO AGENT" in warning.value for warning in app.warning)
