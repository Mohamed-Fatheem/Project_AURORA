# Stage 2 dashboard demo

From the project root in PowerShell:

```powershell
uv sync --locked --extra dev
uv run streamlit run src/aurora/dashboard/app.py
```

Open the local URL printed by Streamlit. This dashboard visualizes synthetic
simulator output; it does not yet infer geology, diagnose faults or choose
actions autonomously.

Two-minute walkthrough:

1. Use `ordinary`, seed 42, 12 Wh, 12 h, five observations and `alternate`;
   click **Run simulation**. Inspect instrument labels, one-noise-SD error bars,
   resource history and event log. Download JSON, which is an agent-visible trace.
2. Switch to `drift` with the same seed and run. Spectrometer readings differ;
   this is simulator output, not a fault diagnosis. Switch back to `ordinary`
   and rerun to recover the same trace. **Reset** clears the displayed run.
3. Turn on **Show evaluation truth** to see the separate, labeled simulator
   state. Downloads remain agent-only regardless of the toggle.

The CSV export repeats scenario, seed, public configuration and schema/model
versions on every observation row. For a zero-observation run, use JSON: CSV
contains a header only. The plot's error bars are the configured generative
noise standard deviation, not confidence intervals or posterior uncertainty.
