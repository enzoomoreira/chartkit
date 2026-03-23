"""Configuration loading, merging, and precedence tests.

Consolidates: test_schema.py, test_loader.py, test_deep_merge.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from chartkit.settings.loader import (
    ConfigLoader,
    _deep_merge,
    configure,
    get_config,
    reset_config,
)
from chartkit.settings.schema import ChartingConfig


class TestDeepMerge:
    """Nested dict merge used in TOML chain resolution."""

    def test_nested_keys_merged(self) -> None:
        result = _deep_merge({"a": {"x": 1}}, {"a": {"y": 2}})
        assert result == {"a": {"x": 1, "y": 2}}

    def test_nested_value_overridden(self) -> None:
        result = _deep_merge({"a": {"x": 1}}, {"a": {"x": 99}})
        assert result["a"]["x"] == 99

    def test_scalar_replaces_dict(self) -> None:
        result = _deep_merge({"a": {"x": 1}}, {"a": 42})
        assert result == {"a": 42}

    def test_dict_replaces_scalar(self) -> None:
        result = _deep_merge({"a": 1}, {"a": {"x": 1}})
        assert result == {"a": {"x": 1}}


class TestConfigureOverrides:
    """configure() init_settings take highest precedence."""

    def test_branding_override(self) -> None:
        configure(branding={"company_name": "TestCo"})
        assert get_config().branding.company_name == "TestCo"

    def test_reset_clears_overrides(self) -> None:
        configure(branding={"company_name": "TestCo"})
        reset_config()
        assert get_config().branding.company_name == ""

    def test_invalidates_cache_on_configure(self) -> None:
        config_before = get_config()
        configure(branding={"company_name": "New"})
        config_after = get_config()
        assert config_before is not config_after

    def test_cached_within_same_state(self) -> None:
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2


class TestEnvVars:
    """Environment variables with CHARTKIT_ prefix."""

    def test_env_overrides_dpi(self, monkeypatch: pytest.MonkeyPatch) -> None:
        ChartingConfig._toml_data = {}
        monkeypatch.setenv("CHARTKIT_LAYOUT__DPI", "72")
        config = ChartingConfig()
        assert config.layout.dpi == 72

    def test_nested_env_delimiter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        ChartingConfig._toml_data = {}
        monkeypatch.setenv("CHARTKIT_BRANDING__COMPANY_NAME", "EnvCorp")
        config = ChartingConfig()
        assert config.branding.company_name == "EnvCorp"


class TestTomlLoading:
    """TOML file loading and pyproject.toml section extraction."""

    def test_dotfolder_config_loaded(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".chartkit").mkdir()
        (tmp_path / ".chartkit" / "config.toml").write_text(
            '[branding]\ncompany_name = "FromToml"\n'
        )
        (tmp_path / ".git").mkdir()

        loader = ConfigLoader()
        config = loader.get_config()
        assert config.branding.company_name == "FromToml"

    def test_pyproject_section_extracted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\n\n'
            '[tool.chartkit.branding]\ncompany_name = "FromPyproject"\n'
        )
        loader = ConfigLoader()
        config = loader.get_config()
        assert config.branding.company_name == "FromPyproject"

    def test_dotfolder_config_wins_over_pyproject(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\n\n'
            '[tool.chartkit.branding]\ncompany_name = "FromPyproject"\n'
        )
        (tmp_path / ".chartkit").mkdir()
        (tmp_path / ".chartkit" / "config.toml").write_text(
            '[branding]\ncompany_name = "FromDotfolder"\n'
        )
        loader = ConfigLoader()
        assert loader.get_config().branding.company_name == "FromDotfolder"


class TestPathResolution:
    """ConfigLoader path resolution chain."""

    def test_outputs_path_default_name(self) -> None:
        loader = ConfigLoader()
        assert loader.outputs_path.name == "outputs"

    def test_outputs_path_explicit(self, tmp_path: Path) -> None:
        loader = ConfigLoader()
        loader.configure(outputs_path=tmp_path / "custom_out")
        assert loader.outputs_path == tmp_path / "custom_out"

    def test_charts_is_subdir_of_outputs(self) -> None:
        loader = ConfigLoader()
        charts = loader.charts_path
        assert charts.name == "charts"
        assert charts.parent.name == "outputs"
