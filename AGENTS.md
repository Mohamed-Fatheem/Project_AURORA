# AGENTS.md — Binding instructions for Codex

## Mission
Build **AURORA: Self-Auditing Scientific Autonomy for Planetary Exploration** from scratch: a scientifically defensible, CPU-first, demoable interactive dashboard where an agent distinguishes planetary evidence from instrument faults/model inadequacy and chooses feasible resource-aware follow-up experiments.

## Priority and reading order
1. This file (mandatory process rules).
2. `docs/STAGE_STATUS.md` (current stage, approval state).
3. The **current stage only** in `docs/IMPLEMENTATION_PLAN.md`.
4. Relevant sections of `docs/PROJECT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/TEST_PLAN.md`, and `docs/EVALUATION_PROTOCOL.md`.
5. Only code/tests needed for the current task; do not read the entire repository or generate enormous logs unless required.

## Non-negotiable stage approval protocol
- **Only Stage 1 is authorized initially.** Every later stage is **BLOCKED** until the USER explicitly approves the preceding stage and instructs you to start the next.
- `docs/STAGE_STATUS.md` is a record, **not self-authorization**. Codex may mark a stage `READY_FOR_REVIEW`, but **must not mark it `APPROVED` on the user's behalf**.
- Completing tests, committing code, hitting a context limit, or receiving an automated tool response is **not approval**.
- Never implement future stage features “because they are easy”, or begin them after reporting a prior stage complete.
- Approval wording must be unambiguous: e.g., `APPROVE STAGE 1; START STAGE 2`. If unclear, stop and request it.
- After each stage: provide demo instructions; files changed; tests actually executed with counts and outcomes; lint and CI status; reproducibility evidence; limitations; exact outstanding items. Then write **`STOP — AWAITING USER APPROVAL FOR NEXT STAGE`** and end.
- If a gate fails, repair it within the approved stage or document blocker; do not bypass or weaken tests.

## Scientific integrity and flexibility
- The methods in the plan are **recommended**, not immutable. If a materially better scientific or technical alternative exists, **do not silently switch**. Give a brief proposal: current approach, alternative, scientific benefit, tradeoffs, time/token impact, validation changes, recommendation. **Wait for user approval** before the material change.
- Routine implementation choices (naming, small helper functions, harmless refactoring) require no approval.
- If identifiability, likelihood assumptions, fairness, real-data provenance, or evaluation leakage are uncertain, flag explicitly and request a decision before changing scientific semantics.
- No access to simulator hidden truth by deployable inference/planning/baseline policies. Oracle is separate and labeled privileged.
- Never invent results, real sensor failure labels, publications or MS-application claims. Report negative outcomes as well as successes.

## Implementation boundaries
- Python 3.11+, `uv` (lockfile committed), `pytest`, `ruff`; NumPy/SciPy for small discrete models; Streamlit/Plotly from Stage 2.
- CPU only; no paid services, GPU, external model APIs, heavyweight probabilistic frameworks, asynchronous agents, databases, unnecessary libraries, or microservices without approved justification.
- Use independent domain logic; keep Streamlit out of the scientific core.
- Use typed contracts, units, explicit preconditions, deterministic random streams, provenance and versioned experiment configs.
- Construct only currently required directories/modules. Never scaffold placeholder future-stage implementations.
- No network access required for Stage 1–4. Stage 5 real-data fetch may require user approval and accessible official sources.

## Unit, regression, integration, CI rules
- **Implement every case in the current stage's `docs/TEST_PLAN.md` inventory**, unless impossible; then report exactly which IDs are blocked and why, and do not declare stage ready.
- Unit-test every public scientific behavior, branch and input validation, including numeric/invalid/budget boundary cases.
- Every bug fix receives a targeted regression test. Keep historical fixtures stable unless approved scientific model changes require versioning.
- All randomness is seeded. Tests use deterministic fixed fixtures, `numpy.testing` tolerances and analytic hand-checks; avoid brittle floating comparisons.
- Enforce both scientific correctness and no-leakage between simulator truth and agent observations.
- Run focused tests during edits, then `uv run pytest -q` and `uv run ruff check .` at each stage end; add CI on pushes/PRs.
- A stage is `READY_FOR_REVIEW` only if its documented acceptance criteria pass, required test IDs exist and pass, prior-stage regression tests pass, and the demo works.
- Do **not** lower assertions or edit expected results merely to pass tests; if semantics change, explain, seek approval where material and version the fixture.
- Record pass/fail/skip counts, commands and exact reason for any skipped test in `docs/STAGE_STATUS.md`.

## Token discipline
- Work **one stage at a time**. One compact plan before coding, then implement vertical slices with narrow tests.
- Read files selectively; use `git diff --stat` and focused diffs. Don't dump entire logs or large dataframes.
- Keep replies concise; avoid repeatedly copying long specs. Update a short stage handoff and start fresh Codex conversations from it when needed.
- No agent swarms, parallel exploratory implementations, repeated broad web research or repeated repo rewrites.
- Low effort for scaffolding/UI/test plumbing; higher reasoning only for Bayesian inference, VOI/decision semantics, and methodology review.
- Before expansive rewrites, stop, explain cause and propose a minimal change for user approval if it changes design.

## Stage final response format
1. Stage and status: `READY_FOR_REVIEW` or `BLOCKED`.
2. Implemented / demo run command.
3. Required test IDs and actual test summary; lint/CI status.
4. Known scientific and implementation limitations.
5. Files changed, commit hash (only if a commit was actually created), and `docs/STAGE_STATUS.md` update.
6. Approval request, then **STOP**.
