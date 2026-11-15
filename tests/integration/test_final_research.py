
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from aurora.final_benchmark import load_manifest, run_suite
from aurora.final_experiments import run_episode
from aurora.final_policies import ABLATIONS, POLICIES, Settings
from aurora.final_real_data import feasibility_report
from aurora.research_mission import development_cases


@pytest.mark.parametrize("policy", POLICIES)
def test_final_policies_share_costs_and_bounds(policy):
    case = development_cases()["bias"]
    row = run_episode(case, 3000, Settings(policy=policy), trace=True)
    assert row["within_budget"] and row["actions"] <= case.config.horizon
    for event in row["trace"]:
        if event["action"] == "calibrate_spectrometer":
            assert event["evidence"][0]["kind"] == "reference"
    assert 0 <= row["initial_fault_probability"] <= 1
    assert row["decision_latencies_s"]


def test_final_keyed_shared_noise():
    case = development_cases()["ordinary"]
    records = [run_episode(case, 9000, Settings(policy=p), trace=True, independent_case_noise=True) for p in POLICIES]
    first_reference = []
    for row in records:
        references = [e["value"] for event in row["trace"] for e in event["evidence"]
                      if e["instrument"] == "spectrometer" and e["kind"] == "reference"]
        if references:
            first_reference.append(references[0])
    assert len(first_reference) >= 2 and len(set(first_reference)) == 1


def test_bug_004_independent_noise_between_scenario_families():
    cases = development_cases()
    known = run_episode(cases["ordinary"], 9000, trace=True, independent_case_noise=True)
    alias = run_episode(cases["unknown_alias"], 9000, trace=True, independent_case_noise=True)
    assert known["trace"][0]["evidence"][0]["value"] != alias["trace"][0]["evidence"][0]["value"]


@pytest.mark.parametrize("ablation", ABLATIONS)
def test_final_controlled_ablation_execution(ablation):
    row = run_episode(development_cases()["bias"], 3000, Settings(ablation=ablation))
    assert row["within_budget"] and row["ablation"] == ablation


def test_final_explicit_reward_sensitivity_scoring():
    case = development_cases()["unknown_alias"]
    row = run_episode(case, 200, Settings(wrong_reward=-40))
    if row["claimed"]:
        assert row["utility"] == pytest.approx(-40 - .15 * row["energy_used_wh"] - .1 * row["time_used_h"])


def test_final_real_uncertainty_preserved():
    report = feasibility_report()
    assert len(report["measurements"]) == 16
    first = report["measurements"][0]
    assert first["analyte"] == "Na2O" and first["concentration"] == 7.11
    assert first["statistical_precision"] == .41 and first["unit"] == "wt_pct"
    assert report["status"] == "feasibility_only"


def test_final_immutable_output_and_partial_run(tmp_path):
    config, digest = load_manifest()
    # One actual development seed, no final seeds; all declared development cases/policies.
    output = tmp_path / "smoke.json"
    result = run_suite(config, digest, "development", output, limit=1)
    assert result["n_episode_rows"] == 70 and result["partial"]
    assert result["paired"] and output.with_suffix(".csv").exists()
    with pytest.raises(FileExistsError):
        run_suite(config, digest, "development", output, limit=1)


def test_final_dashboard_reads_measured_file_and_truth_toggle(tmp_path, monkeypatch):
    config, digest = load_manifest()
    output = tmp_path / "viewer.json"
    run_suite(config, digest, "development", output, limit=1)
    monkeypatch.setenv("AURORA_FINAL_RESULT", str(output))
    app_path = Path(__file__).resolve().parents[2] / "src/aurora/dashboard/final_app.py"
    app = AppTest.from_file(app_path, default_timeout=30).run()
    assert not app.exception and not app.warning
    app.toggle[0].set_value(True).run()
    assert not app.exception
    assert any("NOT AVAILABLE TO AGENT" in item.value for item in app.warning)
