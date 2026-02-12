from __future__ import annotations

from chartkit.settings.loader import _deep_merge


class TestDeepMerge:
    def test_flat_dicts(self) -> None:
        result = _deep_merge({"a": 1}, {"b": 2})
        assert result == {"a": 1, "b": 2}

    def test_override_value(self) -> None:
        result = _deep_merge({"a": 1}, {"a": 2})
        assert result == {"a": 2}

    def test_nested_merge(self) -> None:
        result = _deep_merge({"a": {"x": 1}}, {"a": {"y": 2}})
        assert result == {"a": {"x": 1, "y": 2}}

    def test_nested_override(self) -> None:
        result = _deep_merge({"a": {"x": 1}}, {"a": {"x": 2}})
        assert result == {"a": {"x": 2}}

    def test_list_replaced(self) -> None:
        result = _deep_merge({"a": [1]}, {"a": [2, 3]})
        assert result == {"a": [2, 3]}

    def test_dict_replaces_scalar(self) -> None:
        result = _deep_merge({"a": 1}, {"a": {"x": 1}})
        assert result == {"a": {"x": 1}}

    def test_scalar_replaces_dict(self) -> None:
        result = _deep_merge({"a": {"x": 1}}, {"a": 1})
        assert result == {"a": 1}

    def test_empty_base(self) -> None:
        result = _deep_merge({}, {"a": 1})
        assert result == {"a": 1}
