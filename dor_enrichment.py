#!/usr/bin/env python3
"""
Enrichment Features for Diagnostic Odds Ratio & Youden Index Engine
====================================================================

1. Fagan's LR Integration - Positive/Negative Likelihood Ratios with post-test probability
2. Confidence Intervals for All Metrics - Wilson-score and Clopper-Pearson CIs
3. ROC Curve with Optimal Threshold - Full ROC sweep, AUC, multiple cutpoint methods

Author: Dr. Abu Suraih Sakhri
License: MIT
"""

from __future__ import annotations

import math
from typing import Dict, Any, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Feature 1: Fagan's Likelihood Ratio Integration
# ---------------------------------------------------------------------------

def compute_likelihood_ratios(
    sensitivity: float,
    specificity: float,
) -> Dict[str, Any]:
    """Compute Positive Likelihood Ratio (LR+) and Negative Likelihood Ratio (LR-).

    Parameters
    ----------
    sensitivity : float  (0-1)
    specificity : float  (0-1)

    Returns
    -------
    dict with lr_positive, lr_negative, and interpretation strings.
    """
    if not (0 < sensitivity <= 1) or not (0 < specificity <= 1):
        raise ValueError("Sensitivity and specificity must be in (0, 1].")

    lr_pos = sensitivity / (1.0 - specificity) if specificity < 1.0 else float("inf")
    lr_neg = (1.0 - sensitivity) / specificity if sensitivity < 1.0 else 0.0

    # Interpret LR+
    if lr_pos >= 10:
        lr_pos_interp = "Large shift toward disease (strong rule-in)"
    elif lr_pos >= 5:
        lr_pos_interp = "Moderate shift toward disease"
    elif lr_pos >= 2:
        lr_pos_interp = "Small shift toward disease"
    else:
        lr_pos_interp = "Negligible shift (test not useful for ruling in)"

    # Interpret LR-
    if lr_neg <= 0.1:
        lr_neg_interp = "Large shift away from disease (strong rule-out)"
    elif lr_neg <= 0.2:
        lr_neg_interp = "Moderate shift away from disease"
    elif lr_neg <= 0.5:
        lr_neg_interp = "Small shift away from disease"
    else:
        lr_neg_interp = "Negligible shift (test not useful for ruling out)"

    return {
        "lr_positive": round(lr_pos, 4),
        "lr_negative": round(lr_neg, 4),
        "lr_positive_interpretation": lr_pos_interp,
        "lr_negative_interpretation": lr_neg_interp,
    }


def fagan_nomogram(
    pretest_probability: float,
    lr_positive: Optional[float] = None,
    lr_negative: Optional[float] = None,
    sensitivity: Optional[float] = None,
    specificity: Optional[float] = None,
) -> Dict[str, Any]:
    """Compute post-test probabilities using Fagan's nomogram.

    Parameters
    ----------
    pretest_probability : float  (0-1)
    lr_positive : float, optional
    lr_negative : float, optional
    sensitivity, specificity : float, optional (used to compute LR if not given)

    Returns
    -------
    dict with post_test_positive, post_test_negative, pretest_odds, etc.
    """
    if not (0 < pretest_probability < 1):
        raise ValueError("Pre-test probability must be strictly between 0 and 1.")

    if lr_positive is None or lr_negative is None:
        if sensitivity is None or specificity is None:
            raise ValueError("Provide either LRs or sensitivity+specificity.")
        lrs = compute_likelihood_ratios(sensitivity, specificity)
        if lr_positive is None:
            lr_positive = lrs["lr_positive"]
        if lr_negative is None:
            lr_negative = lrs["lr_negative"]

    pretest_odds = pretest_probability / (1.0 - pretest_probability)
    post_odds_pos = pretest_odds * lr_positive
    post_odds_neg = pretest_odds * lr_negative

    post_prob_pos = post_odds_pos / (1.0 + post_odds_pos) if math.isfinite(post_odds_pos) else 1.0
    post_prob_neg = post_odds_neg / (1.0 + post_odds_neg) if post_odds_neg > 0 else 0.0

    return {
        "pretest_probability": round(pretest_probability, 4),
        "pretest_odds": round(pretest_odds, 4),
        "lr_positive": round(lr_positive, 4),
        "lr_negative": round(lr_negative, 4),
        "post_test_probability_positive": round(post_prob_pos, 4),
        "post_test_probability_negative": round(post_prob_neg, 4),
        "post_odds_positive": round(post_odds_pos, 4),
        "post_odds_negative": round(post_odds_neg, 4),
    }


