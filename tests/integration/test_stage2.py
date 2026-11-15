import json
import os
import subprocess
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

from aurora.dashboard.service import Controls, simulate

APP = Path(__file__).resolve().parents[2] / "src/aurora/dashboard/app.py"


def test_s2_i01_app_smoke():
    app = AppTest.from_file(APP, default_timeout=30).run()
    assert not app.exception
    assert len(app.selectbox) == 2
    assert len(app.number_input) == 4
    assert len(app.button) == 2
    app.button[0].click().run()
    assert not app.exception  # BUG-001: event display must survive a full run.
    assert not app.warning
    next(item for item in app.toggle if item.label == "Show evaluation truth").set_value(True).run()
    assert not app.exception
    assert any("NOT AVAILABLE TO AGENT" in item.value for item in app.warning)


def test_s2_i02_switch_and_reset():
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.button[0].click().run()
    first = app.session_state["trace_json"]
    app.selectbox[0].set_value("drift").run()
    app.button[0].click().run()
    changed = app.session_state["trace_json"]
    assert first != changed
    app.selectbox[0].set_value("ordinary").run()
    app.button[0].click().run()
    assert app.session_state["trace_json"] == first
    app.button[1].click().run()
    assert "trace_json" not in app.session_state
    assert not app.exception


def test_s2_i03_service_cli_equivalence():
    trace = simulate(Controls(instrument="spectrometer"))
    env = dict(os.environ, PYTHONPATH="src")
    result = subprocess.run([sys.executable, "-m", "aurora", "--scenario", "ordinary",
                             "--seed", "42"], capture_output=True, text=True, env=env, check=True)
    assert json.loads(trace.to_json()) == json.loads(result.stdout)
