import json
import os
import subprocess
import sys

from aurora.simulator import scenarios


def cli(*args):
    env = dict(os.environ, PYTHONPATH="src")
    return subprocess.run([sys.executable, "-m", "aurora", *args],
                          capture_output=True, text=True, env=env, check=False)


def test_s1_i01_cli_valid():
    result = cli("--scenario", "ordinary", "--seed", "42")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["seed"] == 42


def test_s1_i02_cli_invalid():
    result = cli("--scenario", "invalid")
    assert result.returncode != 0 and "invalid choice" in result.stderr


def test_s1_i03_all_scenarios():
    for name in scenarios():
        result = cli("--scenario", name, "--seed", "42")
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert len(data["observations"]) <= 5
        assert data["stop_reason"] == "horizon_exhausted"
