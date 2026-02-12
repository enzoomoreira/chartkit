from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from chartkit.composing import compose
from chartkit.composing.layer import Layer
from chartkit.exceptions import ValidationError
from chartkit.result import PlotResult


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


def _make_layer(
    n: int = 5,
    cols: list[str] | None = None,
    axis: str = "left",
    **kwargs,
) -> Layer:
    cols = cols or ["val"]
    idx = pd.date_range("2023-01-01", periods=n, freq="ME")
    data = {c: range(1, n + 1) for c in cols}
    df = pd.DataFrame(data, index=idx)
    return Layer(df=df, axis=axis, **kwargs)  # type: ignore[arg-type]


class TestCompose:
    def test_returns_plot_result(self) -> None:
        result = compose(_make_layer(), title="Test")
        assert isinstance(result, PlotResult)

    def test_no_layers_raises(self) -> None:
        with pytest.raises(ValidationError, match="at least one layer"):
            compose()

    def test_all_right_raises(self) -> None:
        with pytest.raises(ValidationError, match="axis='right'"):
            compose(_make_layer(axis="right"))

    def test_single_layer(self) -> None:
        result = compose(_make_layer())
        assert result.fig is not None
        assert result.ax is not None

    def test_dual_axis(self) -> None:
        left = _make_layer(cols=["price"])
        right = _make_layer(cols=["rate"], axis="right")
        result = compose(left, right)
        assert result.fig is not None

    def test_title_applied(self) -> None:
        result = compose(_make_layer(), title="My Title")
        assert result.ax.get_title() == "My Title"

    def test_no_title(self) -> None:
        result = compose(_make_layer())
        assert result.ax.get_title() == ""

    def test_figsize_override(self) -> None:
        result = compose(_make_layer(), figsize=(4.0, 3.0))
        w, h = result.fig.get_size_inches()
        assert abs(w - 4.0) < 0.1
        assert abs(h - 3.0) < 0.1

    def test_plotter_has_save(self) -> None:
        result = compose(_make_layer())
        assert hasattr(result.plotter, "save")

    def test_multiple_left_layers(self) -> None:
        l1 = _make_layer(cols=["a"])
        l2 = _make_layer(cols=["b"])
        result = compose(l1, l2)
        assert result.fig is not None

    def test_units_applied(self) -> None:
        layer = _make_layer(units="%")
        result = compose(layer)
        formatter = result.ax.yaxis.get_major_formatter()
        assert formatter is not None

    def test_invalid_legend_type_raises(self) -> None:
        with pytest.raises(ValidationError, match="Invalid plot parameters"):
            compose(_make_layer(), legend=1)  # type: ignore[arg-type]
