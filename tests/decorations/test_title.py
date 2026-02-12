from __future__ import annotations

import matplotlib.pyplot as plt
import pytest

from chartkit.decorations.title import add_title


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


class TestAddTitle:
    def test_none_title_no_change(self) -> None:
        _, ax = plt.subplots()
        add_title(ax, None)
        assert ax.get_title() == ""

    def test_empty_string_no_change(self) -> None:
        _, ax = plt.subplots()
        add_title(ax, "")
        assert ax.get_title() == ""

    def test_title_applied(self) -> None:
        _, ax = plt.subplots()
        add_title(ax, "Revenue Growth")
        assert ax.get_title() == "Revenue Growth"

    def test_title_with_special_chars(self) -> None:
        _, ax = plt.subplots()
        add_title(ax, "Variacao % (YoY)")
        assert ax.get_title() == "Variacao % (YoY)"
