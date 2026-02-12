from __future__ import annotations

import pandas as pd
import pytest

from chartkit._internal.extraction import extract_plot_data


@pytest.fixture
def sample_df() -> pd.DataFrame:
    idx = pd.date_range("2023-01-01", periods=3, freq="ME")
    return pd.DataFrame(
        {"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0], "cat": ["x", "y", "z"]},
        index=idx,
    )


class TestExtractData:
    def test_x_none_uses_index(self, sample_df: pd.DataFrame) -> None:
        x_data, _ = extract_plot_data(sample_df, x=None, y=None)
        pd.testing.assert_index_equal(x_data, sample_df.index)

    def test_x_column(self, sample_df: pd.DataFrame) -> None:
        x_data, _ = extract_plot_data(sample_df, x="a", y=None)
        pd.testing.assert_series_equal(x_data, sample_df["a"])

    def test_y_none_selects_numeric(self, sample_df: pd.DataFrame) -> None:
        _, y_data = extract_plot_data(sample_df, x=None, y=None)
        assert isinstance(y_data, pd.DataFrame)
        assert list(y_data.columns) == ["a", "b"]

    def test_y_single_string(self, sample_df: pd.DataFrame) -> None:
        _, y_data = extract_plot_data(sample_df, x=None, y="a")
        assert isinstance(y_data, pd.Series)
        assert y_data.name == "a"

    def test_y_list_of_strings(self, sample_df: pd.DataFrame) -> None:
        _, y_data = extract_plot_data(sample_df, x=None, y=["a", "b"])
        assert isinstance(y_data, pd.DataFrame)
        assert list(y_data.columns) == ["a", "b"]
