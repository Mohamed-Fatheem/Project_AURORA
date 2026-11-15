from pathlib import Path

from streamlit.testing.v1 import AppTest

from aurora.dashboard.service import Controls, belief_rows, simulate
from aurora.inference import infer, infer_trace
from aurora.simulator import AgentTrace, Geology, PrivateTruth, run, scenarios

APP = Path(__file__).resolve().parents[2] / "src/aurora/dashboard/app.py"


def test_s3_i01_simulation_to_inference():
    trace = simulate(Controls())
    assert infer(trace.observations, trace.public_config["noise_scale"]) == infer_trace(trace)


def test_s3_i02_dashboard_adapter():
    trace = simulate(Controls())
    rows = belief_rows(trace)
    assert len(rows) == len(trace.observations)
    assert all(0 <= row["unknown_probability"] <= 1 for row in rows)
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.button[0].click().run()
    assert not app.exception
    assert any("Scientific belief" in item.value for item in app.subheader)


def test_s3_i03_visible_replay():
    trace = simulate(Controls(scenario="drift"))
    assert infer_trace(AgentTrace.from_json(trace.to_json())) == infer_trace(trace)


def test_s3_i04_private_truth_mutation():
    trace, _ = run(scenarios()["ordinary"], 42)
    forged = PrivateTruth(Geology.OTHER, {})
    assert forged.geology != scenarios()["ordinary"].geology
    assert infer_trace(trace) == infer_trace(trace)
    assert "truth" not in infer.__annotations__
