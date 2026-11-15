# Suggested end-state architecture (not a Stage 1 mandate)

```text
Project_AURORA_Codex/
├── AGENTS.md, README.md, pyproject.toml, uv.lock
├── docs/  (research and stage contracts)
├── configs/ (versioned scenarios and defaults)
├── src/aurora/
│   ├── __init__.py, __main__.py
│   ├── core/       # typed models and config
│   ├── simulation/ # geology, instruments, scenario runner
│   ├── reasoning/  # beliefs, update, posterior predictive, adequacy
│   ├── planning/   # actions, utility, VOI, policies, mission loop
│   ├── evaluation/ # metrics, benchmark, confidence intervals, ablation
│   ├── data/       # optional official real-data adapter/provenance
│   └── dashboard/  # Streamlit UI; consumes domain services
├── tests/
│   ├── unit/
│   ├── regression/
│   ├── integration/
│   └── fixtures/
├── scripts/        # reproducible benchmark entry point
├── results/        # generated outputs (mostly gitignored)
└── .github/workflows/ci.yml
```

**Create modules only as their stage needs them.** Small pure functions and typed dataclasses preferred to framework/plugin architecture.

## Contract boundaries
1. `Simulator`: `(scenario_config, seed, permitted_action) -> observation + private_truth_for_evaluation`; private truth never enters agent-visible trace.
2. `BeliefEngine`: `(agent_observation_history, prior, public_model_parameters) -> posterior + diagnostics`; no hidden truth argument.
3. `Planner`: `(belief, agent_visible_resources, legal_actions) -> action + expected utilities + explanation`; no private truth argument.
4. `MissionRunner`: loops simulator->agent observation->belief update->planner until terminal decision or horizon/budget. Records both agent-visible trace and **separate restricted** eval truth.
5. `Evaluator`: consumes truth and decision records **after** execution; trains/tunes nothing on held-out results.
6. `Dashboard`: presentation only; no embedded posterior formulas or reward rules.

## Engineering defaults
- `uv` lockfile committed. `pytest` + `ruff` in CI. NumPy random `Generator` passed explicitly; no global random state.
- Use a stable per-episode RNG scheme that avoids policy-dependent noise advantages when comparing policies. Prefer pre-generated indexed observation noise or documented paired common-random-number streams, accounting for divergent actions.
- Units for all budgets and measurements; input validation; numerical stability with log probabilities as needed.
- Saved traces store config version, seed, code revision, actions, timestamps, posterior and decisions; simulation-only truth is visibly marked private.
- `uv run python -m aurora ...` is default CLI. `uv run streamlit run src/aurora/dashboard/app.py` or stable wrapper is preferred UI command; verify the actual import path.
- Windows PowerShell first, cross-platform CI on Ubuntu for portability.
