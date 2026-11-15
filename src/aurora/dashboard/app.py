"""Streamlit visualization of Stage 1 simulator outputs only."""

import json
import os
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from aurora.dashboard.service import (
    INSTRUMENT_CHOICES,
    TRUTH_LABEL,
    Controls,
    belief_rows,
    benchmark_rows,
    build_config,
    csv_export,
    event_rows,
    observation_rows,
    resource_rows,
    simulate,
)
from aurora.mission import run_mission
from aurora.simulator import NOISE, run, scenarios


def main() -> None:
    st.set_page_config(page_title="AURORA | Simulator", layout="wide")
    st.title("AURORA · Planetary observation simulator")
    st.caption("Synthetic simulator and qualified joint belief · no autonomous decisions yet")

    with st.sidebar:
        st.header("Mission setup")
        scenario = st.selectbox("Scenario", list(scenarios()), index=0)
        seed = int(st.number_input("Seed", min_value=0, max_value=2**32 - 1, value=42))
        energy = float(st.number_input("Energy budget (Wh)", min_value=0.0, value=12.0))
        time = float(st.number_input("Time budget (h)", min_value=0.0, value=12.0))
        steps = int(st.number_input("Maximum observations", min_value=1, max_value=100, value=5))
        instrument = st.selectbox("Instrument pattern", INSTRUMENT_CHOICES, index=2)
        run_clicked = st.button("Run simulation", type="primary")
        reset_clicked = st.button("Reset")
        show_truth = st.toggle("Show evaluation truth", value=False)
        mission_enabled = st.toggle("Autoplay autonomous mission", value=False)
        policy = st.radio("Mission policy", ("voi", "fixed_model", "information_gain", "threshold"))

    if reset_clicked:
        st.session_state.pop("trace_json", None)
        st.session_state.pop("trace_controls", None)
    if run_clicked:
        try:
            controls = Controls(scenario, seed, energy, time, steps, instrument)
            st.session_state["trace_json"] = simulate(controls).to_json()
            st.session_state["trace_controls"] = controls
        except ValueError as exc:
            st.error(str(exc))

    if "trace_json" not in st.session_state:
        st.info("Choose mission settings and run a simulation.")
        return

    from aurora.simulator import AgentTrace  # Local import keeps the view focused on trace data.

    trace = AgentTrace.from_json(st.session_state["trace_json"])
    controls = st.session_state["trace_controls"]
    st.subheader(f"Agent observations · {trace.scenario}")
    st.write(f"Seed {trace.seed} · {len(trace.observations)} observations · stop: {trace.stop_reason}")
    st.caption("Values are synthetic dimensionless indices; error bars show one configured noise SD,"
               " not posterior uncertainty.")

    rows = observation_rows(trace)
    fig = go.Figure()
    for name in NOISE:
        subset = [r for r in rows if r["instrument"] == name]
        if subset:
            fig.add_trace(go.Scatter(x=[r["time_h"] for r in subset],
                                     y=[r["value"] for r in subset], name=name,
                                     mode="lines+markers",
                                     error_y={"type": "data", "array": [r["noise_sd_index"]
                                                                           for r in subset]}))
    fig.update_layout(title="Observations by instrument", xaxis_title="Elapsed time (h)",
                      yaxis_title="Synthetic measurement (index)")
    st.plotly_chart(fig, width="stretch")

    resources = resource_rows(trace)
    resource_fig = go.Figure()
    resource_fig.add_trace(go.Scatter(x=[r["step"] for r in resources],
                                      y=[r["energy_wh"] for r in resources], name="Energy (Wh)"))
    resource_fig.add_trace(go.Scatter(x=[r["step"] for r in resources],
                                      y=[r["remaining_time_h"] for r in resources],
                                      name="Time (h)"))
    resource_fig.update_layout(title="Remaining mission resources", xaxis_title="Observation step",
                               yaxis_title="Remaining resource (labeled in legend)")
    st.plotly_chart(resource_fig, width="stretch")
    beliefs = belief_rows(trace)
    st.subheader("Scientific belief and self-audit")
    st.caption("Probabilities use binned synthetic likelihoods and declared priors."
               " Warnings are not verified fault or discovery labels.")
    belief_fig = go.Figure()
    for label in ("basalt", "clay", "sulfate", "other"):
        belief_fig.add_trace(go.Scatter(x=[r["step"] for r in beliefs],
                                        y=[r[label] for r in beliefs], name=label,
                                        mode="lines+markers"))
    belief_fig.update_layout(title="Geology posterior, including broad unknown component",
                             xaxis_title="Observation step", yaxis_title="Posterior probability",
                             yaxis_range=[0, 1])
    st.plotly_chart(belief_fig, width="stretch")
    fault_fig = go.Figure()
    for key, label in (("spectrometer_fault_probability", "Spectrometer fault"),
                       ("imager_fault_probability", "Imager fault")):
        fault_fig.add_trace(go.Scatter(x=[r["step"] for r in beliefs],
                                       y=[r[key] for r in beliefs], name=label,
                                       mode="lines+markers"))
    fault_fig.update_layout(title="Marginal instrument fault probabilities",
                            xaxis_title="Observation step", yaxis_title="Posterior probability",
                            yaxis_range=[0, 1])
    st.plotly_chart(fault_fig, width="stretch")
    if any(r["adequacy_warning"] for r in beliefs):
        st.warning("Model adequacy caution: low predictive mass or high unknown-component"
                   " probability. This does not identify the cause.")
    st.json(beliefs, expanded=False)
    st.subheader("Event log")
    st.json(event_rows(trace), expanded=False)
    st.download_button("Download agent trace JSON", trace.to_json(),
                       file_name="aurora-trace.json", mime="application/json")
    st.download_button("Download observations CSV", csv_export(trace),
                       file_name="aurora-observations.csv", mime="text/csv")

    if show_truth:
        config, actions = build_config(controls)
        _, truth = run(config, controls.seed, actions)
        st.warning(TRUTH_LABEL)
        st.json({"geology": truth.geology.value,
                 "instrument_conditions": {k: v.value for k, v in truth.conditions.items()}})

    if mission_enabled:
        config, _ = build_config(controls)
        mission, _ = run_mission(config, controls.seed, policy)
        index = st.slider("Replay through decision", min_value=1, max_value=len(mission.events),
                          value=len(mission.events))
        st.subheader("Autonomous mission replay")
        st.caption("One-step binned VOI and declared utility; choices are synthetic-model decisions.")
        for event in mission.events[:index]:
            st.json({"action": event.action, "reason": event.choice.reason,
                     "action_values": event.choice.values, "energy_wh": event.energy_wh,
                     "time_h": event.time_h,
                     "observations": [{"instrument": o.instrument, "time_h": o.time_h,
                                       "value_index": o.value} for o in event.observations]},
                    expanded=False)
        if index == len(mission.events):
            st.info(f"Mission stopped: {mission.stop_reason}")

    if st.toggle("Show benchmark comparison", value=False):
        result_path = Path(os.environ.get("AURORA_BENCHMARK_RESULT",
                                          str(Path(__file__).resolve().parents[3]
                                              / "results/benchmark_heldout.json")))
        if not result_path.exists():
            st.info("Run the Stage 5 benchmark to create results/benchmark_heldout.json.")
        else:
            result = json.loads(result_path.read_text(encoding="utf8"))
            comparison = benchmark_rows(result)
            st.subheader("Measured synthetic benchmark")
            st.caption(f"{result['sample_size']} episode rows · split {result['split']} · "
                       f"config SHA-256 {result['config_sha256'][:12]} · {result['noise_mode']} noise")
            chart = go.Figure(go.Bar(x=[r["policy"] for r in comparison],
                                     y=[r["mean_utility"] for r in comparison]))
            chart.update_layout(title="Mean synthetic utility by policy",
                                xaxis_title="Policy", yaxis_title="Utility units")
            st.plotly_chart(chart, width="stretch")
            st.json({"comparison": comparison, "paired": result["paired"],
                     "caveats": result["caveats"], "real_data": result["real_data"]},
                    expanded=False)
            success = next((e for e in result["episodes"] if e["correct"]), None)
            failure = next((e for e in result["episodes"] if e["claimed"] and not e["correct"]),
                           None)
            for label, episode in (("Supported conclusion", success),
                                   ("Incorrect conclusion", failure)):
                if episode is None:
                    st.info(f"No {label.lower()} in this result file.")
                    continue
                st.subheader(label)
                st.json(episode, expanded=False)
                mission, truth = run_mission(scenarios()[episode["scenario"]],
                                             episode["seed"], episode["policy"], noise_mode="keyed")
                st.json([{"action": event.action, "energy_wh": event.energy_wh,
                          "time_h": event.time_h} for event in mission.events], expanded=False)
                if show_truth:
                    st.warning(TRUTH_LABEL)
                    st.json({"geology": truth.geology.value,
                             "conditions": {k: v.value for k, v in truth.conditions.items()}})


main()
