import json
import os
import subprocess
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

from aurora.benchmark import ABLATIONS, load_config, run_benchmark
from aurora.mission import run_mission
from aurora.real_data import external_validation_status, official_product_status
from aurora.simulator import expected_value, scenarios

APP = Path(__file__).resolve().parents[2] / "src/aurora/dashboard/app.py"


def test_s5_i01_headless_command(tmp_path):
    output = tmp_path / "result.json"
    env = dict(os.environ, PYTHONPATH="src")
    completed = subprocess.run([sys.executable, "-m", "aurora.benchmark", "--split",
                                "development", "--limit", "1", "--no-ablations",
                                "--output", str(output)], env=env, text=True,
                               capture_output=True, check=True)
    assert "Wrote 24" in completed.stdout
    assert json.loads(output.read_text())["sample_size"] == 24
    assert output.with_suffix(".csv").exists()


def test_s5_i02_paired_scenarios():
    config, digest = load_config()
    result = run_benchmark(config, digest, "development", 1, False)
    groups = {}
    for episode in result["episodes"]:
        groups.setdefault((episode["scenario"], episode["seed"]), set()).add(episode["policy"])
    assert all(policies == set(config.policies) for policies in groups.values())
    assert result["noise_mode"] == "keyed"
    world = scenarios()["ordinary"]
    first, _ = run_mission(world, 1000, "voi", noise_mode="keyed")
    second, _ = run_mission(world, 1000, "fixed_model", noise_mode="keyed")
    def residuals(mission):
        return [o.value - expected_value(world, o.instrument, o.time_h)
                for event in mission.events for o in event.observations
                if o.instrument == "spectrometer"]
    assert residuals(first) == residuals(second)


def test_s5_i03_deterministic_replay():
    config, digest = load_config()
    first = run_benchmark(config, digest, "development", 1, False)
    second = run_benchmark(config, digest, "development", 1, False)
    def decisions(result):
        return [(e["scenario"], e["seed"], e["policy"], e["terminal"], e["utility"])
                for e in result["episodes"]]
    assert decisions(first) == decisions(second)


def test_s5_i04_ablation_rows():
    config, digest = load_config()
    result = run_benchmark(config, digest, "development", 1, True)
    assert set(result["ablations"]) == set(ABLATIONS)
    assert all(row["n"] == len(config.scenarios) for row in result["ablations"].values())


def test_s5_i05_dashboard_benchmark_replay(tmp_path, monkeypatch):
    config, digest = load_config()
    result = run_benchmark(config, digest, "development", 1, False)
    path = tmp_path / "benchmark.json"
    path.write_text(json.dumps(result), encoding="utf8")
    monkeypatch.setenv("AURORA_BENCHMARK_RESULT", str(path))
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.button[0].click().run()
    next(item for item in app.toggle if item.label == "Show benchmark comparison").set_value(True).run()
    assert not app.exception
    assert any("Measured synthetic benchmark" in item.value for item in app.subheader), (
        [(item.label, item.value) for item in app.toggle],
        [item.value for item in app.subheader], [item.value for item in app.info])
    assert any("Supported conclusion" in item.value for item in app.subheader)
    assert any("Incorrect conclusion" in item.value for item in app.subheader)
    next(item for item in app.toggle if item.label == "Show evaluation truth").set_value(True).run()
    assert not app.exception
    assert any("NOT AVAILABLE TO AGENT" in item.value for item in app.warning)


def test_s5_i06_real_validation_status():
    status = external_validation_status([])
    assert status["status"] == "adapter_only"
    assert status["ground_truth_fault_labels"] == "unavailable"
    assert not status["synthetic_likelihood_compatible"]
    official = official_product_status()
    assert official["status"] == "qualitative_schema_only"
    assert official["records_validated"] == 16
    assert official["product"]["csv_sha256"] == (
        "73b72f39db63928fbbfac44ac5400991add06a5027ba4e9e14a206910aaff749")
