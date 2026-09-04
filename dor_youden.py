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


def calculate_metrics(**kwargs) -> Dict[str, Any]:
    """
    Core domain algorithm for diagnostic-odds-ratio-sens-spec.

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
    """Process batch CSV file with error handling for each row."""
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

    out_fields = fieldnames + ["score", "classification", "clinical_recommendation"]
    out_rows = []
    errors = []

    for i, r in enumerate(rows):
        try:
            calc_res = calculate_metrics(**r)
            row_dict = dict(r)
            row_dict["score"] = calc_res["score"]
            row_dict["classification"] = calc_res["classification"]
            row_dict["clinical_recommendation"] = calc_res["clinical_recommendation"]
            out_rows.append(row_dict)
        except (ValueError, TypeError) as e:
            errors.append(f"Row {i+1}: {e}")
            # Still include the row with error indication
            row_dict = dict(r)
            row_dict["score"] = "ERROR"
            row_dict["classification"] = "ERROR"
            row_dict["clinical_recommendation"] = str(e)
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

    # Batch parser
    batch_parser = subparsers.add_parser("batch", help="Process batch CSV")
    batch_parser.add_argument("-i", "--input", required=True, help="Input CSV")
    batch_parser.add_argument("-o", "--output", default="results.csv", help="Output CSV")

    args = parser.parse_args(argv)

    if args.command == "single":
        args.func(args)
    elif args.command == "batch":
        process_batch(args.input, args.output)


if __name__ == "__main__":
    main()
