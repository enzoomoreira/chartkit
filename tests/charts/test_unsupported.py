from __future__ import annotations

import pytest

from chartkit.charts.renderer import ChartRenderer
from chartkit.exceptions import ValidationError


class TestUnsupportedKinds:
    @pytest.mark.parametrize("kind", ["imshow", "contour", "contourf", "pcolormesh"])
    def test_grid_kinds_raise(self, kind: str) -> None:
        with pytest.raises(ValidationError, match="not supported"):
            ChartRenderer.validate_kind(kind)

    @pytest.mark.parametrize("kind", ["quiver", "streamplot", "barbs"])
    def test_vector_kinds_raise(self, kind: str) -> None:
        with pytest.raises(ValidationError, match="not supported"):
            ChartRenderer.validate_kind(kind)

    def test_spy_raises(self) -> None:
        with pytest.raises(ValidationError, match="not supported"):
            ChartRenderer.validate_kind("spy")
