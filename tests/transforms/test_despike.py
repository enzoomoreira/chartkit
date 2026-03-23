"""Tests for chartkit.transforms.temporal.despike.

Covers: spike detection and replacement, method variants, edge cases,
validation, multi-column behavior, chaining via accessor.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms.temporal import despike


class TestDespikeDetection:
    def test_detects_obvious_spike(self, known_despike_data: pd.Series) -> None:
        """A 350 value in a ~100 neighborhood should be corrected."""
        result = despike(known_despike_data)
        # The spike at index 5 (value=350) should be replaced
        assert result.iloc[5] != 350.0
        # Replaced value should be close to the neighborhood median (~100)
        assert 95.0 <= result.iloc[5] <= 105.0

    def test_preserves_non_spike_values(self, known_despike_data: pd.Series) -> None:
        """Non-spike values should remain unchanged."""
        result = despike(known_despike_data)
        # All values except the spike at index 5 should be identical
        mask = np.ones(len(known_despike_data), dtype=bool)
        mask[5] = False
        pd.testing.assert_series_equal(
            result.iloc[mask], known_despike_data.iloc[mask]
        )

    def test_no_spikes_returns_original(self, daily_prices: pd.DataFrame) -> None:
        """Data without spikes should pass through unchanged."""
        result = despike(daily_prices)
        pd.testing.assert_frame_equal(result, daily_prices)

    def test_multi_column_independent(self, multi_spike_data: pd.DataFrame) -> None:
        """Each column is despiked independently."""
        result = despike(multi_spike_data)
        # Spike in col a at index 3 should be corrected
        assert result["a"].iloc[3] != 500.0
        assert 95.0 <= result["a"].iloc[3] <= 105.0
        # Spike in col b at index 15 should be corrected
        assert result["b"].iloc[15] != 200.0
        assert 45.0 <= result["b"].iloc[15] <= 55.0


class TestDespikeThreshold:
    def test_moderate_deviation_not_caught(self) -> None:
        """A 20% deviation in volatile data should NOT be caught with threshold=5."""
        idx = pd.date_range("2023-01-02", periods=51, freq="B")
        rng = np.random.default_rng(42)
        values = rng.normal(100, 5, 51)  # realistic volatility
        values[25] = 120.0  # 20% above mean, within ~4 sigma
        s = pd.Series(values, index=idx, name="price")
        result = despike(s)
        assert result.iloc[25] == pytest.approx(120.0)

    def test_low_threshold_catches_more(self, known_despike_data: pd.Series) -> None:
        """Lower threshold should still catch the obvious spike."""
        result = despike(known_despike_data, threshold=3.0)
        assert result.iloc[5] != 350.0

    def test_very_high_threshold_ignores_all(self) -> None:
        """Extremely high threshold should let everything through."""
        idx = pd.date_range("2023-01-02", periods=21, freq="B")
        rng = np.random.default_rng(42)
        values = rng.normal(100, 5, 21)
        values[10] = 200.0  # spike
        s = pd.Series(values, index=idx, name="price")
        result = despike(s, threshold=100.0)
        assert result.iloc[10] == pytest.approx(200.0)


class TestDespikeMethod:
    def test_median_method(self, known_despike_data: pd.Series) -> None:
        """method='median' replaces spike with rolling median."""
        result = despike(known_despike_data, method="median")
        # Should be close to neighborhood median
        assert 95.0 <= result.iloc[5] <= 105.0

    def test_interpolate_method(self, known_despike_data: pd.Series) -> None:
        """method='interpolate' replaces spike with linear interpolation."""
        result = despike(known_despike_data, method="interpolate")
        # Should be between neighbors (99.0 and 100.0)
        assert result.iloc[5] != 350.0
        expected = (known_despike_data.iloc[4] + known_despike_data.iloc[6]) / 2
        assert result.iloc[5] == pytest.approx(expected, abs=1.0)


class TestDespikeWindow:
    def test_small_window(self, known_despike_data: pd.Series) -> None:
        """Smaller window should still detect the spike."""
        result = despike(known_despike_data, window=5)
        assert result.iloc[5] != 350.0

    def test_large_window(self, known_despike_data: pd.Series) -> None:
        """Larger window should still detect the spike."""
        result = despike(known_despike_data, window=11)
        assert result.iloc[5] != 350.0


class TestDespikeValidation:
    def test_window_too_small_raises(self) -> None:
        with pytest.raises(TransformError, match=">= 3"):
            despike(pd.Series([1.0, 2.0, 3.0], name="x"), window=1)

    def test_even_window_raises(self) -> None:
        with pytest.raises(TransformError, match="odd"):
            despike(pd.Series([1.0, 2.0, 3.0], name="x"), window=4)

    def test_negative_threshold_raises(self) -> None:
        with pytest.raises(TransformError, match="positive"):
            despike(pd.Series([1.0, 2.0, 3.0], name="x"), threshold=-1.0)

    def test_zero_threshold_raises(self) -> None:
        with pytest.raises(TransformError, match="positive"):
            despike(pd.Series([1.0, 2.0, 3.0], name="x"), threshold=0.0)

    def test_invalid_method_raises(self) -> None:
        with pytest.raises(TransformError):
            despike(pd.Series([1.0, 2.0, 3.0], name="x"), method="invalid")

    def test_empty_data_raises(self, empty_df: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="empty"):
            despike(empty_df)

    def test_non_numeric_raises(self) -> None:
        s = pd.Series(["a", "b", "c"], name="text")
        with pytest.raises(TransformError, match="numeric"):
            despike(s)


class TestDespikeEdgeCases:
    def test_all_nan(self, all_nan_series: pd.Series) -> None:
        """All-NaN input should produce all-NaN output."""
        result = despike(all_nan_series)
        assert result.isna().all()

    def test_constant_data_unchanged(self, constant_series: pd.Series) -> None:
        """Constant data (no variation) should pass through unchanged."""
        result = despike(constant_series)
        assert (result == 5.0).all()

    def test_series_input(self, known_despike_data: pd.Series) -> None:
        """Works with Series input."""
        result = despike(known_despike_data)
        assert isinstance(result, pd.Series)

    def test_dataframe_input(self, multi_spike_data: pd.DataFrame) -> None:
        """Works with DataFrame input."""
        result = despike(multi_spike_data)
        assert isinstance(result, pd.DataFrame)

    def test_preserves_index(self, known_despike_data: pd.Series) -> None:
        """Output index should match input index."""
        result = despike(known_despike_data)
        pd.testing.assert_index_equal(result.index, known_despike_data.index)

    def test_coerces_dict_input(self) -> None:
        """Dict input should be coerced and despiked."""
        data = {"price": [100.0, 100.0, 100.0, 500.0, 100.0, 100.0, 100.0,
                          100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0,
                          100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0]}
        result = despike(data)
        assert isinstance(result, pd.DataFrame)


class TestDespikeAccessor:
    def test_chaining(self, known_despike_data: pd.Series) -> None:
        """despike should work via TransformAccessor chaining."""
        from chartkit.transforms.accessor import TransformAccessor

        accessor = TransformAccessor(known_despike_data)
        result = accessor.despike().df
        assert result.iloc[5, 0] != 350.0
