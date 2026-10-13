#!/usr/bin/env python3
"""
Diagnostic Odds Ratio (DOR) & Youden Index Engine
Calculates Sensitivity, Specificity, Positive/Negative Predictive Value, Diagnostic Odds Ratio (DOR), and Youden's J.

Zero-dependency Python implementation with single and batch evaluation.
Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import argparse
import csv
import json
import math
import sys
from typing import Dict, Any, List, Optional


def calculate_diagnostic_metrics(tp: int, fp: int, fn: int, tn: int, alpha: float = 0.05) -> Dict[str, Any]:
    """Calculate real diagnostic 2x2 metrics and confidence intervals.

    Rows are reference disease status; columns are index-test result.
    Returns proportions on the 0–1 scale. For zero cells, DOR uses a
    Haldane–Anscombe correction (0.5 added to all four cells).
    """
    from dor_enrichment import compute_all_metrics_with_ci
    return compute_all_metrics_with_ci(tp, fp, fn, tn, alpha=alpha)


def calculate_metrics(**kwargs) -> Dict[str, Any]:
    """
    Legacy generic weighted-score routine, NOT a diagnostic performance metric.

    For sensitivity, specificity, predictive values and DOR, call
    calculate_diagnostic_metrics(tp=..., fp=..., fn=..., tn=...).

    Parameters
    ----------
    **kwargs : keyword arguments with numeric values (v1, v2, v3, ...)

    Returns
    -------
    dict with score, classification, clinical_recommendation, inputs_evaluated.

    Raises
    ------
    ValueError : if no valid numeric inputs are provided.
    """
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            try:
                params[k] = float(v)
            except (ValueError, TypeError):
                params[k] = str(v)

    # Validate that at least one numeric input is provided
    numeric_vals = [val for val in params.values() if isinstance(val, (int, float))]
    if not numeric_vals:
        raise ValueError("At least one numeric input parameter is required.")

    # Validate numeric ranges (prevent overflow/underflow)
    for val in numeric_vals:
        if not math.isfinite(val):
            raise ValueError(f"Input value {val} is not a finite number.")
        if abs(val) > 1e15:
            raise ValueError(f"Input value {val} exceeds maximum allowed magnitude (1e15).")

    primary_val = numeric_vals[0]

    score = primary_val
    for idx, nv in enumerate(numeric_vals[1:], start=2):
        score += nv * (1.0 / idx)

    rounded_score = round(score, 2)

    # Classification / tiering
    if rounded_score < 10.0:
        tier = "Low / Standard"
        action = "Standard monitoring or negative cutoff"
    elif rounded_score < 25.0:
        tier = "Moderate / Intermediate"
        action = "Close observation or secondary evaluation"
    else:
        tier = "High / Severe"
        action = "Urgent clinical intervention or primary positive finding"

    return {
        "tool": "diagnostic-odds-ratio-sens-spec",
        "score": rounded_score,
        "classification": tier,
        "clinical_recommendation": action,
        "inputs_evaluated": len(params),
    }


def process_single(args) -> None:
    kwargs = vars(args)
    kwargs.pop("func", None)
    res = calculate_metrics(**kwargs)
    print(json.dumps(res, indent=2))


def process_batch(input_csv: str, output_csv: str) -> None:
    """Process TP/FP/FN/TN diagnostic tables or legacy weighted-score rows."""
    import os

    # Validate input file exists
    if not os.path.isfile(input_csv):
        raise FileNotFoundError(f"Input CSV file not found: {input_csv}")

    # Validate input file is not empty
    if os.path.getsize(input_csv) == 0:
        raise ValueError(f"Input CSV file is empty: {input_csv}")

    with open(input_csv, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        if not fieldnames:
            raise ValueError("Input CSV file has no header row.")
        rows = list(reader)

    diagnostic_table = {"tp", "fp", "fn", "tn"}.issubset(fieldnames)
    metric_fields = (
        ["sensitivity", "specificity", "ppv", "npv", "lr_positive",
         "lr_negative", "diagnostic_odds_ratio", "youden_j", "prevalence",
         "dor_zero_cell_correction"]
        if diagnostic_table else ["score", "classification", "clinical_recommendation"]
    )
    out_fields = fieldnames + [name for name in metric_fields if name not in fieldnames] + ["error"]
    out_rows, errors = [], []

    for i, r in enumerate(rows):
        row_dict = dict(r)
        try:
            if diagnostic_table:
                counts = {name: int(r[name]) for name in ("tp", "fp", "fn", "tn")}
                if any(str(r[name]).strip() != str(counts[name]) for name in counts):
                    raise ValueError("Counts must be non-negative whole numbers.")
                calc_res = calculate_diagnostic_metrics(**counts)
            else:
                calc_res = calculate_metrics(**r)
            for name in metric_fields:
                row_dict[name] = calc_res[name]
            row_dict["error"] = ""
        except (ValueError, TypeError, KeyError, OverflowError) as e:
            errors.append(f"Row {i+1}: {e}")
            for name in metric_fields:
                row_dict[name] = ""
            row_dict["error"] = str(e)
        out_rows.append(row_dict)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_csv)
    if output_dir and not os.path.isdir(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Processed {len(out_rows)} records -> {output_csv}")
    if errors:
        print(f"  ⚠ {len(errors)} row(s) had errors (see output for details)")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Diagnostic Odds Ratio (DOR) & Youden Index Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Single parser
    single_parser = subparsers.add_parser("single", help="Evaluate single case")
    single_parser.add_argument("--v1", type=float, default=10.0, help="Primary parameter")
    single_parser.add_argument("--v2", type=float, default=5.0, help="Secondary parameter")
    single_parser.add_argument("--v3", type=float, default=2.0, help="Tertiary parameter")
    single_parser.set_defaults(func=process_single)

    # Diagnostic 2x2 table; keep legacy single mode for backward compatibility.
    table_parser = subparsers.add_parser("table", help="Compute true diagnostic 2x2 statistics")
    for cell in ("tp", "fp", "fn", "tn"):
        table_parser.add_argument(f"--{cell}", type=int, required=True)
    table_parser.add_argument("--alpha", type=float, default=0.05,
                              help="Confidence interval significance level (default 0.05)")

    # Batch parser
    batch_parser = subparsers.add_parser("batch", help="Process batch CSV")
    batch_parser.add_argument("-i", "--input", required=True, help="Input CSV")
    batch_parser.add_argument("-o", "--output", default="results.csv", help="Output CSV")

    args = parser.parse_args(argv)

    if args.command == "single":
        args.func(args)
    elif args.command == "table":
        print(json.dumps(calculate_diagnostic_metrics(
            args.tp, args.fp, args.fn, args.tn, alpha=args.alpha
        ), indent=2, allow_nan=False))
    elif args.command == "batch":
        process_batch(args.input, args.output)


if __name__ == "__main__":
    main()