# ---------------------------------------------------------------------------
# Feature 2: Confidence Intervals for All Metrics
# ---------------------------------------------------------------------------

def _wilson_ci(k: int, n: int, alpha: float = 0.05) -> Tuple[float, float]:
    """Wilson score confidence interval for a binomial proportion.

    Parameters
    ----------
    k : number of successes
    n : total trials
    alpha : significance level (default 0.05 for 95% CI)

    Returns
    -------
    (lower, upper) bounds
    """
    if n == 0:
        return (0.0, 0.0)
    z = 1.959963984540054 if alpha == 0.05 else _z_from_alpha(alpha)
    p_hat = k / n
    denom = 1.0 + z * z / n
    centre = p_hat + z * z / (2.0 * n)
    margin = z * math.sqrt((p_hat * (1.0 - p_hat) + z * z / (4.0 * n)) / n)
    lower = max(0.0, (centre - margin) / denom)
    upper = min(1.0, (centre + margin) / denom)
    return (round(lower, 6), round(upper, 6))


def _clopper_pearson_ci(k: int, n: int, alpha: float = 0.05) -> Tuple[float, float]:
    """Clopper-Pearson exact confidence interval for a binomial proportion.

    Uses the beta distribution relationship with the binomial CDF.
    """
    if n == 0:
        return (0.0, 0.0)
    from scipy.stats import beta as beta_dist
    if k == 0:
        lower = 0.0
    else:
        lower = float(beta_dist.ppf(alpha / 2.0, k, n - k + 1))
    if k == n:
        upper = 1.0
    else:
        upper = float(beta_dist.ppf(1.0 - alpha / 2.0, k + 1, n - k))
    return (round(lower, 6), round(upper, 6))


def _z_from_alpha(alpha: float) -> float:
    """Approximate z critical value from alpha using rational approximation."""
    # Abramowitz & Stegun approximation for the inverse normal CDF
    if alpha <= 0 or alpha >= 1:
        raise ValueError("alpha must be in (0,1)")
    p = 1.0 - alpha / 2.0
    if p < 0.5:
        t = math.sqrt(-2.0 * math.log(p))
    else:
        t = math.sqrt(-2.0 * math.log(1.0 - p))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    z = t - (c0 + c1 * t + c2 * t * t) / (1.0 + d1 * t + d2 * t * t + d3 * t * t * t)
    return z


def _dor_ci(tp: int, fp: int, fn: int, tn: int, alpha: float = 0.05) -> Tuple[float, float]:
    """Confidence interval for the Diagnostic Odds Ratio using the log method.

    SE(ln DOR) = sqrt(1/TP + 1/FP + 1/FN + 1/TN)
    """
    if min(tp, fp, fn, tn) == 0:
        # Haldane-Anscombe correction: add 0.5 to all cells
        tp, fp, fn, tn = tp + 0.5, fp + 0.5, fn + 0.5, tn + 0.5

    dor = (tp * tn) / (fp * fn)
    se_log = math.sqrt(1.0 / tp + 1.0 / fp + 1.0 / fn + 1.0 / tn)
    z = _z_from_alpha(alpha)
    log_dor = math.log(dor)
    lower = math.exp(log_dor - z * se_log)
    upper = math.exp(log_dor + z * se_log)
    return (round(lower, 4), round(upper, 4))


