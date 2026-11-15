import csv
import io

import numpy as np

from aurora.dashboard.service import Controls, csv_export, observation_rows, simulate
from aurora.simulator import AgentTrace


def test_s2_r01_plot_fixture():
    rows = observation_rows(simulate(Controls(instrument="spectrometer")))
    np.testing.assert_allclose([r["value"] for r in rows],
                               [1.0914151239263294, 0.6880047681278514,
                                1.2251353587419371, 1.282169414917364,
                                0.41468944340384283], atol=1e-14)
    assert [r["time_h"] for r in rows] == [1, 2, 3, 4, 5]


def test_s2_r02_rerun_reset_state():
    first = simulate(Controls(scenario="ordinary", seed=42)).to_json()
    changed = simulate(Controls(scenario="drift", seed=42)).to_json()
    again = simulate(Controls(scenario="ordinary", seed=42)).to_json()
    assert first == again and first != changed


def test_s2_r03_export_compatibility():
    trace = simulate(Controls(seed=19, instrument="imager"))
    assert AgentTrace.from_json(trace.to_json()).to_json() == trace.to_json()
    rows = list(csv.DictReader(io.StringIO(csv_export(trace))))
    np.testing.assert_allclose([float(r["value"]) for r in rows],
                               [o.value for o in trace.observations])
