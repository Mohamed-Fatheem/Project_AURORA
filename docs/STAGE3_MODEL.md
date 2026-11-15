# Stage 3 synthetic belief model and identifiability review

Model version `joint-binned-1` takes only observations, timestamps, instrument
IDs and public noise scale. It never accepts simulator truth or scenario names.
Geology states are basalt, clay, sulfate and an explicit broad `other` component.
Each instrument has healthy, fixed +1.2 index bias and +0.5 index/hour drift
states. These fault parameters are assumptions for inference, not calibrated
instrument characteristics. Priors are geology 0.30/0.30/0.30/0.10 and each
instrument condition 0.8/0.1/0.1, independent at initialization.

Continuous index observations are placed in bins bounded by 0, 1, 2, 3, 4
and 5, with unbounded tails. For known geology, bin likelihoods integrate the
Gaussian Stage 1 observation model; the unknown component has equal mass in
all seven bins. The broad component is deliberately not centered on the
simulator's hidden `other` mean. Joint updates use log probabilities and
renormalization; all-zero evidence raises an error. A warning is shown when
prior-predictive probability of the observed bin is below 0.05 or unknown
posterior exceeds 0.5. This is a sensitivity choice, **not** a calibrated
false-alarm rate or proof of model failure. No terminal scientific decision is
made in Stage 3.

## Identifiability checkpoint

One sensor measurement cannot generally separate geology and sensor bias.
Repeated measurements at different times can help separate static bias from
drift, and the differently responsive imager helps anchor geology, but
finite noisy traces retain ambiguity. Under the broad unknown component,
fault condition is not identified by the likelihood; its conditional
posterior remains prior-driven. The simulator's `conflict` preset uses a
+1.5 index bias, outside the assumed +1.2 model, so warnings and fault
probabilities may be misleading. The `outside` preset can also be explained
by a known geology plus drift, especially with one instrument. Neither
scenario is guaranteed to yield a correct classification. These limitations
are visible in the dashboard and must be evaluated before a stronger claim.

## Demo

From the project root: `uv run python -m streamlit run src/aurora/dashboard/app.py`.
Run `ordinary`, `bias`, `drift`, `conflict` and `outside` with seed 42 and
`alternate` instruments. Inspect geology and fault probability trajectories,
the unknown probability, prior-predictive warning and separate simulator truth
toggle. Compare observed movement, including uncertainty and failures; the
plots are conditional synthetic beliefs, not verified discoveries.
