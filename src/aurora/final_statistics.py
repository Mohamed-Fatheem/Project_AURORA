"""Episode-level uncertainty, with no artificial independence for repeated readings."""

import math

import numpy as np


def wilson(successes, total):
    if total == 0:
        return "N/A"
    z = 1.959963984540054
    fraction = successes / total
    center = (fraction + z * z / (2 * total)) / (1 + z * z / total)
    half = z / (1 + z * z / total) * math.sqrt(fraction * (1 - fraction) / total + z * z / (4 * total * total))
    return [max(0., center - half), min(1., center + half)]


def rate_record(numerator, denominator):
    return {"value": numerator / denominator if denominator else "N/A",
            "numerator": int(numerator), "denominator": int(denominator),
            "ci95": wilson(numerator, denominator)}


def bootstrap_indices(rows, seed=42026, resamples=1000):
    if not rows:
        raise ValueError("empty episode set")
    rng = np.random.default_rng(seed)
    blocks = []
    for case in sorted({r["case"] for r in rows}):
        indices = np.array([i for i, r in enumerate(rows) if r["case"] == case])
        blocks.append(indices[rng.integers(0, len(indices), size=(resamples, len(indices)))])
    return np.concatenate(blocks, axis=1)


def _ci(values):
    finite = np.asarray(values)[np.isfinite(values)]
    return np.percentile(finite, [2.5, 97.5]).tolist() if len(finite) else "N/A"


def binary_metrics(truth, prediction, draws):
    truth, prediction = np.array(truth, dtype=bool), np.array(prediction, dtype=bool)
    tp, fp, fn, tn = truth & prediction, ~truth & prediction, truth & ~prediction, ~truth & ~prediction
    counts = {name: int(values.sum()) for name, values in (("tp", tp), ("fp", fp), ("fn", fn), ("tn", tn))}
    valid = counts["tp"] + counts["fp"] > 0 and counts["tp"] + counts["fn"] > 0
    sampled_tp, sampled_fp, sampled_fn = tp[draws].sum(axis=1), fp[draws].sum(axis=1), fn[draws].sum(axis=1)
    denominator = 2 * sampled_tp + sampled_fp + sampled_fn
    sampled_f1 = np.divide(2 * sampled_tp, denominator, out=np.full(len(draws), np.nan), where=denominator > 0)
    return {**counts, "precision": rate_record(counts["tp"], counts["tp"] + counts["fp"]),
            "recall": rate_record(counts["tp"], counts["tp"] + counts["fn"]),
            "f1": {"value": 2 * counts["tp"] / (2 * counts["tp"] + counts["fp"] + counts["fn"]) if valid else "N/A",
                   "ci95": _ci(sampled_f1) if valid else "N/A"}}


def summarize(rows, resamples=1000):
    draws = bootstrap_indices(rows, resamples=resamples)
    n = len(rows)
    claimed, correct = sum(r["claimed"] for r in rows), sum(r["correct"] for r in rows)
    sulfate = [r for r in rows if r["truth_geology"] == "sulfate"]
    result = {"n": n, "accuracy": rate_record(correct, n),
              "coverage": rate_record(claimed, n), "abstention": rate_record(n - claimed, n),
              "false_conclusion_proportion": rate_record(claimed - correct, claimed),
              "selective_accuracy": rate_record(correct, claimed),
              "supported_discovery_recall": rate_record(sum(r["correct"] for r in sulfate), len(sulfate)),
              "within_budget": rate_record(sum(r["within_budget"] for r in rows), n),
              "initial_fault": binary_metrics([r["initial_fault_truth"] for r in rows],
                                               [r["initial_fault_predicted"] for r in rows], draws),
              "unknown": binary_metrics([r["unknown_truth"] for r in rows],
                                         [r["unknown_predicted"] for r in rows], draws)}
    for key in ("utility", "regret", "energy_used_wh", "time_used_h"):
        values = np.array([r[key] for r in rows])
        result[key] = {"mean": float(values.mean()), "ci95": _ci(values[draws].mean(axis=1))}
    result["fault_brier"] = float(np.mean([(r["initial_fault_probability"] - r["initial_fault_truth"]) ** 2 for r in rows]))
    result["unknown_brier"] = float(np.mean([(r["unknown_probability"] - r["unknown_truth"]) ** 2 for r in rows]))
    latencies = [t for r in rows for t in r["decision_latencies_s"]]
    result["decision_latency"] = {"median_s": float(np.median(latencies)),
                                  "p95_s": float(np.percentile(latencies, 95)),
                                  "calls": len(latencies), "scope": "selection call, includes terminal selection"}
    active = {key: sum(r["active_instrument_time_counts"][key] for r in rows) for key in ("tp", "fp", "tn", "fn")}
    # Repeated instrument-times are clustered inside each resampled episode.
    result["active_instrument_time"] = {**active, "unit": "instrument-time; not independent episodes"}
    for label, numerator_keys, denominator_keys in (
        ("precision", ("tp",), ("tp", "fp")), ("recall", ("tp",), ("tp", "fn"))):
        numerator = sum(active[k] for k in numerator_keys)
        denominator = sum(active[k] for k in denominator_keys)
        per_num = np.array([sum(r["active_instrument_time_counts"][k] for k in numerator_keys) for r in rows])
        per_den = np.array([sum(r["active_instrument_time_counts"][k] for k in denominator_keys) for r in rows])
        sampled_den = per_den[draws].sum(axis=1)
        sampled = np.divide(per_num[draws].sum(axis=1), sampled_den,
                            out=np.full(len(draws), np.nan), where=sampled_den > 0)
        result["active_instrument_time"][label] = {"value": numerator / denominator if denominator else "N/A",
                                                  "ci95": _ci(sampled)}
    result["faults_removed"] = sum(r["faults_removed"] for r in rows)
    return result


def paired(rows, reference="improved_voi", resamples=1000):
    lookup = {(r["case"], r["seed"], r["policy"]): r for r in rows}
    reference_rows = sorted([r for r in rows if r["policy"] == reference], key=lambda r: (r["case"], r["seed"]))
    draws = bootstrap_indices(reference_rows, resamples=resamples)
    output = {}
    for policy in sorted({r["policy"] for r in rows} - {reference}):
        differences = np.array([r["utility"] - lookup[(r["case"], r["seed"], policy)]["utility"] for r in reference_rows])
        output[policy] = {"n_pairs": len(differences), "mean_utility_difference": float(differences.mean()),
                          "ci95": _ci(differences[draws].mean(axis=1))}
    return output
