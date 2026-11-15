# Project AURORA — Scientific product specification

## Core research question
How can an autonomous planetary explorer distinguish genuine scientific evidence from faulty instruments and inadequate scientific hypotheses, then choose the next most scientifically valuable feasible experiment under limited energy, time and communication?

## Research hypothesis (NOT a result)
Joint reasoning about latent geology, instrument reliability and model adequacy, paired with *decision-focused* Value of Information (VOI), may reduce false scientific conclusions and decision regret at comparable discovery recall and resource budgets versus simpler baselines.

## Scope and intellectual distinction
This is **scientific decision-making with epistemic self-auditing**, not a generic telemetry anomaly detector or a scientific chatbot. A decision may be: observe, cross-check with an independent instrument, recalibrate, discriminate between hypotheses, conclude, abstain, or escalate to human review (when communication is available). Every recommendation needs a reason trace.

## Core variables and data boundary
- `G`: hidden geological state/hypothesis. Initial simulation: 3 predefined hypotheses + cases where truth is outside their supported family.
- `M`: hidden per-instrument condition (healthy / biased / drifting); initial simulation: 2 sensors with distinct observation likelihoods.
- `U`: model adequacy / unknown hypothesis indicator; must not be inferred by merely renormalizing known-hypothesis probabilities.
- `D_t`: **agent-visible** observation and action history only; includes measurement provenance, timestamps, instrument ID and costs.
- `B_t`: remaining energy/time/communication budget and finite horizon.
- Hidden simulator truth is used for generating observations, oracle and **offline evaluation only**; do not put it in inference/planner interfaces.

Aim to infer or diagnose `P(G, M, U | D_t)` (or a justified calibrated adequacy test) from the observation model; explicitly discuss *identifiability*. Unknown-state inference is not magically guaranteed, especially when sensor drift and unusual geology generate similar signals.

## Suggested generative model (may improve with prior approval)
- Small discrete geology classes with well-separated but overlapping expected sensor values, realistic stochastic measurement noise, optional fixed sensor bias and time-varying drift.
- Observation likelihood conditioned on geological state, sensor condition, action and time; priors and transition assumptions documented in units.
- Independent verification instrument and calibration action must have genuine different information/cost implications.
- Missing-hypothesis scenario uses an out-of-family data-generating state; model-adequacy mechanism must be tested for false positives as well as missed unknowns.
- Configurable resources/mission horizon. Observation timestamp, measurement values, sensor identifiers and action history are first-class fields.
- All distributions, thresholds, initial priors, energy costs, reward terms and seed handling documented and versioned. Avoid overclaiming physical fidelity of synthetic Mars-like scenarios.

## Planning and stopping
Start with tractable one-step VOI against the **best terminal decision** (e.g., conclude vs abstain). Suggested formula:

`VOI(a) = E_y[max_d EU(d | D_t, y, a)] - max_d EU(d | D_t) - lambda * cost(a)`

Account once, not twice, for each action's energy, time, risk and communication. Require action feasibility, deterministic tie-breaks and explicit stop reasons. Zero budget must terminate safely. More complex lookahead is an optional approved research enhancement.

## Dashboard demo acceptance
- Stage 2: scenario/seed/budget controls; observations over time; instrument traces; remaining resources; export; separate *agent view* from *ground-truth inspection* (truth off by default).
- Stage 3: scientific posterior, instrument reliability and adequacy diagnostics, warnings with evidence provenance.
- Stage 4: interactive step/autoplay, available actions, selected action and transparent rationale, resource change, terminal conclusion or abstention.
- Stage 5: replayable representative missions, policy comparisons, results and uncertainty intervals, ablation effects, exportable benchmark summary.
- Run locally on a regular Windows laptop/CPU. Streamlit and Plotly preferred; no authentication, backend service, paid hosting or cloud requirement.

## Hybrid data policy
Simulation supplies fully known truth for controlled evaluation. A small **official** planetary dataset may be added in Stage 5 for external plausibility/adapter demonstration, preferably NASA Planetary Data System (PDS), subject to real availability, licensing, measurement semantics, instrument provenance and calibration metadata. Do **not** invent sensor failures, geological ground truth, or synthetic labels and report them as real. Separate real-world predictive/qualitative checks from simulation-only fault detection metrics.

## MS admissions contribution
Demonstrable research skills: Bayesian modeling, decision theory, uncertainty, calibrated confidence, autonomous planning, scientific software, falsifiable hypotheses, reproducible comparison baselines, ablations and critical limitations. In an interview show (1) genuine anomaly, (2) fault-induced false alarm, (3) out-of-model observation, and explain different actions. In CV/SOP state only completed work and actually measured results.

## Explicit exclusions
No planetary mission control claims, spacecraft-grade robustness claims, robotic flight hardware, real-time telemetry ingestion promises, GPU training, LLM-generated discoveries, fabricated NASA validation, or publication acceptance claims.
