from __future__ import annotations

from chartkit.settings.schema import ChartingConfig


class TestChartingConfigDefaults:
    def test_default_values(self) -> None:
        ChartingConfig._toml_data = {}
        config = ChartingConfig()
        assert config.layout.dpi == 300
        assert config.layout.figsize == (10.0, 6.0)
        assert config.branding.company_name == ""
        assert config.colors.primary is not None

    def test_nested_access(self) -> None:
        ChartingConfig._toml_data = {}
        config = ChartingConfig()
        assert isinstance(config.layout.figsize, tuple)
        assert config.formatters.locale.decimal == ","
        assert config.formatters.locale.thousands == "."

    def test_colors_cycle(self) -> None:
        ChartingConfig._toml_data = {}
        config = ChartingConfig()
        cycle = config.colors.cycle()
        assert isinstance(cycle, list)
        assert len(cycle) == 6


class TestSubConfigs:
    def test_transforms_config_defaults(self) -> None:
        ChartingConfig._toml_data = {}
        config = ChartingConfig()
        assert config.transforms.normalize_base == 100
        assert config.transforms.accum_window == 12

    def test_paths_config_defaults(self) -> None:
        ChartingConfig._toml_data = {}
        config = ChartingConfig()
        assert config.paths.charts_subdir == "charts"
        assert config.paths.outputs_dir == ""

    def test_collision_config_defaults(self) -> None:
        ChartingConfig._toml_data = {}
        config = ChartingConfig()
        assert config.collision.movement == "y"
        assert config.collision.max_iterations == 50

    def test_formatters_locale_defaults(self) -> None:
        ChartingConfig._toml_data = {}
        config = ChartingConfig()
        assert config.formatters.locale.babel_locale == "pt_BR"

    def test_branding_config_defaults(self) -> None:
        ChartingConfig._toml_data = {}
        config = ChartingConfig()
        assert config.branding.company_name == ""
        assert "{source}" in config.branding.footer_format


class TestEnvVars:
    def test_env_prefix(self, monkeypatch) -> None:
        ChartingConfig._toml_data = {}
        monkeypatch.setenv("CHARTKIT_LAYOUT__DPI", "72")
        config = ChartingConfig()
        assert config.layout.dpi == 72

    def test_nested_env_delimiter(self, monkeypatch) -> None:
        ChartingConfig._toml_data = {}
        monkeypatch.setenv("CHARTKIT_BRANDING__COMPANY_NAME", "EnvCorp")
        config = ChartingConfig()
        assert config.branding.company_name == "EnvCorp"
