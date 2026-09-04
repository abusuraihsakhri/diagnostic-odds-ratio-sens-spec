"""
Tests for Diagnostic Odds Ratio (DOR) & Youden Index Engine.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import math
from dor_youden import calculate_metrics, process_batch


class TestCalculateMetrics:
    """Tests for the calculate_metrics function."""

    def test_basic_calculation(self):
        """Test basic metric calculation with valid inputs."""
        res = calculate_metrics(v1=12.0, v2=4.0)
        assert "score" in res
        assert "classification" in res
        assert "clinical_recommendation" in res
        assert res["score"] > 0
        assert res["tool"] == "diagnostic-odds-ratio-sens-spec"

    def test_single_input(self):
        """Test with a single input parameter."""
        res = calculate_metrics(v1=15.0)
        assert res["score"] == 15.0
        assert res["inputs_evaluated"] == 1

    def test_multiple_inputs(self):
        """Test with multiple input parameters."""
        res = calculate_metrics(v1=10.0, v2=5.0, v3=2.0)
        # score = 10.0 + 5.0/2 + 2.0/3 = 10.0 + 2.5 + 0.667 = 13.167
        assert res["score"] == pytest.approx(13.17, abs=0.01)
        assert res["inputs_evaluated"] == 3

    def test_classification_low(self):
        """Test Low/Standard classification."""
        res = calculate_metrics(v1=5.0)
        assert res["classification"] == "Low / Standard"
        assert "Standard monitoring" in res["clinical_recommendation"]

    def test_classification_moderate(self):
        """Test Moderate/Intermediate classification."""
        res = calculate_metrics(v1=15.0)
        assert res["classification"] == "Moderate / Intermediate"
        assert "Close observation" in res["clinical_recommendation"]

    def test_classification_high(self):
        """Test High/Severe classification."""
        res = calculate_metrics(v1=30.0)
        assert res["classification"] == "High / Severe"
        assert "Urgent clinical intervention" in res["clinical_recommendation"]

    def test_string_input_conversion(self):
        """Test that string inputs are converted to float."""
        res = calculate_metrics(v1="12.5", v2="3.0")
        assert res["score"] == pytest.approx(14.0, abs=0.01)

    def test_no_numeric_input_raises_error(self):
        """Test that ValueError is raised when no numeric inputs are provided."""
        with pytest.raises(ValueError, match="At least one numeric input"):
            calculate_metrics(v1="not_a_number", v2="also_not_a_number")

    def test_inf_input_raises_error(self):
        """Test that ValueError is raised for infinite inputs."""
        with pytest.raises(ValueError, match="not a finite number"):
            calculate_metrics(v1=float("inf"))

    def test_negative_inf_input_raises_error(self):
        """Test that ValueError is raised for negative infinite inputs."""
        with pytest.raises(ValueError, match="not a finite number"):
            calculate_metrics(v1=float("-inf"))

    def test_nan_input_raises_error(self):
        """Test that ValueError is raised for NaN inputs."""
        with pytest.raises(ValueError, match="not a finite number"):
            calculate_metrics(v1=float("nan"))

    def test_extreme_value_raises_error(self):
        """Test that ValueError is raised for extremely large values."""
        with pytest.raises(ValueError, match="exceeds maximum allowed magnitude"):
            calculate_metrics(v1=1e16)

    def test_none_values_ignored(self):
        """Test that None values are ignored."""
        res = calculate_metrics(v1=10.0, v2=None)
        assert res["score"] == 10.0
        assert res["inputs_evaluated"] == 1


class TestProcessBatch:
    """Tests for the process_batch function."""

    def test_batch_processing(self, tmp_path):
        """Test batch CSV processing."""
        csv_in = tmp_path / "in.csv"
        csv_out = tmp_path / "out.csv"
        csv_in.write_text("Patient,v1,v2\nPat_001,15.0,3.0\nPat_002,5.0,1.0\n", encoding="utf-8")

        process_batch(str(csv_in), str(csv_out))
        assert csv_out.exists()
        content = csv_out.read_text(encoding="utf-8")
        assert "Pat_001" in content
        assert "score" in content

    def test_batch_missing_file_raises_error(self, tmp_path):
        """Test that FileNotFoundError is raised for missing input file."""
        with pytest.raises(FileNotFoundError):
            process_batch(str(tmp_path / "nonexistent.csv"), str(tmp_path / "out.csv"))

    def test_batch_empty_file_raises_error(self, tmp_path):
        """Test that ValueError is raised for empty input file."""
        csv_in = tmp_path / "empty.csv"
        csv_in.write_text("", encoding="utf-8")
        with pytest.raises(ValueError, match="empty"):
            process_batch(str(csv_in), str(tmp_path / "out.csv"))

    def test_batch_no_header_processes_first_row_as_header(self, tmp_path):
        """Test that CSV without explicit header uses first row as header (standard CSV behavior)."""
        csv_in = tmp_path / "noheader.csv"
        csv_in.write_text("15.0,3.0\n5.0,1.0\n", encoding="utf-8")
        # Standard CSV behavior: first row becomes header
        # This should not raise an error, but process with first row as field names
        process_batch(str(csv_in), str(tmp_path / "out.csv"))
        assert (tmp_path / "out.csv").exists()
