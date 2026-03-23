"""Project root and config file discovery tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from chartkit.settings.discovery import (
    find_config_files,
    find_project_root,
    get_user_config_dir,
    reset_project_root_cache,
)


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    """Ensure each test starts with a fresh cache."""
    reset_project_root_cache()


class TestFindProjectRoot:
    def test_finds_git_marker(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        assert find_project_root(start_path=tmp_path) == tmp_path

    def test_finds_pyproject_marker(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n")
        assert find_project_root(start_path=tmp_path) == tmp_path

    def test_walks_up_directory_tree(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        nested = tmp_path / "a" / "b" / "c"
        nested.mkdir(parents=True)
        assert find_project_root(start_path=nested) == tmp_path

    def test_returns_none_without_marker(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "chartkit.settings.discovery.PROJECT_ROOT_MARKERS",
            ("__nonexistent_marker_file_12345__",),
        )
        isolated = tmp_path / "isolated"
        isolated.mkdir()
        assert find_project_root(start_path=isolated) is None


class TestFindConfigFiles:
    def test_finds_dotfolder_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".chartkit").mkdir()
        (tmp_path / ".chartkit" / "config.toml").write_text("[branding]\n")
        files = find_config_files(project_root=tmp_path)
        assert any(f.name == "config.toml" and ".chartkit" in str(f) for f in files)

    def test_empty_when_no_configs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        isolated = tmp_path / "clean"
        isolated.mkdir()
        monkeypatch.chdir(isolated)
        assert find_config_files(project_root=isolated) == []


class TestUserConfigDir:
    def test_returns_path_or_none(self) -> None:
        result = get_user_config_dir()
        assert result is None or isinstance(result, Path)
