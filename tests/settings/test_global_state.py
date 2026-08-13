"""Regressions for the shared-state defects fixed in the F4 pass.

Registries accepted silent overwrites, the merged TOML lived on a ClassVar
every loader shared, and config discovery had no way to be turned off.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pytest

from chartkit.charts import ChartRenderer
from chartkit.exceptions import RegistryError
from chartkit.metrics import MetricRegistry
from chartkit.settings.discovery import (
    AUTO_CONFIG_ENV_VAR,
    auto_config_enabled,
    find_config_files,
)


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


class TestMetricRegistryProtection:
    def test_registering_an_existing_name_raises(self) -> None:
        """A second 'ath' used to replace the built-in without a word."""
        with pytest.raises(RegistryError, match="already registered"):

            @MetricRegistry.register("ath")
            def _shadow(ax, x_data, y_data, **kwargs) -> None: ...

    def test_replace_makes_the_override_deliberate(self) -> None:
        @MetricRegistry.register("ath", replace=True)
        def _override(ax, x_data, y_data, **kwargs) -> None: ...

        assert MetricRegistry._metrics["ath"].func is _override

    def test_a_new_name_registers_normally(self) -> None:
        @MetricRegistry.register("nova_metrica")
        def _fresh(ax, x_data, y_data, **kwargs) -> None: ...

        assert "nova_metrica" in MetricRegistry.available()

    def test_unregister_removes_one_metric(self) -> None:
        @MetricRegistry.register("descartavel")
        def _tmp(ax, x_data, y_data, **kwargs) -> None: ...

        MetricRegistry.unregister("descartavel")
        assert "descartavel" not in MetricRegistry.available()

    def test_unregister_names_the_missing_metric(self) -> None:
        with pytest.raises(RegistryError, match="nao_existe"):
            MetricRegistry.unregister("nao_existe")

    def test_reset_keeps_the_builtins(self) -> None:
        """clear() emptied the registry, leaving 'ath' and 'ma' undefined."""

        @MetricRegistry.register("temporaria")
        def _tmp(ax, x_data, y_data, **kwargs) -> None: ...

        MetricRegistry.reset_to_builtins()

        assert "temporaria" not in MetricRegistry.available()
        assert {"ath", "atl", "ma", "std_band"} <= set(MetricRegistry.available())


class TestEnhancerRegistryProtection:
    def test_registering_an_existing_kind_raises(self) -> None:
        with pytest.raises(RegistryError, match="already handled"):

            @ChartRenderer.register_enhancer("bar")
            def _shadow(ax, x, y_data, highlight, **kwargs) -> None: ...

    def test_replace_makes_the_override_deliberate(self) -> None:
        original = ChartRenderer._enhancers["bar"]
        try:

            @ChartRenderer.register_enhancer("bar", replace=True)
            def _override(ax, x, y_data, highlight, **kwargs) -> None: ...

            assert ChartRenderer._enhancers["bar"] is _override
        finally:
            ChartRenderer._enhancers["bar"] = original

    def test_a_new_kind_registers_normally(self) -> None:
        try:

            @ChartRenderer.register_enhancer("meu_grafico")
            def _fresh(ax, x, y_data, highlight, **kwargs) -> None: ...

            assert "meu_grafico" in ChartRenderer.available()
        finally:
            ChartRenderer._enhancers.pop("meu_grafico", None)


class TestAutoDiscoveryOptOut:
    def test_discovery_is_on_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(AUTO_CONFIG_ENV_VAR, raising=False)
        assert auto_config_enabled() is True

    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
    def test_the_env_var_disables_discovery(
        self, value: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without this, chartkit reads whatever pyproject.toml sits above cwd."""
        monkeypatch.setenv(AUTO_CONFIG_ENV_VAR, value)
        assert auto_config_enabled() is False
        assert find_config_files() == []

    @pytest.mark.parametrize("value", ["0", "false", "no", ""])
    def test_falsey_values_leave_discovery_on(
        self, value: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(AUTO_CONFIG_ENV_VAR, value)
        assert auto_config_enabled() is True


class TestTomlDataIsolation:
    def test_two_loaders_do_not_share_toml_state(self, tmp_path) -> None:
        """The merged TOML lived on a ChartingConfig ClassVar, so whichever
        loader built its config last defined what the other one saw."""
        from chartkit.settings.loader import ConfigLoader

        first_toml = tmp_path / "first.toml"
        first_toml.write_text('[branding]\ncompany_name = "Primeira"\n')
        second_toml = tmp_path / "second.toml"
        second_toml.write_text('[branding]\ncompany_name = "Segunda"\n')

        first = ConfigLoader()
        first.configure(config_path=first_toml)
        second = ConfigLoader()
        second.configure(config_path=second_toml)

        # Build the second config first: with shared class state the write
        # would leak into the first loader's later read.
        assert second.get_config().branding.company_name == "Segunda"
        assert first.get_config().branding.company_name == "Primeira"

    def test_the_carrier_kwarg_is_not_a_field(self) -> None:
        from chartkit.settings.schema import TOML_DATA_KWARG, ChartingConfig

        assert TOML_DATA_KWARG not in ChartingConfig.model_fields
