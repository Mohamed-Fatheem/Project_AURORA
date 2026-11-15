"""Read-only final evaluation viewer with agent evidence replay."""

import json
import os
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from aurora.final_experiments import case_catalog, run_episode
from aurora.final_policies import Settings

st.set_page_config(page_title="AURORA final research", layout="wide")
st.title("AURORA · Final synthetic evaluation")
path = Path(os.environ.get("AURORA_FINAL_RESULT", str(Path(__file__).resolve().parents[3] / "results/research_final_v2.json")))
if not path.exists():
    st.info("Run the frozen final benchmark to load measured results.")
else:
    result = json.loads(path.read_text(encoding="utf8"))
    st.caption(f"{result['version']} · {result['n_episode_rows']} episode rows · "
               f"config {result['config_sha256'][:12]} · partial run: {result['partial']}")
    summaries = result["summary"]
    chart = go.Figure(go.Bar(x=list(summaries), y=[v["utility"]["mean"] for v in summaries.values()]))
    chart.update_layout(title="Measured mean synthetic utility", xaxis_title="Policy", yaxis_title="Utility")
    st.plotly_chart(chart, width="stretch")
    st.json({"metrics_and_intervals": summaries, "paired": result["paired"],
             "uncertainty_method": result["uncertainty"]}, expanded=False)
    st.caption("Synthetic scores only. APXS measurements support a feasibility demonstration, not real accuracy.")
    st.json(result["real_data"], expanded=False)
    policy = st.selectbox("Replay policy", list(summaries))
    examples = [r for r in result["rows"] if r["policy"] == policy]
    labels = [f"{r['case']} / seed {r['seed']} / {r['terminal']}" for r in examples]
    selection = st.selectbox("Replay episode", range(len(examples)), format_func=lambda i: labels[i])
    row = examples[selection]
    replay = run_episode(case_catalog()[row["case"]], row["seed"], Settings(policy=policy), trace=True,
                         independent_case_noise=True)
    st.subheader("Agent evidence and selected actions")
    st.json({"terminal": replay["terminal"], "trace": replay["trace"]}, expanded=False)
    if st.toggle("Show offline evaluation truth", value=False):
        st.warning("SIMULATOR TRUTH—NOT AVAILABLE TO AGENT")
        st.json({key: row[key] for key in ("truth_geology", "initial_fault_truth", "correct", "unknown_truth")})
