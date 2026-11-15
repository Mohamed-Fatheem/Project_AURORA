# Decision record

## Approved initial choices (user-confirmed)
- **Project:** AURORA, self-auditing autonomous planetary scientific reasoning (not telemetry anomaly monitoring).
- **Data:** Hybrid (simulation first, appropriately sourced official real planetary data later).
- **Interface:** Interactive dashboard, Streamlit/Plotly recommended.
- **Compute:** CPU-first; local development; no paid infrastructure.
- **Process:** Exactly five implementation stages, explicit approval after each, independently tested with unit + regression coverage.
- **Research:** Bayesian joint reasoning, model-adequacy awareness and decision-focused VOI are **suggested** methods, subject to reasoned alternative proposals and user approval.

## Material-change request template
**Decision ID:** ADR-___  
**Stage:** ___  
**Current proposal:** ___  
**Alternative:** ___  
**Scientific reason:** ___  
**Tradeoffs, dependencies, tokens/complexity:** ___  
**New/changed tests and metrics:** ___  
**Recommendation:** ___  
**USER decision:** PENDING / APPROVED / REJECTED  

Codex must not implement a material alternative while the user decision is PENDING. Add dated ADR entries for every approved deviation from the specified research design.
