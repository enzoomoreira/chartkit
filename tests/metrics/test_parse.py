from __future__ import annotations

import pytest

from chartkit.exceptions import RegistryError, ValidationError
from chartkit.metrics.registry import MetricRegistry, MetricSpec

# Ensure builtins are registered
import chartkit.metrics.builtin  # noqa: F401


class TestMetricParseBasic:
    def test_simple_name(self) -> None:
        spec = MetricRegistry.parse("ath")
        assert spec.name == "ath"
        assert spec.params == {}
        assert spec.series is None
        assert spec.label is None

    def test_single_param(self) -> None:
        spec = MetricRegistry.parse("ma:12")
        assert spec.name == "ma"
        assert spec.params == {"window": 12}

    def test_two_params(self) -> None:
        spec = MetricRegistry.parse("band:1.5:4.5")
        assert spec.name == "band"
        assert spec.params == {"lower": 1.5, "upper": 4.5}


class TestMetricParseCoercion:
    def test_int_coercion(self) -> None:
        spec = MetricRegistry.parse("ma:12")
        assert isinstance(spec.params["window"], int)
        assert spec.params["window"] == 12

    def test_float_coercion(self) -> None:
        spec = MetricRegistry.parse("band:1.5:4.5")
        assert isinstance(spec.params["lower"], float)

    def test_string_param_preserved(self) -> None:
        spec = MetricRegistry.parse("vband:2023-01:2023-06")
        assert isinstance(spec.params["start"], str)
        assert spec.params["start"] == "2023-01"
        assert spec.params["end"] == "2023-06"


class TestMetricParseSeries:
    def test_at_series(self) -> None:
        spec = MetricRegistry.parse("ath@revenue")
        assert spec.series == "revenue"

    def test_at_with_params(self) -> None:
        spec = MetricRegistry.parse("ma:12@revenue")
        assert spec.name == "ma"
        assert spec.params == {"window": 12}
        assert spec.series == "revenue"

    def test_empty_series_raises(self) -> None:
        with pytest.raises(ValidationError, match="Empty series"):
            MetricRegistry.parse("ath@")


class TestMetricParseLabel:
    def test_label_pipe(self) -> None:
        spec = MetricRegistry.parse("ath|Maximo")
        assert spec.label == "Maximo"

    def test_label_with_params_and_series(self) -> None:
        spec = MetricRegistry.parse("ma:12@revenue|Media 12M")
        assert spec.name == "ma"
        assert spec.params == {"window": 12}
        assert spec.series == "revenue"
        assert spec.label == "Media 12M"

    def test_empty_label_becomes_none(self) -> None:
        spec = MetricRegistry.parse("ath| ")
        assert spec.label is None


class TestMetricParseValidation:
    def test_unknown_metric_raises(self) -> None:
        with pytest.raises(RegistryError, match="Unknown metric"):
            MetricRegistry.parse("xyz")

    def test_missing_required_param_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires parameter"):
            MetricRegistry.parse("ma")

    def test_metricspec_passthrough(self) -> None:
        original = MetricSpec("ath", {}, None, None)
        result = MetricRegistry.parse(original)
        assert result is original


class TestMetricParseBuiltins:
    def test_ath_parses(self) -> None:
        spec = MetricRegistry.parse("ath")
        assert spec.name == "ath"

    def test_atl_parses(self) -> None:
        spec = MetricRegistry.parse("atl")
        assert spec.name == "atl"

    def test_avg_parses(self) -> None:
        spec = MetricRegistry.parse("avg")
        assert spec.name == "avg"

    def test_hline_parses(self) -> None:
        spec = MetricRegistry.parse("hline:100")
        assert spec.params == {"value": 100}

    def test_target_parses(self) -> None:
        spec = MetricRegistry.parse("target:50")
        assert spec.params == {"value": 50}

    def test_std_band_parses(self) -> None:
        spec = MetricRegistry.parse("std_band:20:2")
        assert spec.params == {"window": 20, "num_std": 2}

    def test_vband_parses(self) -> None:
        spec = MetricRegistry.parse("vband:2023-01-01:2023-06-30")
        assert spec.params["start"] == "2023-01-01"
        assert spec.params["end"] == "2023-06-30"
