from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms._validation import coerce_input


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
        assert len(result) == 2

    def test_dict_scalar_to_series(self) -> None:
        result = coerce_input({"a": 1, "b": 2})
        assert isinstance(result, pd.Series)
        assert len(result) == 2

    def test_list_1d_to_series(self) -> None:
        result = coerce_input([1, 2, 3])
        assert isinstance(result, pd.Series)
        assert len(result) == 3

    def test_list_2d_to_dataframe(self) -> None:
        result = coerce_input([[1, 2], [3, 4]])
        assert isinstance(result, pd.DataFrame)
        assert result.shape == (2, 2)

    def test_ndarray_1d_to_series(self) -> None:
        result = coerce_input(np.array([1.0, 2.0, 3.0]))
        assert isinstance(result, pd.Series)
        assert len(result) == 3

    def test_ndarray_2d_to_dataframe(self) -> None:
        result = coerce_input(np.array([[1, 2], [3, 4]]))
        assert isinstance(result, pd.DataFrame)
        assert result.shape == (2, 2)


class TestCoerceInputErrors:
    def test_3d_array_raises(self) -> None:
        with pytest.raises(TransformError, match="3 dimensions"):
            coerce_input(np.zeros((2, 3, 4)))

    def test_4d_array_raises(self) -> None:
        with pytest.raises(TransformError, match="4 dimensions"):
            coerce_input(np.zeros((2, 3, 4, 5)))

    def test_string_raises(self) -> None:
        with pytest.raises(TransformError, match="str"):
            coerce_input("hello")

    def test_int_raises(self) -> None:
        with pytest.raises(TransformError, match="int"):
            coerce_input(42)

    def test_none_raises(self) -> None:
        with pytest.raises(TransformError, match="NoneType"):
            coerce_input(None)

    def test_set_raises(self) -> None:
        with pytest.raises(TransformError, match="set"):
            coerce_input({1, 2, 3})
