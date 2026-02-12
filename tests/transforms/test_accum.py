from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms.temporal import accum


class TestAccumCorrectness:
    def test_known_compound_product(self, known_accum_data: pd.DataFrame) -> None:
        result = accum(known_accum_data, window=3)
        # (1.01 * 1.02 * 1.03 - 1) * 100 = 6.1106%
        expected = (1.01 * 1.02 * 1.03 - 1) * 100
        assert result["rate"].iloc[-1] == pytest.approx(expected, rel=1e-6)

    def test_window_2(self) -> None:
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"rate": [1.0, 2.0, 3.0]}, index=idx)
        result = accum(df, window=2)
        # Window=2 at index 1: (1.01 * 1.02 - 1) * 100
        expected = (1.01 * 1.02 - 1) * 100
        assert result["rate"].iloc[1] == pytest.approx(expected, rel=1e-6)


class TestAccumFreqResolution:
    def test_explicit_window(self, monthly_rates: pd.DataFrame) -> None:
        result = accum(monthly_rates, window=6)
        # First 5 should be NaN (min_periods=6)
        assert result["cdi"].iloc[:5].isna().all()
        assert not np.isnan(result["cdi"].iloc[5])

    def test_explicit_freq(self, monthly_rates: pd.DataFrame) -> None:
        result = accum(monthly_rates, freq="M")
        # freq="M" -> accum -> 12 periods
        assert result["cdi"].iloc[:11].isna().all()

    def test_auto_detect(self, monthly_rates: pd.DataFrame) -> None:
        result = accum(monthly_rates)
        # Auto-detect monthly -> accum=12
        assert result["cdi"].iloc[:11].isna().all()

    def test_fallback_to_config_accum_window(self, monkeypatch) -> None:
        from unittest.mock import MagicMock

        mock_config = MagicMock()
        mock_config.transforms.accum_window = 3
        monkeypatch.setattr(
            "chartkit.transforms.temporal.get_config", lambda: mock_config
        )
        df = pd.DataFrame({"rate": [1.0, 2.0, 3.0, 4.0, 5.0]})
        result = accum(df)
        # Should use window=3 from config fallback
        assert result["rate"].iloc[:2].isna().all()
        assert not np.isnan(result["rate"].iloc[2])


class TestAccumInputTypes:
    def test_accepts_series(self, single_series: pd.Series) -> None:
        result = accum(single_series, window=3)
        assert isinstance(result, pd.Series)

    def test_accepts_dataframe(self, monthly_rates: pd.DataFrame) -> None:
        result = accum(monthly_rates, window=3)
        assert isinstance(result, pd.DataFrame)


class TestAccumEdgeCases:
    def test_empty_raises(self, empty_df: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="empty"):
            accum(empty_df, window=3)

    def test_single_row_all_nan(self) -> None:
        idx = pd.date_range("2023-01-31", periods=1, freq="ME")
        df = pd.DataFrame({"rate": [1.0]}, index=idx)
        result = accum(df, window=3)
        assert result["rate"].isna().all()

    def test_both_window_and_freq_raises(self, monthly_rates: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="Cannot specify both"):
            accum(monthly_rates, window=6, freq="M")
