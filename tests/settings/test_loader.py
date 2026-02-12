from __future__ import annotations

from pathlib import Path

from chartkit.settings.loader import ConfigLoader, configure, get_config, reset_config
from chartkit.settings.schema import ChartingConfig


class TestConfigLoader:
    def test_default_config_loads(self) -> None:
        config = get_config()
        assert isinstance(config, ChartingConfig)

    def test_configure_overrides(self) -> None:
        configure(branding={"company_name": "TestCo"})
        config = get_config()
        assert config.branding.company_name == "TestCo"

    def test_reset_clears_overrides(self) -> None:
        configure(branding={"company_name": "TestCo"})
        reset_config()
        config = get_config()
        assert config.branding.company_name == ""

    def test_config_cached(self) -> None:
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_invalidate_after_configure(self) -> None:
        config1 = get_config()
        configure(branding={"company_name": "New"})
        config2 = get_config()
        assert config1 is not config2


class TestPathResolution:
    def test_outputs_path_default(self) -> None:
        loader = ConfigLoader()
        path = loader.outputs_path
        assert path.name == "outputs"

    def test_outputs_path_explicit(self, tmp_path: Path) -> None:
        loader = ConfigLoader()
        loader.configure(outputs_path=tmp_path / "custom_out")
        assert loader.outputs_path == tmp_path / "custom_out"

    def test_charts_path_subdirectory(self) -> None:
        loader = ConfigLoader()
        charts = loader.charts_path
        # Default: outputs / "charts"
        assert charts.name == "charts"
        assert charts.parent.name == "outputs"

    def test_assets_path_default(self) -> None:
        loader = ConfigLoader()
        path = loader.assets_path
        assert path.name == "assets"


class TestTomlLoading:
    def test_load_toml_file(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        toml_file = tmp_path / ".charting.toml"
        toml_file.write_text('[branding]\ncompany_name = "FromToml"\n')
        (tmp_path / ".git").mkdir()

        loader = ConfigLoader()
        config = loader.get_config()
        assert config.branding.company_name == "FromToml"

    def test_pyproject_section_extraction(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[project]\nname = "test"\n\n'
            '[tool.charting.branding]\ncompany_name = "FromPyproject"\n'
        )

        loader = ConfigLoader()
        config = loader.get_config()
        assert config.branding.company_name == "FromPyproject"

    def test_merge_chain_precedence(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        # pyproject has lower precedence
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[project]\nname = "test"\n\n'
            '[tool.charting.branding]\ncompany_name = "FromPyproject"\n'
        )
        # .charting.toml has higher precedence
        charting = tmp_path / ".charting.toml"
        charting.write_text('[branding]\ncompany_name = "FromCharting"\n')

        loader = ConfigLoader()
        config = loader.get_config()
        assert config.branding.company_name == "FromCharting"
