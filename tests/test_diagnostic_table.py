"""Clinically interpretable 2x2 calculations and input-validation regression tests."""
import math
import pytest
from fastapi.testclient import TestClient

from dor_youden import calculate_diagnostic_metrics, main
from dor_enrichment import compute_all_metrics_with_ci, compute_roc_curve, compute_cost_sensitive_cutpoint
from agents.api import app


def test_standard_table():
    result = calculate_diagnostic_metrics(tp=95, fp=10, fn=5, tn=90)
    assert result["sensitivity"] == 0.95
    assert result["specificity"] == 0.9
    assert result["ppv"] == pytest.approx(95 / 105)
    assert result["npv"] == pytest.approx(90 / 95)
    assert result["diagnostic_odds_ratio"] == 171
    assert result["youden_j"] == pytest.approx(0.85)
    assert result["dor_zero_cell_correction"] is False


def test_zero_cell_correction_identified():
    result = calculate_diagnostic_metrics(tp=10, fp=0, fn=2, tn=18)
    assert result["dor_zero_cell_correction"] is True
    assert math.isfinite(result["diagnostic_odds_ratio"])


def test_undefined_predictive_value_returned_as_null():
    result = calculate_diagnostic_metrics(tp=0, fp=0, fn=10, tn=20)
    assert result["ppv"] is None
    assert result["ppv_95ci"] is None


@pytest.mark.parametrize("counts", [
    (-1, 2, 3, 4), (1.5, 2, 3, 4), (True, 2, 3, 4),
    (0, 0, 0, 0), (1, 0, 1, 0), (0, 1, 0, 1),
])
def test_invalid_tables(counts):
    with pytest.raises(ValueError):
        calculate_diagnostic_metrics(*counts)


def test_invalid_confidence_options():
    with pytest.raises(ValueError):
        compute_all_metrics_with_ci(10, 2, 3, 15, alpha=0)
    with pytest.raises(ValueError):
        compute_all_metrics_with_ci(10, 2, 3, 15, ci_method="unknown")


def test_roc_rejects_bad_samples():
    with pytest.raises(ValueError):
        compute_roc_curve([0.1, float("nan")], [0, 1])
    with pytest.raises(ValueError):
        compute_roc_curve([0.1], [1, 0])


def test_cost_rejects_invalid_values():
    with pytest.raises(ValueError):
        compute_cost_sensitive_cutpoint([0.1, 0.8], [0, 1], cost_fp=-1)


def test_cli_table(capsys):
    main(["table", "--tp", "95", "--fp", "10", "--fn", "5", "--tn", "90"])
    assert '"diagnostic_odds_ratio": 171' in capsys.readouterr().out


def test_http_diagnostics_and_validation():
    client = TestClient(app)
    response = client.post("/api/diagnostic-metrics",
                           json={"tp": 95, "fp": 10, "fn": 5, "tn": 90})
    assert response.status_code == 200
    assert response.json()["diagnostic_odds_ratio"] == 171
    assert client.post("/api/diagnostic-metrics",
                       json={"tp": -1, "fp": 10, "fn": 5, "tn": 90}).status_code == 422
    assert client.post("/api/diagnostic-metrics",
                       json={"tp": 0, "fp": 10, "fn": 0, "tn": 90}).status_code == 422


def test_api_rejects_detectable_phi():
    client = TestClient(app)
    response = client.post("/api/audit", json={
        "task_id": "example", "target_identifier": "John Doe",
        "primary_metric": 1.0
    })
    assert response.status_code == 422
