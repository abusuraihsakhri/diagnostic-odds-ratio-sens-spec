"""
Tests for Diagnostic Odds Ratio Enrichment Features.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import math

# Check if scipy is available
try:
    import scipy.stats  # noqa: F401
    SCIPY_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    SCIPY_AVAILABLE = False

from dor_enrichment import (
    compute_likelihood_ratios,
    fagan_nomogram,
    compute_all_metrics_with_ci,
    _wilson_ci,
    _z_from_alpha,
)


class TestLikelihoodRatios:
    """Tests for compute_likelihood_ratios function."""

    def test_basic_lr_calculation(self):
        """Test basic likelihood ratio calculation."""
        result = compute_likelihood_ratios(sensitivity=0.95, specificity=0.90)
        assert "lr_positive" in result
        assert "lr_negative" in result
        # LR+ = 0.95 / (1 - 0.90) = 9.5
        assert result["lr_positive"] == pytest.approx(9.5, abs=0.01)
        # LR- = (1 - 0.95) / 0.90 = 0.056
        assert result["lr_negative"] == pytest.approx(0.056, abs=0.01)

    def test_perfect_sensitivity(self):
        """Test with perfect sensitivity (1.0)."""
        result = compute_likelihood_ratios(sensitivity=1.0, specificity=0.90)
        # LR- should be 0 when sensitivity is 1.0
        assert result["lr_negative"] == 0.0

    def test_perfect_specificity(self):
        """Test with perfect specificity (1.0)."""
        result = compute_likelihood_ratios(sensitivity=0.95, specificity=1.0)
        # LR+ should be inf when specificity is 1.0
        assert result["lr_positive"] == float("inf")

    def test_invalid_sensitivity_raises_error(self):
        """Test that ValueError is raised for invalid sensitivity."""
        with pytest.raises(ValueError):
            compute_likelihood_ratios(sensitivity=0.0, specificity=0.90)

    def test_invalid_specificity_raises_error(self):
        """Test that ValueError is raised for invalid specificity."""
        with pytest.raises(ValueError):
            compute_likelihood_ratios(sensitivity=0.95, specificity=0.0)

    def test_out_of_range_sensitivity_raises_error(self):
        """Test that ValueError is raised for sensitivity > 1."""
        with pytest.raises(ValueError):
            compute_likelihood_ratios(sensitivity=1.5, specificity=0.90)


class TestFaganNomogram:
    """Tests for fagan_nomogram function."""

    def test_basic_fagan_calculation(self):
        """Test basic Fagan nomogram calculation."""
        result = fagan_nomogram(pretest_probability=0.20, sensitivity=0.95, specificity=0.90)
        assert "post_test_probability_positive" in result
        assert "post_test_probability_negative" in result
        assert result["pretest_probability"] == 0.20

    def test_fagan_with_lr(self):
        """Test Fagan nomogram with pre-computed LRs."""
        result = fagan_nomogram(pretest_probability=0.20, lr_positive=10.0, lr_negative=0.1)
        assert result["post_test_probability_positive"] > result["pretest_probability"]
        assert result["post_test_probability_negative"] < result["pretest_probability"]

    def test_invalid_pretest_probability_raises_error(self):
        """Test that ValueError is raised for invalid pretest probability."""
        with pytest.raises(ValueError):
            fagan_nomogram(pretest_probability=0.0, sensitivity=0.95, specificity=0.90)

    def test_missing_parameters_raises_error(self):
        """Test that ValueError is raised when neither LRs nor sens/spec provided."""
        with pytest.raises(ValueError):
            fagan_nomogram(pretest_probability=0.20)


class TestConfidenceIntervals:
    """Tests for confidence interval functions."""

    def test_wilson_ci_basic(self):
        """Test Wilson score confidence interval."""
        lower, upper = _wilson_ci(50, 100)
        assert 0 <= lower <= upper <= 1
        # For 50/100, CI should be around 0.5
        assert lower < 0.5 < upper

    def test_wilson_ci_zero_trials(self):
        """Test Wilson CI with zero trials."""
        lower, upper = _wilson_ci(0, 0)
        assert lower == 0.0
        assert upper == 0.0

    def test_z_from_alpha_005(self):
        """Test z-score calculation for alpha=0.05."""
        z = _z_from_alpha(0.05)
        # z should be approximately 1.96 for alpha=0.05
        assert z == pytest.approx(1.96, abs=0.01)

    def test_z_from_alpha_invalid(self):
        """Test that ValueError is raised for invalid alpha."""
        with pytest.raises(ValueError):
            _z_from_alpha(0.0)
        with pytest.raises(ValueError):
            _z_from_alpha(1.0)


class TestComputeAllMetricsWithCI:
    """Tests for compute_all_metrics_with_ci function."""

    def test_basic_metrics(self):
        """Test basic metrics calculation."""
        result = compute_all_metrics_with_ci(tp=95, fp=10, fn=5, tn=90)
        assert result["sensitivity"] == pytest.approx(0.95, abs=0.01)
        assert result["specificity"] == pytest.approx(0.90, abs=0.01)
        assert "sensitivity_95ci" in result
        assert "specificity_95ci" in result

    def test_dor_calculation(self):
        """Test Diagnostic Odds Ratio calculation."""
        result = compute_all_metrics_with_ci(tp=95, fp=10, fn=5, tn=90)
        # DOR = (95 * 90) / (10 * 5) = 8550 / 50 = 171
        assert result["diagnostic_odds_ratio"] == pytest.approx(171.0, abs=0.1)

    def test_youden_j_calculation(self):
        """Test Youden's J calculation."""
        result = compute_all_metrics_with_ci(tp=95, fp=10, fn=5, tn=90)
        # Youden J = sens + spec - 1 = 0.95 + 0.90 - 1 = 0.85
        assert result["youden_j"] == pytest.approx(0.85, abs=0.01)

    def test_zero_cells_haldane_correction(self):
        """Test Haldane-Anscombe correction for zero cells."""
        result = compute_all_metrics_with_ci(tp=0, fp=10, fn=5, tn=90)
        # Should not raise error due to Haldane-Anscombe correction
        assert "diagnostic_odds_ratio" in result

    @pytest.mark.skipif(not SCIPY_AVAILABLE, reason="scipy not available")
    def test_clopper_pearson_method(self):
        """Test Clopper-Pearson CI method."""
        result = compute_all_metrics_with_ci(tp=95, fp=10, fn=5, tn=90, ci_method="clopper-pearson")
        assert result["ci_method"] == "clopper-pearson"
        assert "sensitivity_95ci" in result
