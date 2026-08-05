"""Regressions for the rendering defects fixed in the F3A pass.

Each test names the input that used to produce a wrong chart, a bare pandas or
matplotlib exception, or silence where an error was warranted.  They are kept
together because they share a cause: the render path trusted its inputs to be
well-formed and the axis to be temporal.
"""

from __future__ import annotations

import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from chartkit._internal.highlight import normalize_highlight
from chartkit._internal.plot_validation import coerce_axis_limits
from chartkit.charts._helpers import (
    RenderContext,
    _coerce_datetime_index,
    is_categorical_index,
    resolve_color,
)
from chartkit.exceptions import ChartKitError, ValidationError
from chartkit.settings import get_config


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


@pytest.fixture
def dates() -> pd.DatetimeIndex:
    return pd.date_range("2023-01-31", periods=12, freq="ME")


class TestHighlightNormalization:
    def test_non_iterable_raises_chartkit_error(self) -> None:
        """A bare TypeError escapes every ``except ChartKitError`` a caller writes."""
        with pytest.raises(ChartKitError):
            normalize_highlight(123)  # type: ignore[arg-type]

    def test_error_names_the_offending_value(self) -> None:
        with pytest.raises(ValidationError, match="123"):
            normalize_highlight(123)  # type: ignore[arg-type]


class TestTickRotationValidation:
    def test_true_is_not_an_angle(self, dates: pd.DatetimeIndex) -> None:
        """``isinstance(True, int)`` let ``tick_rotation=True`` mean 1 degree."""
        df = pd.DataFrame({"a": range(12)}, index=dates)
        with pytest.raises(ValidationError, match="tick_rotation"):
            df.chartkit.plot(tick_rotation=True)  # type: ignore[arg-type]

    def test_int_still_accepted(self, dates: pd.DatetimeIndex) -> None:
        df = pd.DataFrame({"a": range(12)}, index=dates)
        result = df.chartkit.plot(tick_rotation=45)
        assert result.axes.get_xticklabels()[0].get_rotation() == 45


class TestColorCycle:
    def test_empty_palette_raises_instead_of_dividing_by_zero(self) -> None:
        ctx = RenderContext(
            config=get_config(),
            colors=[],
            user_color=None,
            color_offset=0,
            zorder=1.0,
            y_data=pd.DataFrame({"a": [1.0]}),
        )
        with pytest.raises(ChartKitError, match="palette"):
            resolve_color(ctx, 0)

    def test_user_color_bypasses_the_palette(self) -> None:
        ctx = RenderContext(
            config=get_config(),
            colors=[],
            user_color="#ff0000",
            color_offset=0,
            zorder=1.0,
            y_data=pd.DataFrame({"a": [1.0]}),
        )
        assert resolve_color(ctx, 0) == "#ff0000"


class TestIndexClassification:
    def test_empty_object_index_is_not_categorical(self) -> None:
        """``all([])`` is True, so an empty index claimed to be categorical."""
        assert is_categorical_index(pd.Index([], dtype="object")) is False

    def test_numeric_index_is_not_reinterpreted_as_nanoseconds(self) -> None:
        """``pd.to_datetime([2020])`` yields 1970-01-01, not the year 2020."""
        assert _coerce_datetime_index(pd.Index([2020, 2021, 2022, 2023])) is None

    def test_datetime_index_still_coerces(self, dates: pd.DatetimeIndex) -> None:
        coerced = _coerce_datetime_index(dates)
        assert coerced is not None
        assert len(coerced) == 12


class TestAxisLimitCoercion:
    def test_year_strings_stay_dates_on_a_date_axis(
        self, dates: pd.DatetimeIndex
    ) -> None:
        """``"2023"`` parsed as float(2023.0) put the axis 2000 years off."""
        import matplotlib.dates as mdates

        df = pd.DataFrame({"a": range(12)}, index=dates)
        result = df.chartkit.plot(xlim=("2023", "2024"))

        lo, hi = result.axes.get_xlim()
        assert lo == pytest.approx(mdates.date2num(pd.Timestamp("2023-01-01")))
        assert hi == pytest.approx(mdates.date2num(pd.Timestamp("2024-01-01")))

    def test_numeric_strings_stay_numeric_without_a_date_axis(self) -> None:
        assert coerce_axis_limits(("100", "200")) == (100.0, 200.0)


