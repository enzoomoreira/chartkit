from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Temporary directory with a pyproject.toml marker."""
    marker = tmp_path / "pyproject.toml"
    marker.write_text("[project]\nname = 'test'\n")
    return tmp_path
