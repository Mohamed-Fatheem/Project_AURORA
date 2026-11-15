"""Step 1 development audit view; no final benchmark results or truth by default."""

from dataclasses import asdict

import streamlit as st

from aurora.research_mission import development_cases, run_audit

st.set_page_config(page_title="AURORA research audit", layout="wide")
st.title("AURORA · Development audit model")
st.caption("Continuous synthetic inference; Step 1 diagnostics, not final validation.")
cases = development_cases()
name = st.selectbox("Development case", list(cases))
seed = int(st.number_input("Development seed", min_value=200, max_value=999, value=200))
if st.button("Run audit", type="primary"):
    mission = run_audit(cases[name], seed)
    st.session_state["audit"] = asdict(mission)
    st.session_state["audit_case"] = name
if "audit" in st.session_state:
    st.subheader(f"Agent audit · {st.session_state['audit_case']}")
    st.caption("Initial fault probabilities retain pre-repair evidence; active probabilities"
               " account for the declared calibration reset. Science values use index units.")
    st.json(st.session_state["audit"])
    if st.toggle("Show evaluation truth", value=False):
        st.warning("SIMULATOR TRUTH—NOT AVAILABLE TO AGENT")
        case = cases[st.session_state["audit_case"]]
        st.json({"geology": case.config.geology.value,
                 "initial_conditions": {k: v.value for k, v in case.config.conditions.items()},
                 "private_generating_means": case.private_means})
