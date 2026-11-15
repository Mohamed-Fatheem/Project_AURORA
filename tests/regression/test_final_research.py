import hashlib
import json
import zipfile
from pathlib import Path

from aurora.final_experiments import run_episode
from aurora.research_mission import development_cases, run_audit

ROOT = Path(__file__).resolve().parents[2]


def test_final_preserves_all_historical_hashes():
    for path, digest in json.loads((ROOT / "research_archive/preserved_hashes.json").read_text()).items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest


def test_final_step1_source_archive():
    digest = hashlib.sha256()
    with zipfile.ZipFile(ROOT / "research_archive/research_step1_source.zip") as archive:
        for name in sorted(archive.namelist()):
            digest.update(name.encode())
            digest.update(archive.read(name))
    freeze = json.loads((ROOT / "research_archive/research_step1_freeze.json").read_text())
    assert freeze["version"] == "research-step1"
    assert digest.hexdigest() == freeze["source_sha256"]


def test_final_improved_nominal_matches_approved_step1():
    case = development_cases()["bias"]
    approved = run_audit(case, 200)
    improved = run_episode(case, 200, trace=True)
    assert improved["terminal"] == approved.terminal
    assert [event["action"] for event in improved["trace"]] == [e.action for e in approved.events]
    assert improved["energy_used_wh"] == case.config.energy_wh - approved.energy_wh


def test_final_exact_unknown_alias_stays_negative_result():
    cases = development_cases()
    first = run_episode(cases["ordinary"], 200)
    alias = run_episode(cases["unknown_alias"], 200)
    assert first["terminal"] == alias["terminal"] == "basalt"
    assert first["correct"] and not alias["correct"]
