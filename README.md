# AURORA — synthetic planetary scientific autonomy demo

The completed two-step research improvement is documented in
[FINAL_RESEARCH_REPORT.md](docs/FINAL_RESEARCH_REPORT.md). The frozen current
evaluation manifest is `configs/research_final_v2.json`; benchmark-2 and the
earlier reports remain historical evidence. The final viewer reads the new
measured artifacts:

```powershell
python -m uv run --extra dev python -m streamlit run src/aurora/dashboard/final_app.py
```

Regenerate final experiments with new output names (completed results are
protected from overwrite):

```powershell
python -m uv run --extra dev python -m aurora.final_benchmark --suite development --output results/replay_development.json
python -m uv run --extra dev python -m aurora.final_benchmark --suite final --output results/replay_final.json
python -m uv run --extra dev python -m aurora.final_benchmark --suite ablations --output results/replay_ablations.json
python -m uv run --extra dev python -m aurora.final_benchmark --suite robustness --output results/replay_robustness.json
python -m uv run --extra dev python -m aurora.final_benchmark --suite legacy_bridge --output results/replay_bridge.json
```

See [the frozen protocol](docs/FINAL_EVALUATION_PROTOCOL.md) for matched action
contracts, uncertainty, seed partitions and the disclosed sampling correction.
The setup and original benchmark commands below remain available.

AURORA is a CPU-first local research prototype. A small simulator generates dimensionless measurements for basalt, clay, sulfate and outside-family truth, with healthy, biased or drifting instruments. A joint discrete belief model and one-step value-of-information policy choose resource-feasible actions. Synthetic results do not establish real planetary discovery or fault detection performance.

## Windows PowerShell setup

Run from the project root:

```powershell
cd D:\Projects\Project_AURORA
python -m uv sync --locked --extra dev
python -m uv run --extra dev python -m pytest -q
python -m uv run --extra dev python -m ruff check .
python -m uv run --extra dev python -m streamlit run src/aurora/dashboard/app.py
```

Open the Local URL printed by Streamlit. The Python-module form works on this host where Windows Application Control blocks the streamlit launcher.

## Reproducible experiment

`configs/benchmark_v2.json` freezes scenarios, policy and utility versions, nonoverlapping seed splits, thresholds, keyed observation noise, and bootstrap settings. To regenerate paired results:

```powershell
python -m uv run --extra dev python -m aurora.benchmark --split development --output results/benchmark_development.json
python -m uv run --extra dev python -m aurora.benchmark --split heldout --output results/benchmark_heldout.json
```

Each command writes JSON and a compact per-scenario CSV. Full JSON includes per-episode outcomes, denominators, paired confidence intervals, config and source hashes, runtime metadata, ablations, and real-product provenance. Latency varies by host; decisions and synthetic scores should replay.

## Five-minute interview walkthrough

1. Open the dashboard with ordinary, seed 42, alternating instruments. Explain units, error bars and the agent/private-truth boundary.
2. Switch to unusual, then bias and drift. Point to geology, fault and unknown posterior trajectories. Explain why one sensor is ambiguous.
3. Run outside. Show the adequacy caution and a failure case; this is a diagnostic, not perfect detection.
4. Enable autonomous mission replay on drift. Step through selected action, competing values, costs and terminal choice. Switch to a baseline policy.
5. Open measured benchmark comparison. Explain paired seeds, confidence intervals, abstention, negative outcomes, and the limited real APXS schema check. State that synthetic utilities and noise are illustrative and the sample is small.

See [research results](docs/RESEARCH_RESULTS.md), [decision model](docs/STAGE4_DECISIONS.md), and [stage evidence](docs/STAGE_STATUS.md).

