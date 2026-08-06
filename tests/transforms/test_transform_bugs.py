"""Regressions for the transform defects fixed in the F3B pass.

The common thread is silence: each of these produced a plausible-looking
number, imputed data the caller never supplied, or blamed the wrong cause in
a log line, rather than failing where the problem was.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms.temporal import accum, despike, normalize, resample, zscore
from chartkit.warnings import DataMutationWarning, InferenceWarning


@pytest.fixture
def business_days() -> pd.DatetimeIndex:
    return pd.date_range("2023-01-02", periods=80, freq="B")


class TestDespikeInterpolate:
    def test_genuine_nans_are_preserved(self, business_days: pd.DatetimeIndex) -> None:
        """interpolate() filled every gap, including ones present in the input."""
        s = pd.Series(np.linspace(10.0, 12.0, 80), index=business_days)
        s.iloc[40] = 500.0
        s.iloc[5] = np.nan

        result = despike(s, window=11, method="interpolate")

        assert pd.isna(result.iloc[5]), "a gap in the input was imputed"
        assert result.iloc[40] != 500.0, "the spike was not replaced"

    def test_the_spike_itself_is_interpolated(
        self, business_days: pd.DatetimeIndex
    ) -> None:
        s = pd.Series(np.linspace(10.0, 12.0, 80), index=business_days)
        s.iloc[40] = 500.0

        result = despike(s, window=11, method="interpolate")
        assert result.iloc[40] == pytest.approx(s.iloc[39:42:2].mean(), abs=0.1)

    def test_median_method_also_preserves_gaps(
        self, business_days: pd.DatetimeIndex
    ) -> None:
        s = pd.Series(np.linspace(10.0, 12.0, 80), index=business_days)
        s.iloc[5] = np.nan
        assert pd.isna(despike(s, window=11, method="median").iloc[5])


class TestResampleContract:
    def test_non_numeric_columns_are_dropped_with_a_warning(
        self, business_days: pd.DatetimeIndex
    ) -> None:
        """Every other transform runs validate_numeric; resample skipped it, so a
        text column travelled through untouched instead of being reported."""
        df = pd.DataFrame(
            {"v": np.arange(80.0), "name": ["x"] * 80}, index=business_days
        )
        with pytest.warns(DataMutationWarning, match="non-numeric"):
            result = resample(df, freq="month")

        assert list(result.columns) == ["v"]

    def test_infinities_are_sanitised(self) -> None:
        idx = pd.date_range("2023-01-31", periods=6, freq="ME")
        s = pd.Series([1.0, 2.0, np.inf, 4.0, 5.0, 6.0], index=idx)

        result = resample(s, freq="month", method="mean")
        assert not np.isinf(result.to_numpy()).any()

    def test_numeric_resample_still_works(
        self, business_days: pd.DatetimeIndex
    ) -> None:
        s = pd.Series(np.arange(80.0), index=business_days)
        result = resample(s, freq="month")
        assert len(result) == 4


class TestNormalizeBaseDate:
    def test_non_temporal_index_raises_transform_error(self) -> None:
        """get_indexer leaked a raw TypeError from the pandas comparison."""
        df = pd.DataFrame({"v": [1.0, 2.0, 3.0]}, index=["a", "b", "c"])
        with (
            pytest.warns(InferenceWarning),
            pytest.raises(TransformError, match="base_date"),
        ):
            normalize(df, base_date="2023-01-01")

    def test_duplicated_index_raises_transform_error(self) -> None:
        """get_indexer raised InvalidIndexError, which is not a ChartKitError."""
        idx = pd.to_datetime(["2023-01-31", "2023-01-31", "2023-02-28"])
        df = pd.DataFrame({"v": [1.0, 2.0, 3.0]}, index=idx)
        with pytest.raises(TransformError, match="base_date"):
            normalize(df, base_date="2023-02-01")

    def test_nearest_match_still_works(self) -> None:
        idx = pd.date_range("2023-01-31", periods=6, freq="ME")
        df = pd.DataFrame({"v": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]}, index=idx)

        # 2023-03-05 is five days from 2023-02-28 and twenty-six from 2023-03-31.
        result = normalize(df, base=100.0, base_date="2023-03-05")
        assert result["v"].iloc[1] == pytest.approx(100.0)


class TestZScoreDiagnostics:
    def test_window_longer_than_the_data_says_so(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The log blamed constant data when the window simply did not fit."""
        idx = pd.date_range("2023-01-31", periods=10, freq="ME")
        s = pd.Series(np.linspace(1.0, 10.0, 10), index=idx)

        with caplog.at_level(logging.WARNING, logger="chartkit.transforms.temporal"):
            zscore(s, window=50)

        assert "std=0" not in caplog.text
        assert "window" in caplog.text

    def test_constant_data_still_reports_std_zero(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        idx = pd.date_range("2023-01-31", periods=10, freq="ME")
        s = pd.Series([5.0] * 10, index=idx)

        with caplog.at_level(logging.WARNING, logger="chartkit.transforms.temporal"):
            zscore(s)

        assert "std=0" in caplog.text


class TestAccumFallback:
    def test_holidays_do_not_force_the_config_window(self) -> None:
        """pd.infer_freq gives up on a business series with holidays; the
        fallback then used the monthly default on daily data."""
        idx = pd.date_range("2023-01-02", periods=80, freq="B").delete([3, 9, 17])
        s = pd.Series(np.full(len(idx), 0.1), index=idx)

        with pytest.warns(InferenceWarning, match="estimated"):
            result = accum(s)

        # Daily data accumulates over a business year, not over 12 days.
        assert result.notna().sum() < len(s) - 100 or result.isna().all()

    def test_explicit_window_is_untouched(self) -> None:
        idx = pd.date_range("2023-01-02", periods=80, freq="B").delete([3, 9, 17])
        s = pd.Series(np.full(len(idx), 0.1), index=idx)

        result = accum(s, window=5)
        assert result.notna().sum() == len(s) - 4

    def test_regular_monthly_data_needs_no_fallback(self) -> None:
        idx = pd.date_range("2023-01-31", periods=24, freq="ME")
        s = pd.Series(np.full(24, 1.0), index=idx)

        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error", InferenceWarning)
            accum(s)
