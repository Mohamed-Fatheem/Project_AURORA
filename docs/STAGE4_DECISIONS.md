# Stage 4 synthetic decision model

Policy version `voi-1` ranks feasible actions using exact one-step enumeration
of the seven Stage 3 observation bins. Terminal utility is +10 for a correct
known-geology conclusion and -20 for a wrong one; abstention is 0.
Escalation is +1 when one communication unit is available. These are illustrative
utility units, not mission-certified preferences. Every nonterminal action
subtracts 0.15 utility/Wh and 0.10 utility/h exactly once. Terminal actions
have no resource cost. The agent chooses the highest score, breaking ties by
the documented action order in `planning.ACTIONS`.

Measurement actions use the Stage 1 synthetic sensor model. `cross_check`
is an imager reading and requires an earlier spectrometer reading.
`discriminate` performs spectrometer then imager readings within one action;
its one-step value enumerates all 49 bin pairs. `calibrate_spectrometer` is a
composite: it resets the spectrometer to healthy, then measures. Its 4 Wh/2 h
cost includes the 2 Wh/1 h measurement. This gives calibration an immediate
observation effect and permits one-step VOI comparison; it is not a model of a
real calibration procedure. The belief transition collapses spectrometer
fault states to healthy before the reading. All actions require sufficient
energy/time and remaining observation horizon. Zero resources or exhausted
horizon force a feasible terminal action.

The fixed-model baseline conditions on both instruments being healthy and
otherwise shares feasibility; information gain ranks nonterminal actions by
joint-state entropy reduction, with terminal utility as a stopping option;
threshold concludes the most probable known geology at 0.85 or measures with
a terminal fallback. These baselines are exploratory, not tuned or fairly
benchmarked yet. No deployable policy accepts simulator truth. The mission
runner returns private truth separately for later offline evaluation.

## Demo

From the project root, launch
`python -m uv run --extra dev python -m streamlit run src/aurora/dashboard/app.py`.
Run the `drift` scenario, seed 42, then turn on **Autoplay autonomous mission**.
The current VOI policy calibrates the spectrometer, measures again, and
concludes clay in the fixed smoke fixture. Inspect action values, costs,
remaining resources and observations. Use **Replay through decision** to
step through the recorded mission; change policy to inspect a baseline.

The Stage 3 unknown component and sensor faults remain only partially
identifiable; policy choices inherit this uncertainty and the arbitrary
synthetic utility values. The selected action is a transparent model result,
not operational advice for a spacecraft.