class TestConstantSeries:
    def test_y_origin_auto_does_not_collapse_the_axis(
        self, dates: pd.DatetimeIndex
    ) -> None:
        """set_ylim(v, v) emits a UserWarning that becomes an error under -W error."""
        flat = pd.DataFrame({"a": [5.0] * 6}, index=dates[:6])
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            result = flat.chartkit.plot(kind="bar", y_origin="auto")

        lo, hi = result.axes.get_ylim()
        assert lo < hi


class TestColumnSelection:
    def test_numeric_x_column_is_not_replotted_as_a_series(self) -> None:
        """``x='year'`` still landed in ``select_dtypes``, drawing year vs year."""
        df = pd.DataFrame({"year": [2020, 2021, 2022], "value": [1.0, 2.0, 3.0]})
        result = df.chartkit.plot(x="year")

        labels = [line.get_label() for line in result.axes.lines]
        assert labels == ["value"]

    def test_explicit_y_may_still_name_the_x_column(self) -> None:
        """Only the implicit y=None path drops it; an explicit ask is honoured."""
        df = pd.DataFrame({"year": [2020, 2021, 2022], "value": [1.0, 2.0, 3.0]})
        result = df.chartkit.plot(x="year", y="year")
        assert [line.get_label() for line in result.axes.lines] == ["year"]

    def test_duplicate_y_columns_rejected(self, dates: pd.DatetimeIndex) -> None:
        """``df[["a","a"]]["a"]`` returns a DataFrame and broadcasting explodes."""
        df = pd.DataFrame({"a": range(12), "b": range(12)}, index=dates)
        with pytest.raises(ValidationError, match=r"[Dd]uplicate"):
            df.chartkit.plot(y=["a", "a"], kind="bar")


class TestDuplicatedIndex:
    def test_highlight_max_survives_a_duplicated_index(
        self, dates: pd.DatetimeIndex
    ) -> None:
        """idxmax() returns a Series when the index repeats; np.isfinite blew up."""
        dup = pd.DataFrame({"a": [1.0, 5.0, 5.0, 2.0]}, index=[dates[0]] * 4)
        result = dup.chartkit.plot(highlight="max")
        assert len(result.axes.texts) == 1

    def test_highlight_last_survives_a_duplicated_index(
        self, dates: pd.DatetimeIndex
    ) -> None:
        dup = pd.DataFrame({"a": [1.0, 5.0, 5.0, 2.0]}, index=[dates[0]] * 4)
        result = dup.chartkit.plot(highlight="last")
        assert len(result.axes.texts) == 1


class TestNonTemporalKinds:
    """Kinds whose X axis holds values or categories must not be date-formatted."""

    @pytest.fixture(autouse=True)
    def _date_format_configured(self):
        from chartkit import configure

        configure(ticks={"date_format": "%b/%Y"})
        yield
        configure(ticks={"date_format": None})

    @pytest.mark.parametrize("kind", ["hist", "ecdf", "boxplot", "violinplot"])
    def test_value_axis_is_not_labelled_with_dates(
        self, kind: str, dates: pd.DatetimeIndex
    ) -> None:
        """A configured date_format turned bin edges into 'Jan/1970'."""
        df = pd.DataFrame({"a": np.linspace(1, 12, 12)}, index=dates)
        result = df.chartkit.plot(kind=kind)

        formatter = result.axes.xaxis.get_major_formatter()
        rendered = [formatter(t) for t in result.axes.get_xticks()]
        assert not any("1970" in str(label) for label in rendered)

    def test_temporal_kinds_still_get_dates(self, dates: pd.DatetimeIndex) -> None:
        df = pd.DataFrame({"a": np.linspace(1, 12, 12)}, index=dates)
        result = df.chartkit.plot(kind="line")

        formatter = result.axes.xaxis.get_major_formatter()
        rendered = [formatter(t) for t in result.axes.get_xticks()]
        assert any("2023" in str(label) for label in rendered)


