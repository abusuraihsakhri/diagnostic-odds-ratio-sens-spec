# Diagnostic Odds Ratio Sens Spec

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Reference Guidelines & Standards:** Standard Clinical Formulations & ISO/IEC Quality Frameworks

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

Diagnostic Odds Ratio (DOR) & Youden Index Engine with enrichment features for clinical decision support.

### Core Features

1. **DOR & Youden Index Calculation** - Sensitivity, Specificity, PPV, NPV, DOR, and Youden's J from a 2x2 table
2. **Fagan's LR Integration** - Positive/Negative Likelihood Ratios with post-test probability
3. **Confidence Intervals** - Wilson-score and Clopper-Pearson CIs for all metrics
4. **ROC Curve Analysis** - Full ROC sweep, AUC, multiple cutpoint methods
5. **Cost-Sensitive Threshold** - Find optimal threshold minimizing expected cost

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calculate_metrics()`** - Core scoring algorithm with classification tiers
- **`compute_likelihood_ratios()`** - Compute LR+ and LR- with interpretations
- **`fagan_nomogram()`** - Compute post-test probabilities using Fagan's nomogram
- **`compute_all_metrics_with_ci()`** - Full metrics with confidence intervals
- **`compute_roc_curve()`** - ROC curve with optimal cutpoints
- **`compute_cost_sensitive_cutpoint()`** - Cost-minimizing threshold

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/diagnostic-odds-ratio-sens-spec.git
cd diagnostic-odds-ratio-sens-spec

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🚀 CLI Quickstart & Usage

### 1. Single Case Evaluation
```bash
python dor_youden.py single --v1 12.0 --v2 4.0 --v3 2.0
```

### 2. Batch CSV Processing
```bash
python dor_youden.py batch -i sample.csv -o results.csv
```

### 3. Interactive CLI with Full System
```bash
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2
```

### 4. Batch Processing via CLI
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### 6. Verify Audit Trail
```bash
python cli.py verify-audit
```

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances, Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`)

### Security Configuration

Set the `AUDIT_SECRET_KEY` environment variable for persistent audit integrity across restarts:

```bash
export AUDIT_SECRET_KEY="your-secure-random-key"
```

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

---

## 📁 Project Structure

```
diagnostic-odds-ratio-sens-spec/
├── agents/                 # Enterprise agent framework
│   ├── api.py             # FastAPI REST server
│   ├── base.py            # Security, PHI guard, audit trail
│   ├── models.py          # Pydantic data models
│   ├── supervisor.py      # Multi-agent orchestrator
│   ├── workers.py         # Specialized domain workers
│   ├── llm_factory.py     # LLM provider factory
│   ├── learning.py        # Bayesian calibration engine
│   ├── metrics.py         # Prometheus metrics exporter
│   └── streamer.py        # WebSocket telemetry broadcaster
├── tests/                 # Test suite
├── web/                   # Operations console (HTML)
├── cli.py                 # Command line interface
├── dor_youden.py          # Core DOR & Youden calculations
├── dor_enrichment.py      # Enrichment features (LR, CI, ROC)
├── enrichment.py          # Additional enrichment engines
├── simulator.py           # High-throughput simulation
├── sample.csv             # Sample input data
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container configuration
└── docker-compose.yml     # Multi-container orchestration
```

---

## 📐 Mathematical Formulation

### Diagnostic Odds Ratio (DOR)
```
DOR = (TP × TN) / (FP × FN)
```

### Youden's J
```
J = Sensitivity + Specificity - 1
```

### Likelihood Ratios
```
LR+ = Sensitivity / (1 - Specificity)
LR- = (1 - Sensitivity) / Specificity
```

### Fagan's Nomogram (Post-Test Probability)
```
Pre-test Odds = Pre-test Probability / (1 - Pre-test Probability)
Post-test Odds = Pre-test Odds × LR
Post-test Probability = Post-test Odds / (1 + Post-test Odds)
```