def compute_all_metrics_with_ci(
    tp: int, fp: int, fn: int, tn: int,
    alpha: float = 0.05,
    ci_method: str = "wilson",
) -> Dict[str, Any]:
    """Compute sensitivity, specificity, PPV, NPV, DOR, Youden's J with CIs.

    Parameters
    ----------
    tp, fp, fn, tn : int  (confusion matrix cells)
    alpha : significance level (default 0.05 for 95% CI)
    ci_method : "wilson" or "clopper-pearson"

    Returns
    -------
    dict with all metrics and their confidence intervals.
    """
    cells = {"tp": tp, "fp": fp, "fn": fn, "tn": tn}
    if any(type(v) is not int or v < 0 for v in cells.values()):
        raise ValueError("2x2 counts must be non-negative integers (not booleans).")
    if not (math.isfinite(alpha) and 0 < alpha < 1):
        raise ValueError("alpha must be a finite number strictly between 0 and 1.")
    if ci_method not in {"wilson", "clopper-pearson"}:
        raise ValueError("ci_method must be 'wilson' or 'clopper-pearson'.")
    n_pos = tp + fn
    n_neg = fp + tn
    total = tp + fp + fn + tn
    if n_pos == 0 or n_neg == 0:
        raise ValueError("Both reference-positive and reference-negative groups are required.")

    sens = tp / n_pos if n_pos > 0 else 0.0
    spec = tn / n_neg if n_neg > 0 else 0.0
    ppv = tp / (tp + fp) if (tp + fp) > 0 else None
    npv = tn / (tn + fn) if (tn + fn) > 0 else None

    ci_fn = _wilson_ci if ci_method == "wilson" else _clopper_pearson_ci

    sens_ci = ci_fn(tp, n_pos, alpha)
    spec_ci = ci_fn(tn, n_neg, alpha)
    ppv_ci = ci_fn(tp, tp + fp, alpha) if tp + fp else None
    npv_ci = ci_fn(tn, tn + fn, alpha) if tn + fn else None

    # DOR
    if min(tp, fp, fn, tn) > 0:
        dor = (tp * tn) / (fp * fn)
    else:
        dor = (tp + 0.5) * (tn + 0.5) / ((fp + 0.5) * (fn + 0.5))
    dor_ci = _dor_ci(tp, fp, fn, tn, alpha)

    # Youden's J
    youden_j = sens + spec - 1.0
    # Wald/delta-method approximation for Youden's J (not a bootstrap).
    se_j = math.sqrt(
        (sens * (1.0 - sens) / n_pos if n_pos > 0 else 0) +
        (spec * (1.0 - spec) / n_neg if n_neg > 0 else 0)
    )
    z = _z_from_alpha(alpha)
    youden_ci = (max(-1.0, youden_j - z * se_j), min(1.0, youden_j + z * se_j))

    ci_pct = int(round((1.0 - alpha) * 100))

    return {
        "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "sensitivity": round(sens, 6),
        f"sensitivity_{ci_pct}ci": sens_ci,
        "specificity": round(spec, 6),
        f"specificity_{ci_pct}ci": spec_ci,
        "ppv": round(ppv, 6) if ppv is not None else None,
        f"ppv_{ci_pct}ci": ppv_ci,
        "npv": round(npv, 6) if npv is not None else None,
        f"npv_{ci_pct}ci": npv_ci,
        # Represent infinity as a string for strict JSON compatibility.
        "lr_positive": round(sens / (1 - spec), 6) if spec < 1
            else ("Infinity" if sens > 0 else None),
        "lr_negative": round((1 - sens) / spec, 6) if spec > 0
            else ("Infinity" if sens < 1 else None),
        "diagnostic_odds_ratio": round(dor, 4),
        "dor_zero_cell_correction": min(tp, fp, fn, tn) == 0,
        f"dor_{ci_pct}ci": dor_ci,
        "youden_j": round(youden_j, 6),
        f"youden_j_{ci_pct}ci": (round(youden_ci[0], 6), round(youden_ci[1], 6)),
        "prevalence": round((tp + fn) / total, 6) if total > 0 else 0.0,
        "ci_method": ci_method,
        "alpha": alpha,
    }


# ---------------------------------------------------------------------------
# Feature 3: ROC Curve with Optimal Threshold
# ---------------------------------------------------------------------------

