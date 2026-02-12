from __future__ import annotations

import pytest

from chartkit._internal.formatting import FORMATTERS


class TestFormatters:
    EXPECTED_KEYS = {"BRL", "USD", "BRL_compact", "USD_compact", "%", "human", "points"}

    def test_all_keys_present(self) -> None:
        assert set(FORMATTERS.keys()) == self.EXPECTED_KEYS

    @pytest.mark.parametrize("key", sorted(EXPECTED_KEYS))
    def test_factory_returns_callable(self, key: str) -> None:
        formatter = FORMATTERS[key]()
        assert callable(formatter)

    def test_missing_key_raises(self) -> None:
        with pytest.raises(KeyError):
            FORMATTERS["INVALID"]
