from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import matplotlib.pyplot as plt
import pytest

from chartkit._internal.saving import save_figure


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


@pytest.fixture
def fig() -> plt.Figure:
    f, _ = plt.subplots()
    return f


class TestSaveFigure:
    def test_absolute_path_saves_directly(
        self, fig: plt.Figure, tmp_path: Path
    ) -> None:
        target = tmp_path / "chart.png"
        save_figure(fig, str(target))
        assert target.exists()

    def test_relative_path_resolves_to_charts_dir(
        self, fig: plt.Figure, tmp_path: Path
    ) -> None:
        charts_dir = tmp_path / "charts"
        with patch(
            "chartkit._internal.saving.get_charts_path", return_value=charts_dir
        ):
            save_figure(fig, "my_chart.png")
        assert (charts_dir / "my_chart.png").exists()

    def test_creates_charts_dir_if_missing(
        self, fig: plt.Figure, tmp_path: Path
    ) -> None:
        charts_dir = tmp_path / "nonexistent" / "charts"
        assert not charts_dir.exists()
        with patch(
            "chartkit._internal.saving.get_charts_path", return_value=charts_dir
        ):
            save_figure(fig, "test.png")
        assert charts_dir.exists()

    def test_default_dpi_from_config(self, fig: plt.Figure, tmp_path: Path) -> None:
        target = tmp_path / "chart.png"
        mock_config = MagicMock()
        mock_config.layout.dpi = 150
        with patch("chartkit._internal.saving.get_config", return_value=mock_config):
            with patch.object(fig, "savefig", wraps=fig.savefig) as mock_save:
                save_figure(fig, str(target), dpi=None)
                mock_save.assert_called_once()
                assert mock_save.call_args.kwargs["dpi"] == 150

    def test_explicit_dpi_overrides_config(
        self, fig: plt.Figure, tmp_path: Path
    ) -> None:
        target = tmp_path / "chart.png"
        mock_config = MagicMock()
        mock_config.layout.dpi = 150
        with patch("chartkit._internal.saving.get_config", return_value=mock_config):
            with patch.object(fig, "savefig", wraps=fig.savefig) as mock_save:
                save_figure(fig, str(target), dpi=72)
                assert mock_save.call_args.kwargs["dpi"] == 72