def compute_roc_curve(
    scores: List[float],
    labels: List[int],
    positive_label: int = 1,
) -> Dict[str, Any]:
    """Compute full ROC curve by sweeping all thresholds.

    Parameters
    ----------
    scores : list of numeric test scores
    labels : list of binary labels (matching positive_label for positives)
    positive_label : which label value indicates positive class

    Returns
    -------
    dict with thresholds, fpr, tpr, auc, and multiple optimal cutpoints.
    """
    import numpy as np

    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels)
    if scores.ndim != 1 or labels.ndim != 1 or not len(scores) or len(scores) != len(labels):
        raise ValueError("scores and labels must be equal-length nonempty 1D arrays.")
    if not np.all(np.isfinite(scores)):
        raise ValueError("ROC scores must be finite numbers.")
    pos_mask = labels == positive_label
    neg_mask = ~pos_mask
    n_pos = pos_mask.sum()
    n_neg = neg_mask.sum()

    if n_pos == 0 or n_neg == 0:
        raise ValueError("ROC requires at least one positive and one negative case.")

    # Sort unique thresholds descending
    uniq = np.unique(scores)[::-1]
    thresholds = np.concatenate(([np.inf], uniq))

    tpr_arr = np.empty(len(thresholds))
    fpr_arr = np.empty(len(thresholds))
    for i, t in enumerate(thresholds):
        pred_pos = scores >= t
        tpr_arr[i] = np.count_nonzero(pred_pos & pos_mask) / n_pos
        fpr_arr[i] = np.count_nonzero(pred_pos & neg_mask) / n_neg

    # AUC via trapezoidal rule
    _trapz = getattr(np, "trapezoid", None) or np.trapz
    order = np.argsort(fpr_arr, kind="mergesort")
    auc = float(_trapz(tpr_arr[order], fpr_arr[order]))

    sens = tpr_arr
    spec = 1.0 - fpr_arr

    # Method 1: Youden's J
    j = sens + spec - 1.0
    finite_mask = np.isfinite(thresholds)
    idx_fin = np.where(finite_mask)[0]
    youden_idx = idx_fin[np.argmax(j[idx_fin])]
    youden_cutpoint = {
        "method": "youden",
        "threshold": float(thresholds[youden_idx]),
        "sensitivity": float(sens[youden_idx]),
        "specificity": float(spec[youden_idx]),
        "youden_j": float(j[youden_idx]),
    }

    # Method 2: Closest to (0, 1) corner
    dist = np.sqrt(fpr_arr ** 2 + (1.0 - tpr_arr) ** 2)
    corner_idx = idx_fin[np.argmin(dist[idx_fin])]
    corner_cutpoint = {
        "method": "closest_to_corner",
        "threshold": float(thresholds[corner_idx]),
        "sensitivity": float(sens[corner_idx]),
        "specificity": float(spec[corner_idx]),
        "distance": float(dist[corner_idx]),
    }

    # Method 3: Maximum efficiency (balanced accuracy)
    balanced_acc = (sens + spec) / 2.0
    eff_idx = idx_fin[np.argmax(balanced_acc[idx_fin])]
    efficiency_cutpoint = {
        "method": "max_efficiency",
        "threshold": float(thresholds[eff_idx]),
        "sensitivity": float(sens[eff_idx]),
        "specificity": float(spec[eff_idx]),
        "balanced_accuracy": float(balanced_acc[eff_idx]),
    }

    return {
        "n_positive": int(n_pos),
        "n_negative": int(n_neg),
        "auc": round(auc, 6),
        "thresholds": [float(t) if math.isfinite(t) else None for t in thresholds],
        "fpr": [round(float(v), 6) for v in fpr_arr],
        "tpr": [round(float(v), 6) for v in tpr_arr],
        "optimal_cutpoints": {
            "youden": youden_cutpoint,
            "closest_to_corner": corner_cutpoint,
            "max_efficiency": efficiency_cutpoint,
        },
    }


