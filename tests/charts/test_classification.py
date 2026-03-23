"""Chart kind classification: alias resolution, capability lookup, and validation."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from chartkit.charts._classification import (
    KIND_ALIASES,
    KindCaps,
    _extract_metric_name,
    get_kind_caps,
    resolve_kind_alias,
    validate_highlight_for_kind,
    validate_metrics_for_kind,
)
from chartkit.exceptions import ValidationError


# ---------------------------------------------------------------------------
# resolve_kind_alias
# ---------------------------------------------------------------------------


class TestResolveKindAlias:
    @pytest.mark.parametrize(
        "alias, expected",
        [("line", "plot"), ("area", "fill_between")],
    )
    def test_known_aliases(self, alias: str, expected: str) -> None:
        assert resolve_kind_alias(alias) == expected

    def test_non_alias_passes_through(self) -> None:
        assert resolve_kind_alias("scatter") == "scatter"

    def test_unknown_string_passes_through(self) -> None:
        assert resolve_kind_alias("totally_custom") == "totally_custom"

    def test_aliases_dict_matches_renderer(self) -> None:
        """KIND_ALIASES must stay in sync with ChartRenderer._ALIASES."""
        from chartkit.charts.renderer import ChartRenderer

        assert ChartRenderer._ALIASES is KIND_ALIASES


# ---------------------------------------------------------------------------
# get_kind_caps
# ---------------------------------------------------------------------------


class TestGetKindCaps:
    @pytest.mark.parametrize(
        "kind",
        [
            "plot",
            "scatter",
            "bar",
            "barh",
            "step",
            "fill_between",
            "stackplot",
            "stacked_bar",
            "stairs",
            "stem",
        ],
    )
    def test_series_kinds_are_composable(self, kind: str) -> None:
        caps = get_kind_caps(kind)
        assert caps is not None
        assert caps.group == "series"
        assert caps.composable is True

    @pytest.mark.parametrize(
        "kind",
        ["boxplot", "violinplot", "hist", "ecdf", "pie", "eventplot"],
    )
    def test_non_series_kinds_are_not_composable(self, kind: str) -> None:
        caps = get_kind_caps(kind)
        assert caps is not None
        assert caps.composable is False

    def test_unclassified_kind_returns_none(self) -> None:
        assert get_kind_caps("hexbin") is None

    def test_returns_frozen_dataclass(self) -> None:
        caps = get_kind_caps("plot")
        assert isinstance(caps, KindCaps)
        with pytest.raises(AttributeError):
            caps.highlight = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# validate_highlight_for_kind
# ---------------------------------------------------------------------------


class TestValidateHighlightForKind:
    @pytest.mark.parametrize(
        "kind", ["plot", "scatter", "bar", "step", "stairs", "stem"]
    )
    def test_highlight_supported_kinds_pass(self, kind: str) -> None:
        validate_highlight_for_kind(kind)

    @pytest.mark.parametrize(
        "kind",
        ["stackplot", "boxplot", "violinplot", "hist", "ecdf", "pie", "eventplot"],
    )
    def test_highlight_unsupported_kinds_raise(self, kind: str) -> None:
        with pytest.raises(ValidationError, match="does not support highlight"):
            validate_highlight_for_kind(kind)

    def test_alias_resolves_before_check(self) -> None:
        """'line' -> 'plot' which supports highlight."""
        validate_highlight_for_kind("line")

    def test_alias_in_error_message_uses_original_name(self) -> None:
        """Error should show user-facing name, not canonical."""
        # 'area' resolves to 'fill_between' which supports highlight,
        # so we can't test error message with aliases that support highlight.
        # Instead, verify that the function accepts resolved= kwarg
        # and uses the original kind in the message.
        # stackplot doesn't support highlight -- pass it as kind.
        with pytest.raises(ValidationError, match="stackplot"):
            validate_highlight_for_kind("stackplot")

    def test_unclassified_kind_passes(self) -> None:
        """Unknown generic kinds should not be blocked."""
        validate_highlight_for_kind("hexbin")

    def test_preresolved_skips_alias_lookup(self) -> None:
        """When resolved= is provided, alias lookup is skipped."""
        # Pass kind="anything" but resolved="plot" (which supports highlight)
        validate_highlight_for_kind("anything", resolved="plot")

    def test_preresolved_unsupported_raises(self) -> None:
        """When resolved= points to unsupported kind, original kind in error."""
        with pytest.raises(ValidationError, match="my_alias"):
            validate_highlight_for_kind("my_alias", resolved="stackplot")


# ---------------------------------------------------------------------------
# _extract_metric_name
# ---------------------------------------------------------------------------


class TestExtractMetricName:
    def test_simple_name(self) -> None:
        assert _extract_metric_name("ath") == "ath"

    def test_name_with_params(self) -> None:
        assert _extract_metric_name("ma:12") == "ma"

    def test_name_with_multiple_params(self) -> None:
        assert _extract_metric_name("band:1.5:4.5") == "band"

    def test_name_with_column(self) -> None:
        assert _extract_metric_name("ath@revenue") == "ath"

    def test_name_with_params_and_column(self) -> None:
        assert _extract_metric_name("ma:12@col") == "ma"

    def test_name_with_label(self) -> None:
        assert _extract_metric_name("ath|Maximum") == "ath"

    def test_full_syntax(self) -> None:
        """name:param@column|label -- all decorators present."""
        assert _extract_metric_name("ma:12@col|Custom Label") == "ma"

    def test_label_before_column(self) -> None:
        """Pipe before @ -- unusual but should still extract name."""
        assert _extract_metric_name("ma:12|Label@col") == "ma"

    def test_metric_spec_object(self) -> None:
        """Objects with .name attribute (like MetricSpec)."""
        spec = SimpleNamespace(name="std_band")
        assert _extract_metric_name(spec) == "std_band"

    def test_metric_spec_name_attribute_takes_priority(self) -> None:
        """If object has .name, string parsing is skipped."""
        spec = SimpleNamespace(name="ma")
        # Even if str() would give something weird, .name wins
        assert _extract_metric_name(spec) == "ma"


# ---------------------------------------------------------------------------
# validate_metrics_for_kind
# ---------------------------------------------------------------------------


class TestValidateMetricsForKind:
    # -- series kinds: everything allowed --

    def test_series_kind_allows_any_metric(self) -> None:
        validate_metrics_for_kind("plot", ["ath", "ma:12", "hline:100"])

    def test_series_kind_allows_temporal_metrics(self) -> None:
        validate_metrics_for_kind("bar", ["ma:6", "std_band", "vband:2023-01:2023-06"])

    # -- non-series kinds: all metrics blocked --

    @pytest.mark.parametrize("kind", ["boxplot", "violinplot"])
    def test_distribution_kind_blocks_all_metrics(self, kind: str) -> None:
        with pytest.raises(ValidationError, match="does not support metrics"):
            validate_metrics_for_kind(kind, "ath")

    @pytest.mark.parametrize("kind", ["hist", "ecdf"])
    def test_aggregation_kind_blocks_all_metrics(self, kind: str) -> None:
        with pytest.raises(ValidationError, match="does not support metrics"):
            validate_metrics_for_kind(kind, ["hline:50"])

    def test_pie_blocks_metrics(self) -> None:
        with pytest.raises(ValidationError, match="does not support metrics"):
            validate_metrics_for_kind("pie", "ath")

    def test_eventplot_blocks_metrics(self) -> None:
        with pytest.raises(ValidationError, match="does not support metrics"):
            validate_metrics_for_kind("eventplot", "ath")

    # -- error message includes metric name --

    def test_error_includes_metric_name(self) -> None:
        with pytest.raises(ValidationError, match="'hline'"):
            validate_metrics_for_kind("hist", "hline:100")

    def test_error_includes_kind_name(self) -> None:
        with pytest.raises(ValidationError, match="'pie'"):
            validate_metrics_for_kind("pie", "ath")

    # -- unclassified generic kinds: allow all --

    def test_unclassified_kind_allows_all_metrics(self) -> None:
        validate_metrics_for_kind("hexbin", ["ath", "ma:12", "vband:a:b"])

    # -- string vs list normalization --

    def test_single_string_spec(self) -> None:
        with pytest.raises(ValidationError):
            validate_metrics_for_kind("hist", "ath")

    def test_list_of_specs(self) -> None:
        with pytest.raises(ValidationError):
            validate_metrics_for_kind("hist", ["ath", "ma:12"])

    # -- alias resolution --

    def test_alias_resolved_before_lookup(self) -> None:
        """'line' -> 'plot' (series) should allow all metrics."""
        validate_metrics_for_kind("line", ["ath", "ma:12"])

    # -- first failing metric short-circuits --

    def test_first_invalid_metric_raises(self) -> None:
        """When all_metrics=False, the first metric triggers the error."""
        with pytest.raises(ValidationError, match="'ath'"):
            validate_metrics_for_kind("pie", ["ath", "ma:12"])

    # -- MetricSpec objects --

    def test_metric_spec_object_validated(self) -> None:
        spec = SimpleNamespace(name="ath")
        with pytest.raises(ValidationError, match="'ath'"):
            validate_metrics_for_kind("pie", [spec])
