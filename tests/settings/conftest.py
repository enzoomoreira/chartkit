from __future__ import annotations

from pathlib import Path

import pytest

from chartkit.settings.loader import reset_config


@pytest.fixture(autouse=True)
def _isolate_config():
    """Reset config state before and after each test."""
    reset_config()
    yield
    reset_config()


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Temporary directory with a pyproject.toml marker."""
    marker = tmp_path / "pyproject.toml"
    marker.write_text("[project]\nname = 'test'\n")
    return tmp_path
