from __future__ import annotations

from pathlib import Path

from chartkit.settings.discovery import (
    find_config_files,
    find_project_root,
    get_user_config_dir,
    reset_project_root_cache,
)


class TestFindProjectRoot:
    def test_finds_git_dir(self, tmp_path: Path) -> None:
        reset_project_root_cache()
        (tmp_path / ".git").mkdir()
        result = find_project_root(start_path=tmp_path)
        assert result == tmp_path

    def test_finds_pyproject_toml(self, tmp_path: Path) -> None:
        reset_project_root_cache()
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")
        result = find_project_root(start_path=tmp_path)
        assert result == tmp_path

    def test_walks_up_tree(self, tmp_path: Path) -> None:
        reset_project_root_cache()
        (tmp_path / ".git").mkdir()
        nested = tmp_path / "a" / "b" / "c"
        nested.mkdir(parents=True)
        result = find_project_root(start_path=nested)
        assert result == tmp_path

    def test_no_marker_returns_none(self, tmp_path: Path, monkeypatch) -> None:
        reset_project_root_cache()
        monkeypatch.setattr(
            "chartkit.settings.discovery.PROJECT_ROOT_MARKERS",
            ("__nonexistent_marker_file_12345__",),
        )
        isolated = tmp_path / "isolated"
        isolated.mkdir()
        result = find_project_root(start_path=isolated)
        assert result is None

    def test_caching_works(self, tmp_path: Path) -> None:
        reset_project_root_cache()
        (tmp_path / ".git").mkdir()
        result1 = find_project_root(start_path=tmp_path)
        result2 = find_project_root(start_path=tmp_path)
        assert result1 == result2


class TestFindConfigFiles:
    def test_finds_charting_toml(self, tmp_path: Path, monkeypatch) -> None:
        reset_project_root_cache()
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".charting.toml").write_text("[branding]\n")
        files = find_config_files(project_root=tmp_path)
        assert any(f.name == ".charting.toml" for f in files)

    def test_finds_pyproject_toml(self, tmp_path: Path, monkeypatch) -> None:
        reset_project_root_cache()
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text("[tool.charting]\n")
        files = find_config_files(project_root=tmp_path)
        assert any(f.name == "pyproject.toml" for f in files)

    def test_empty_when_nothing_exists(self, tmp_path: Path, monkeypatch) -> None:
        reset_project_root_cache()
        isolated = tmp_path / "clean"
        isolated.mkdir()
        monkeypatch.chdir(isolated)
        files = find_config_files(project_root=isolated)
        assert files == []


class TestGetUserConfigDir:
    def test_returns_path(self) -> None:
        result = get_user_config_dir()
        # On Windows, returns Path; on Linux too
        assert result is None or isinstance(result, Path)