def compute_cost_sensitive_cutpoint(
    scores: List[float],
    labels: List[int],
    cost_fp: float = 1.0,
    cost_fn: float = 1.0,
    positive_label: int = 1,
) -> Dict[str, Any]:
    """Find the threshold minimizing expected cost: cost_fn*FN + cost_fp*FP.

    Parameters
    ----------
    scores, labels : data
    cost_fp : cost of a false positive
    cost_fn : cost of a false negative
    positive_label : which label is positive

    Returns
    -------
    dict with optimal threshold and associated metrics.
    """
    import numpy as np

    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels)
    if scores.ndim != 1 or labels.ndim != 1 or not len(scores) or len(scores) != len(labels):
        raise ValueError("scores and labels must be equal-length nonempty 1D arrays.")
    if not np.all(np.isfinite(scores)):
        raise ValueError("Threshold scores must be finite numbers.")
    if not (math.isfinite(cost_fp) and math.isfinite(cost_fn) and cost_fp >= 0 and cost_fn >= 0):
        raise ValueError("False-positive and false-negative costs must be finite and non-negative.")
    pos_mask = labels == positive_label
    neg_mask = ~pos_mask
    n_pos = pos_mask.sum()
    n_neg = neg_mask.sum()
    if n_pos == 0 or n_neg == 0:
        raise ValueError("Threshold selection requires both positive and negative cases.")

    uniq = np.unique(scores)[::-1]
    thresholds = np.concatenate(([np.inf], uniq))

    best_cost = float("inf")
    best_result = {}

    for t in thresholds:
        pred_pos = scores >= t
        fn = int(n_pos - np.count_nonzero(pred_pos & pos_mask))
        fp = int(np.count_nonzero(pred_pos & neg_mask))
        cost = cost_fn * fn + cost_fp * fp
        if cost < best_cost:
            best_cost = cost
            tp = int(n_pos - fn)
            tn = int(n_neg - fp)
            best_result = {
                "threshold": float(t) if math.isfinite(t) else None,
                "sensitivity": round(tp / n_pos, 6) if n_pos > 0 else 0.0,
                "specificity": round(tn / n_neg, 6) if n_neg > 0 else 0.0,
                "false_positives": fp,
                "false_negatives": fn,
                "total_cost": round(cost, 2),
                "cost_fp": cost_fp,
                "cost_fn": cost_fn,
            }

    return best_result


# ---------------------------------------------------------------------------
# Self-test / demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Demo: 2x2 table
    print("=" * 60)
    print("Feature 1: Fagan's LR Integration")
    print("=" * 60)
    lr = compute_likelihood_ratios(0.95, 0.90)
    print(f"  LR+ = {lr['lr_positive']}, LR- = {lr['lr_negative']}")
    print(f"  LR+ interpretation: {lr['lr_positive_interpretation']}")

    fagan = fagan_nomogram(pretest_probability=0.20, sensitivity=0.95, specificity=0.90)
    print(f"  Pre-test prob: {fagan['pretest_probability']}")
    print(f"  Post-test prob (positive): {fagan['post_test_probability_positive']}")
    print(f"  Post-test prob (negative): {fagan['post_test_probability_negative']}")

    print()
    print("=" * 60)
    print("Feature 2: Confidence Intervals for All Metrics")
    print("=" * 60)
    result = compute_all_metrics_with_ci(tp=95, fp=10, fn=5, tn=90, ci_method="wilson")
    for k, v in result.items():
        print(f"  {k}: {v}")

    print()
    print("=" * 60)
    print("Feature 3: ROC Curve with Optimal Threshold")
    print("=" * 60)
    import random
    random.seed(42)
    scores = [random.gauss(5, 1) for _ in range(50)] + [random.gauss(3, 1) for _ in range(50)]
    labels = [1] * 50 + [0] * 50
    roc = compute_roc_curve(scores, labels)
    print(f"  AUC: {roc['auc']}")
    for method, cutpoint in roc['optimal_cutpoints'].items():
        print(f"  {method}: threshold={cutpoint['threshold']:.3f}, "
              f"sens={cutpoint['sensitivity']:.3f}, spec={cutpoint['specificity']:.3f}")
