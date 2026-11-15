import hashlib
import json
from pathlib import Path

import numpy as np

from aurora.research_mission import development_cases, run_audit
from aurora.research_model import Belief

ROOT = Path(__file__).resolve().parents[2]


def test_research_preserves_historical_artifacts_and_bug002():
    hashes = json.loads((ROOT / "research_archive/preserved_hashes.json").read_text())
    for path, digest in hashes.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest


def test_research_exact_alias_is_unidentifiable():
    cases = development_cases()
    known = run_audit(cases["ordinary"], 200)
    alias = run_audit(cases["unknown_alias"], 200)
    assert known == alias  # Private label cannot change the evidence or policy.
    assert alias.terminal == "basalt"  # An explicitly documented negative result.


def test_research_reference_shape_regression():
    means, variance = Belief().parameters("imager", "reference", 1)
    assert means.shape == variance.shape == (196,)
    np.testing.assert_allclose(variance, .45 ** 2)
