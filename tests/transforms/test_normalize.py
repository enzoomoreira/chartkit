"""Tests for chartkit.transforms.temporal.normalize.

Covers: base value correctness, base_date (exact/nearest), config default,
multi-column, validation (zero/NaN), edge cases.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms.temporal import normalize


class TestNormalizeKnownValues:
    def test_basic_normalize_base_100(self, known_normalize_data: pd.DataFrame) -> None:
        """[50, 100, 150, 200] base=100 -> [100, 200, 300, 400]."""
        result = normalize(known_normalize_data, base=100)
        expected = [100.0, 200.0, 300.0, 400.0]
        for i, exp in enumerate(expected):
            assert result["val"].iloc[i] == pytest.approx(exp)

    def test_custom_base_1(self, known_normalize_data: pd.DataFrame) -> None:
        """base=1 scales first value to 1.0."""
        result = normalize(known_normalize_data, base=1)
        assert result["val"].iloc[0] == pytest.approx(1.0)
        assert result["val"].iloc[1] == pytest.approx(2.0)

    def test_default_base_from_config(
        self, known_normalize_data: pd.DataFrame, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When base=None, uses config.transforms.normalize_base."""
        mock_config = MagicMock()
        mock_config.transforms.normalize_base = 1000
        monkeypatch.setattr(
            "chartkit.transforms.temporal.get_config", lambda: mock_config
        )
        result = normalize(known_normalize_data)
        assert result["val"].iloc[0] == pytest.approx(1000.0)
        assert result["val"].iloc[1] == pytest.approx(2000.0)


class TestNormalizeBaseDate:
    def test_base_date_exact_match(self) -> None:
        """Exact date in index uses that value as reference."""
        idx = pd.date_range("2023-01-31", periods=4, freq="ME")
        df = pd.DataFrame({"val": [50.0, 100.0, 150.0, 200.0]}, index=idx)
        result = normalize(df, base=100, base_date="2023-02-28")
        assert result["val"].iloc[0] == pytest.approx(50.0)
        assert result["val"].iloc[1] == pytest.approx(100.0)

    def test_base_date_nearest_match(self) -> None:
        """Date not in index snaps to nearest available date."""
        idx = pd.date_range("2023-01-31", periods=4, freq="ME")
        df = pd.DataFrame({"val": [50.0, 100.0, 150.0, 200.0]}, index=idx)
        result = normalize(df, base=100, base_date="2023-02-15")
        assert result["val"].iloc[1] == pytest.approx(100.0)

    def test_invalid_base_date_raises(self, monthly_rates: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="Invalid base_date"):
            normalize(monthly_rates, base_date="not-a-date")


class TestNormalizeMultiColumn:
    def test_multi_column_independent_bases(self) -> None:
        """Each column normalizes to its own first non-NaN value."""
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame(
            {"a": [10.0, 20.0, 30.0], "b": [200.0, 400.0, 600.0]}, index=idx
        )
        result = normalize(df, base=100)
        assert result["a"].iloc[0] == pytest.approx(100.0)
        assert result["b"].iloc[0] == pytest.approx(100.0)
        assert result["a"].iloc[1] == pytest.approx(200.0)
        assert result["b"].iloc[1] == pytest.approx(200.0)

    def test_mixed_dtypes_drops_non_numeric(
        self, multi_series_monthly: pd.DataFrame
    ) -> None:
        result = normalize(multi_series_monthly, base=100)
        assert "category" not in result.columns


class TestNormalizeValidation:
    def test_zero_base_value_raises(self) -> None:
        """First value=0 makes division impossible."""
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"val": [0.0, 100.0, 200.0]}, index=idx)
        with pytest.raises(TransformError, match="zero"):
            normalize(df, base=100)

    def test_all_nan_series_raises(self, all_nan_series: pd.Series) -> None:
        with pytest.raises(TransformError, match="NaN"):
            normalize(all_nan_series, base=100)

    def test_df_with_zero_column_raises(self) -> None:
        """DataFrame where one column starts at zero raises."""
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame(
            {"ok": [10.0, 20.0, 30.0], "bad": [0.0, 5.0, 10.0]}, index=idx
        )
        with pytest.raises(TransformError, match="zero or NaN"):
            normalize(df, base=100)


class TestNormalizeEdgeCases:
    def test_inf_sanitized(self) -> None:
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"val": [1.0, np.inf, 3.0]}, index=idx)
        result = normalize(df, base=100)
        assert np.isnan(result["val"].iloc[1])

    def test_single_value_normalizes_to_base(self) -> None:
        idx = pd.date_range("2023-01-31", periods=1, freq="ME")
        df = pd.DataFrame({"val": [50.0]}, index=idx)
        result = normalize(df, base=100)
        assert result["val"].iloc[0] == pytest.approx(100.0)
