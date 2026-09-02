# Diagnostic Odds Ratio Sens Spec

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Enrichment Features for Diagnostic Odds Ratio & Youden Index Engine
====================================================================

1. Fagan's LR Integration - Positive/Negative Likelihood Ratios with post-test probability
2. Confidence Intervals for All Metrics - Wilson-score and Clopper-Pearson CIs
3. ROC Curve with Optimal Threshold - Full ROC sweep, AUC, multiple cutpoint methods

Author: Dr. Abu Suraih Sakhri
License: MIT

Diagnostic Odds Ratio (DOR) & Youden Index Engine
Calculates Sensitivity, Specificity, Positive/Negative Predictive Value, Diagnostic Odds Ratio (DOR), and Youden's J.

Zero-dependency Python implementation with single and batch evaluation.
Author: Dr. Abu Suraih Sakhri
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`compute_likelihood_ratios()`**: Compute Positive Likelihood Ratio (LR+) and Negative Likelihood Ratio (LR-).

Parameters
----------
sensitivity : float  (0-1)
specificity : float  (0-1)

Returns
-------
dict with lr_positive, lr_negative, and interpretation strings.
- **`fagan_nomogram()`**: Compute post-test probabilities using Fagan's nomogram.

Parameters
----------
pretest_probability : float  (0-1)
lr_positive : float, optional
lr_negative : float, optional
sensitivity, specificity : float, optional (used to compute LR if not given)

Returns
-------
dict with post_test_positive, post_test_negative, pretest_odds, etc.
- **`compute_all_metrics_with_ci()`**: Compute sensitivity, specificity, PPV, NPV, DOR, Youden's J with CIs.

Parameters
----------
tp, fp, fn, tn : int  (confusion matrix cells)
alpha : significance level (default 0.05 for 95% CI)
ci_method : "wilson" or "clopper-pearson"

Returns
-------
dict with all metrics and their confidence intervals.
- **`compute_roc_curve()`**: Compute full ROC curve by sweeping all thresholds.

Parameters
----------
scores : list of numeric test scores
labels : list of binary labels (matching positive_label for positives)
positive_label : which label value indicates positive class

Returns
-------
dict with thresholds, fpr, tpr, auc, and multiple optimal cutpoints.
- **`compute_cost_sensitive_cutpoint()`**: Find the threshold minimizing expected cost: cost_fn*FN + cost_fp*FP.

Parameters
----------
scores, labels : data
cost_fp : cost of a false positive
cost_fn : cost of a false negative
positive_label : which label is positive

Returns
-------
dict with optimal threshold and associated metrics.

---

## 📐 Mathematical Formulation & Logic

```text
  return (0.0, 0.0)
  return (round(lower, 6), round(upper, 6))
  return (round(lower, 4), round(upper, 4))
  score = primary_val
  rounded_score = round(score, 2)
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --task-id <value> --target <value> --primary <value> --secondary <value>
```

### Parameter Reference
- `--task-id`: Specifies input measurement or parameter value.
- `--target`: Specifies input measurement or parameter value.
- `--primary`: Specifies input measurement or parameter value.
- `--secondary`: Specifies input measurement or parameter value.
- `--critical`: Specifies input measurement or parameter value.
- `--status`: Specifies input measurement or parameter value.
- `--input`: Specifies input measurement or parameter value.
- `--output`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Parameter / observation metric | Required |
| `v1` | Parameter / observation metric | Required |
| `v2` | Parameter / observation metric | Required |
| `v3` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t diagnostic-odds-ratio-sens-spec .
docker run -p 8000:8000 diagnostic-odds-ratio-sens-spec
```
