# Diagnostic Test Performance Calculator

### [Open the Live Application →](https://abusuraihsakhri.github.io/diagnostic-odds-ratio-sens-spec/)

Calculate diagnostic test performance from a **2×2 reference-standard table**. The public application is a dependency-free static website; Python functions, a CLI, and an optional FastAPI service are also provided.

## Browser calculator

Enter true positives (TP), false positives (FP), false negatives (FN), and true negatives (TN). All counts must be non-negative integers, and both reference-positive and reference-negative observations must be present.

- **Sensitivity, specificity, PPV, NPV, and observed prevalence**, with Wilson-score 95% confidence intervals for the four accuracy proportions.
- **Diagnostic odds ratio (DOR)** and log-normal 95% CI; adds 0.5 to each cell when any cell is zero, with the correction explicitly identified.
- **Positive/negative likelihood ratios (LR+/LR−)** and **Youden's J**.
- **Post-test probability** after positive and negative tests from a user-supplied pre-test probability.
- **CSV export**, input validation, and responsive layout.

An estimate that is mathematically undefined is displayed as such; it is not silently interpreted as zero.

**Privacy:** The browser calculator performs all computations locally. It does not upload input counts or require an account, cookie, API key, analytics provider, or remote service. Do not enter identifiable patient data. Exported CSVs are generated and downloaded by the browser.

## Methods

For the confusion matrix (TP, FP, FN, TN):

```text
Sensitivity = TP / (TP + FN)
Specificity = TN / (TN + FP)
PPV         = TP / (TP + FP)
NPV         = TN / (TN + FN)
DOR         = (TP × TN) / (FP × FN)
Youden J    = Sensitivity + Specificity − 1
LR+         = Sensitivity / (1 − Specificity)
LR−         = (1 − Sensitivity) / Specificity
```

PPV and NPV are sample-prevalence dependent. Post-test probabilities instead apply the likelihood ratios to the **specified pre-test probability**. The Youden J confidence interval in the Python enrichment module is an approximate delta-method interval; it is not a bootstrap interval. The DOR log-normal interval may be unreliable for sparse tables, and the zero-cell correction is a convention rather than an exact estimate.

This software provides descriptive research calculations, **not clinical recommendations or a validated clinical decision rule**.

## Python installation and examples

Python 3.10–3.12 is tested.

```bash
git clone https://github.com/abusuraihsakhri/diagnostic-odds-ratio-sens-spec.git
cd diagnostic-odds-ratio-sens-spec
python -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Calculate an individual 2×2 table:

```bash
python dor_youden.py table --tp 95 --fp 10 --fn 5 --tn 90
```

Process `example_2x2.csv` and save calculated metrics:

```bash
python dor_youden.py batch -i example_2x2.csv -o results.csv
```

The batch command recognizes the exact column names `tp,fp,fn,tn`. Invalid rows receive an `error` field. The historical `single --v1 --v2 --v3` mode and `sample.csv` remain available for compatibility but are a **generic weighted-score demonstration, not diagnostic statistics**.

The `dor_enrichment.py` module additionally exposes `compute_all_metrics_with_ci()`, `compute_likelihood_ratios()`, `fagan_nomogram()`, `compute_roc_curve()`, and `compute_cost_sensitive_cutpoint()`; the confidence-interval helper supports Wilson and Clopper–Pearson methods (the latter uses SciPy).

## Local application and API

To run only the web interface, serve the `web` directory with any static file server:

```bash
python -m http.server 8080 --directory web
```

Open [http://localhost:8080/](http://localhost:8080/).

To run the Python REST service, including the same browser UI:

```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`. The API offers `POST /api/diagnostic-metrics` with JSON `{"tp":95,"fp":10,"fn":5,"tn":90}`; `GET /health`, `GET /metrics`, and FastAPI's generated `GET /openapi.json` are also available. The `/metrics` endpoint returns JSON operational counts, **not Prometheus exposition format**.

The separate `cli.py audit` and `/api/audit` workflows demonstrate **illustrative, unvalidated threshold rules**; they do not evaluate the diagnostic 2×2 table. The conversational adapter is a **mock**: external model providers are not implemented. Its in-memory HMAC audit ledger is ephemeral, and regex identifier screening is incomplete; neither is a compliance guarantee. Do not process PHI through this service.

## Docker

```bash
docker build -t diagnostic-performance .
docker run --rm -p 127.0.0.1:8000:8000 -e AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')" diagnostic-performance
```

Alternatively set `AUDIT_SECRET_KEY` to a strong value in your environment and run `docker compose up --build`. The Compose file deliberately requires this variable and binds the server to localhost. Historical test keys should not be reused.

## Tests and deployment

```bash
python -m pytest -q
node --check web/metrics.js
node --check web/app.js
node --test web/tests.test.cjs
```

GitHub Actions tests Python 3.10, 3.11 and 3.12, checks the browser scripts, and deploys `web/` to GitHub Pages from `master`. The deployment workflow verifies the live HTML and JavaScript files after publication. The browser JavaScript runs natively; **Pyodide/PyScript are not required**.

The static interface uses modern browser features such as `Number.isSafeInteger`, `Blob`, and `requestSubmit`; it is intended for current desktop and mobile browsers. Automated tests do not constitute cross-browser certification.

## License

[MIT](LICENSE).