class TestPlotterReuse:
    def test_each_plot_result_saves_its_own_figure(
        self, dates: pd.DatetimeIndex, tmp_path
    ) -> None:
        """save() went through the plotter, whose ``_fig`` the second plot replaced."""
        from chartkit.engine import ChartingPlotter

        df = pd.DataFrame({"a": range(12)}, index=dates)
        plotter = ChartingPlotter(df)
        first = plotter.plot(title="FIRST", figsize=(4.0, 3.0))
        plotter.plot(title="SECOND", figsize=(9.0, 7.0))

        target = tmp_path / "first.png"
        first.save(str(target))

        from PIL import Image

        with Image.open(target) as saved:
            width, height = saved.size
        assert width < height * 2, (
            f"saved a {width}x{height} image; the 4x3 figure was expected, "
            "so the second plot's figure was written instead"
        )


class TestCollisionRunsLast:
    def test_labels_do_not_overlap_after_limits_are_applied(
        self, dates: pd.DatetimeIndex
    ) -> None:
        """Collision ran before finalize_chart, so it never saw the final ylim."""
        df = pd.DataFrame(
            {"a": np.linspace(10.0, 10.5, 12), "b": np.linspace(10.1, 10.6, 12)},
            index=dates,
        )
        result = df.chartkit.plot(highlight="last", ylim=(0.0, 400.0))

        assert result.describe(geometry=True)["overlaps"] == []

    def test_collision_can_still_be_disabled(self, dates: pd.DatetimeIndex) -> None:
        df = pd.DataFrame({"a": range(12)}, index=dates)
        result = df.chartkit.plot(highlight="last", collision=False)
        assert len(result.axes.texts) == 1


class TestBarSort:
    def test_sort_on_a_datetime_axis_is_rejected(self, dates: pd.DatetimeIndex) -> None:
        """Each bar stayed at its own date, so the chart came out unsorted."""
        df = pd.DataFrame({"a": np.linspace(1, 12, 12)}, index=dates)
        with pytest.raises(ValidationError, match="categorical"):
            df.chartkit.plot(kind="bar", sort="descending")

    def test_sort_on_a_numeric_axis_is_rejected(self) -> None:
        df = pd.DataFrame({"a": [3.0, 9.0, 5.0]}, index=[10, 20, 30])
        with pytest.raises(ValidationError, match="categorical"):
            df.chartkit.plot(kind="bar", sort="ascending")

    def test_categorical_sort_still_works(self) -> None:
        df = pd.DataFrame({"v": [3.0, 9.0, 5.0]}, index=["norte", "sul", "leste"])
        result = df.chartkit.plot(kind="bar", sort="descending")

        by_position = sorted(result.axes.patches, key=lambda p: p.get_x())
        heights = [p.get_height() for p in by_position]
        assert heights == [9.0, 5.0, 3.0]

    def test_barh_sorts_a_datetime_axis(self, dates: pd.DatetimeIndex) -> None:
        """barh draws at ordinal positions, so ranking is meaningful there."""
        df = pd.DataFrame({"a": np.linspace(1, 12, 12)}, index=dates)
        result = df.chartkit.plot(kind="barh", sort="descending")

        by_position = sorted(result.axes.patches, key=lambda p: p.get_y())
        widths = [p.get_width() for p in by_position]
        assert widths == sorted(widths, reverse=True)


class TestStairsAxis:
    def test_dates_survive_the_stairs_enhancer(self, dates: pd.DatetimeIndex) -> None:
        """Without explicit edges, ax.stairs() replaced the dates with 0..n."""
        import matplotlib.dates as mdates

        df = pd.DataFrame({"a": np.linspace(1, 12, 12)}, index=dates)
        result = df.chartkit.plot(kind="stairs")

        lo, _ = result.axes.get_xlim()
        assert lo >= mdates.date2num(pd.Timestamp("2022-01-01"))

    def test_categorical_index_keeps_positional_edges(self) -> None:
        df = pd.DataFrame({"v": [3.0, 9.0, 5.0]}, index=["norte", "sul", "leste"])
        result = df.chartkit.plot(kind="stairs")
        assert result.axes.get_xlim()[1] <= 4
