from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms.temporal import normalize


class TestNormalizeCorrectness:
    def test_basic_normalize(self, known_normalize_data: pd.DataFrame) -> None:
        result = normalize(known_normalize_data, base=100)
        expected = [100.0, 200.0, 300.0, 400.0]
        for i, exp in enumerate(expected):
            assert result["val"].iloc[i] == pytest.approx(exp)

    def test_default_base_from_config(
        self, known_normalize_data: pd.DataFrame, monkeypatch
    ) -> None:
        from unittest.mock import MagicMock

        mock_config = MagicMock()
        mock_config.transforms.normalize_base = 1000
        monkeypatch.setattr(
            "chartkit.transforms.temporal.get_config", lambda: mock_config
        )
        result = normalize(known_normalize_data)
        # base=1000, first value=50 -> [1000, 2000, 3000, 4000]
        assert result["val"].iloc[0] == pytest.approx(1000.0)
        assert result["val"].iloc[1] == pytest.approx(2000.0)

    def test_custom_base(self, known_normalize_data: pd.DataFrame) -> None:
        result = normalize(known_normalize_data, base=1)
        assert result["val"].iloc[0] == pytest.approx(1.0)
        assert result["val"].iloc[1] == pytest.approx(2.0)


class TestNormalizeBaseDate:
    def test_base_date_exact_match(self) -> None:
        idx = pd.date_range("2023-01-31", periods=4, freq="ME")
        df = pd.DataFrame({"val": [50.0, 100.0, 150.0, 200.0]}, index=idx)
        result = normalize(df, base=100, base_date="2023-02-28")
        # Base value is 100 at index 1 -> [50, 100, 150, 200]
        assert result["val"].iloc[0] == pytest.approx(50.0)
        assert result["val"].iloc[1] == pytest.approx(100.0)

    def test_base_date_nearest_match(self) -> None:
        idx = pd.date_range("2023-01-31", periods=4, freq="ME")
        df = pd.DataFrame({"val": [50.0, 100.0, 150.0, 200.0]}, index=idx)
        # 2023-02-15 is between Jan 31 and Feb 28, nearest is Feb 28
        result = normalize(df, base=100, base_date="2023-02-15")
        assert result["val"].iloc[1] == pytest.approx(100.0)

    def test_invalid_base_date_raises(self, monthly_rates: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="Invalid base_date"):
            normalize(monthly_rates, base_date="not-a-date")


class TestNormalizeValidation:
    def test_zero_base_value_raises(self) -> None:
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"val": [0.0, 100.0, 200.0]}, index=idx)
        with pytest.raises(TransformError, match="zero"):
            normalize(df, base=100)

    def test_all_nan_raises(self, all_nan_series: pd.Series) -> None:
        with pytest.raises(TransformError, match="NaN"):
            normalize(all_nan_series, base=100)

    def test_df_zero_base_column_raises(self) -> None:
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame(
            {"ok": [10.0, 20.0, 30.0], "bad": [0.0, 5.0, 10.0]}, index=idx
        )
        with pytest.raises(TransformError, match="zero or NaN"):
            normalize(df, base=100)


class TestNormalizeInputTypes:
    def test_accepts_series(self, single_series: pd.Series) -> None:
        result = normalize(single_series, base=100)
        assert isinstance(result, pd.Series)

    def test_accepts_dataframe(self, monthly_rates: pd.DataFrame) -> None:
        result = normalize(monthly_rates, base=100)
        assert isinstance(result, pd.DataFrame)


class TestNormalizeEdgeCases:
    def test_empty_raises(self, empty_df: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="empty"):
            normalize(empty_df, base=100)

    def test_inf_sanitized(self) -> None:
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"val": [1.0, np.inf, 3.0]}, index=idx)
        result = normalize(df, base=100)
        # inf/1.0 * 100 = inf -> sanitized to NaN
        assert np.isnan(result["val"].iloc[1])

    def test_single_value(self) -> None:
        idx = pd.date_range("2023-01-31", periods=1, freq="ME")
        df = pd.DataFrame({"val": [50.0]}, index=idx)
        result = normalize(df, base=100)
        assert result["val"].iloc[0] == pytest.approx(100.0)

    def test_mixed_dtypes_filtered(self, multi_series_monthly: pd.DataFrame) -> None:
        result = normalize(multi_series_monthly, base=100)
        assert "category" not in result.columns
