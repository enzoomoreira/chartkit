"""Tests for the input pipeline: coerce_input, validate_numeric, sanitize_result.

Consolidates: test_coerce_input.py, test_validate_numeric.py, test_sanitize_result.py
+ parametrized empty_raises across all transforms.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms._validation import (
    coerce_input,
    sanitize_result,
    validate_numeric,
)
from chartkit.transforms.temporal import (
    accum,
    annualize,
    diff,
    drawdown,
    normalize,
    variation,
    zscore,
)


# ---------------------------------------------------------------------------
# coerce_input
# ---------------------------------------------------------------------------


class TestCoerceInputPassthrough:
    def test_dataframe_passthrough(self) -> None:
        df = pd.DataFrame({"a": [1, 2]})
        result = coerce_input(df)
        assert result is df

    def test_series_passthrough(self) -> None:
        s = pd.Series([1, 2])
        result = coerce_input(s)
        assert result is s


class TestCoerceInputConversion:
    def test_dict_to_dataframe(self) -> None:
        result = coerce_input({"a": [1, 2], "b": [3, 4]})
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["a", "b"]

    def test_dict_scalar_to_series(self) -> None:
        result = coerce_input({"a": 1, "b": 2})
        assert isinstance(result, pd.Series)

    def test_list_1d_to_series(self) -> None:
        result = coerce_input([1, 2, 3])
        assert isinstance(result, pd.Series)

    def test_list_2d_to_dataframe(self) -> None:
        result = coerce_input([[1, 2], [3, 4]])
        assert isinstance(result, pd.DataFrame)
        assert result.shape == (2, 2)

    def test_ndarray_1d_to_series(self) -> None:
        result = coerce_input(np.array([1.0, 2.0, 3.0]))
        assert isinstance(result, pd.Series)

    def test_ndarray_2d_to_dataframe(self) -> None:
        result = coerce_input(np.array([[1, 2], [3, 4]]))
        assert isinstance(result, pd.DataFrame)
        assert result.shape == (2, 2)


class TestCoerceInputErrors:
    @pytest.mark.parametrize(
        "value, match",
        [
            (np.zeros((2, 3, 4)), "3 dimensions"),
            ("hello", "str"),
            (42, "int"),
            (None, "NoneType"),
            ({1, 2, 3}, "set"),
        ],
        ids=["3d_array", "string", "int", "none", "set"],
    )
    def test_unsupported_types_raise(self, value: object, match: str) -> None:
        with pytest.raises(TransformError, match=match):
            coerce_input(value)


# ---------------------------------------------------------------------------
# validate_numeric
# ---------------------------------------------------------------------------


class TestValidateNumericSeries:
    def test_numeric_series_passthrough(self, single_series: pd.Series) -> None:
        result = validate_numeric(single_series)
        assert result is single_series

    def test_non_numeric_series_raises(self) -> None:
        s = pd.Series(["a", "b", "c"])
        with pytest.raises(TransformError, match="must be numeric"):
            validate_numeric(s)

    def test_empty_series_raises(self, empty_series: pd.Series) -> None:
        with pytest.raises(TransformError, match="empty"):
            validate_numeric(empty_series)

    def test_non_datetime_index_no_raise(
        self, non_datetime_index_df: pd.DataFrame
    ) -> None:
        s = non_datetime_index_df["val"]
        result = validate_numeric(s)
        assert len(result) == 5


class TestValidateNumericDataFrame:
    def test_numeric_df_passthrough(self, monthly_rates: pd.DataFrame) -> None:
        result = validate_numeric(monthly_rates)
        assert result is monthly_rates

    def test_mixed_df_drops_non_numeric(
        self, multi_series_monthly: pd.DataFrame
    ) -> None:
        result = validate_numeric(multi_series_monthly)
        assert "category" not in result.columns
        assert len(result.columns) == 3

    def test_all_non_numeric_df_raises(self) -> None:
        df = pd.DataFrame({"a": ["x", "y"], "b": ["z", "w"]})
        with pytest.raises(TransformError, match="No numeric columns"):
            validate_numeric(df)

    def test_empty_df_raises(self, empty_df: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="empty"):
            validate_numeric(empty_df)


# ---------------------------------------------------------------------------
# sanitize_result
# ---------------------------------------------------------------------------


class TestSanitizeResult:
    def test_inf_replaced_with_nan(self) -> None:
        s = pd.Series([1.0, np.inf, 3.0])
        result = sanitize_result(s)
        assert np.isnan(result.iloc[1])
        assert result.iloc[0] == 1.0

    def test_neg_inf_replaced_with_nan(self) -> None:
        s = pd.Series([1.0, -np.inf, 3.0])
        result = sanitize_result(s)
        assert np.isnan(result.iloc[1])

    def test_normal_values_unchanged(self) -> None:
        s = pd.Series([1.0, 2.0, 3.0])
        result = sanitize_result(s)
        pd.testing.assert_series_equal(result, s)

    def test_nan_stays_nan(self) -> None:
        s = pd.Series([1.0, np.nan, 3.0])
        result = sanitize_result(s)
        assert np.isnan(result.iloc[1])


# ---------------------------------------------------------------------------
# Parametrized: all transforms reject empty data
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "transform_fn, kwargs",
    [
        (variation, {"horizon": "month", "periods": 1}),
        (accum, {"window": 3}),
        (normalize, {"base": 100}),
        (drawdown, {}),
        (zscore, {}),
        (annualize, {"freq": "M"}),
        (diff, {}),
    ],
    ids=["variation", "accum", "normalize", "drawdown", "zscore", "annualize", "diff"],
)
def test_all_transforms_reject_empty_dataframe(
    transform_fn: object, kwargs: dict, empty_df: pd.DataFrame
) -> None:
    """Every transform raises TransformError on empty input."""
    with pytest.raises(TransformError, match="empty"):
        transform_fn(empty_df, **kwargs)  # type: ignore[operator]
