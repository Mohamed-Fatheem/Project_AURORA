# Stage 1 local setup (Windows PowerShell)

Install Python 3.11+ and uv, then from the project root:

```powershell
uv sync --locked --extra dev
uv run python -m aurora --scenario ordinary --seed 42
uv run python -m aurora --scenario drift --seed 42 --truth
uv run pytest -q
uv run ruff check .
```

The first JSON line is the agent-visible trace. `--truth` adds a separate,
clearly labeled private evaluation line. The generated trace can be redirected
to a `.json` file. No policy or inference is implemented yet.

All measurements are synthetic dimensionless `index` values. Spectrometer
means for basalt/clay/sulfate/other are 1.0/2.5/4.0/5.5;
imager means are 4.0/2.8/1.2/5.0. Independent Gaussian noise has standard
deviation 0.30 and 0.45 index units respectively, multiplied by public
`noise_scale`. Fixed bias adds 1.2 or 1.5 index units in the supplied cases.
Drift adds 0.5 index units per elapsed mission hour. Calibration is deferred;
there is no reset transition in Stage 1. Observations occur after action time
cost is spent. Instrument costs are spectrometer 2 Wh/1 h and imager 1 Wh/1.5 h.
Default initial resources are 12 Wh/12 h and horizon five observations.

The seed is passed to a local NumPy `Generator`; the global RNG is unused.
`schema_version=1.0` and `model_version=synthetic-1` identify this synthetic
law. The public trace records the scenario name, seed, noise scale, horizon,
initial and remaining resources, provenance and stop reason. Scenario names
are public experiment identifiers and can reveal the preset to a human;
future deployable policies must consume only agent observations and public
configuration, never infer hidden truth from scenario names. `PrivateTruth`
is returned separately and never serialized by `AgentTrace`.

Supported future inference hypotheses are basalt, clay and sulfate; no priors
are applied in Stage 1. `other` generates outside-family truth for evaluation.
These values are illustrative and have no physical calibration or real-data
provenance. In particular, an outside-family episode is generated, not detected.
