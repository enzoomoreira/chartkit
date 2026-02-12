from __future__ import annotations

import pytest
from matplotlib.transforms import Bbox

from chartkit._internal.collision import _best_displacement


# Axes bbox: 0-500 x 0-400 pixel space
AXES_BBOX = Bbox.from_extents(0, 0, 500, 400)
PADDING = 5.0


class TestBestDisplacementVertical:
    def test_overlap_picks_smallest_y(self) -> None:
        # mov y=[100,120], fix y=[110,130], padding=5
        # dy_up = 130+5-100 = 35, dy_down = 110-5-120 = -15
        # Smallest: |dy_down|=15 < |dy_up|=35 -> moves down
        mov = Bbox.from_extents(100, 100, 150, 120)
        fix = Bbox.from_extents(100, 110, 150, 130)
        result = _best_displacement(mov, fix, "y", PADDING, AXES_BBOX)
        assert result is not None
        dx, dy = result
        assert dx == 0
        assert dy == pytest.approx(-15.0)

    def test_overlap_y_picks_up_when_smaller(self) -> None:
        # mov y=[115,135], fix y=[100,120], padding=5
        # dy_up = 120+5-115 = 10, dy_down = 100-5-135 = -40
        # Smallest: |dy_up|=10 < |dy_down|=40 -> moves up
        mov = Bbox.from_extents(100, 115, 150, 135)
        fix = Bbox.from_extents(100, 100, 150, 120)
        result = _best_displacement(mov, fix, "y", PADDING, AXES_BBOX)
        assert result is not None
        dx, dy = result
        assert dx == 0
        assert dy == pytest.approx(10.0)

    def test_overlap_x_mode(self) -> None:
        # mov x=[100,150], fix x=[130,180], padding=5
        # dx_right = 180+5-100 = 85, dx_left = 130-5-150 = -25
        # Smallest: |dx_left|=25 < |dx_right|=85 -> moves left
        mov = Bbox.from_extents(100, 100, 150, 120)
        fix = Bbox.from_extents(130, 100, 180, 120)
        result = _best_displacement(mov, fix, "x", PADDING, AXES_BBOX)
        assert result is not None
        dx, dy = result
        assert dy == 0
        assert dx == pytest.approx(-25.0)

    def test_xy_mode_picks_smallest(self) -> None:
        # mov=(100,100,150,120), fix=(130,100,180,120), padding=5
        # Y: dy_up=25, dy_down=-25. X: dx_right=85, dx_left=-25.
        # Minimum absolute displacement = 25 (three options tied)
        mov = Bbox.from_extents(100, 100, 150, 120)
        fix = Bbox.from_extents(130, 100, 180, 120)
        result = _best_displacement(mov, fix, "xy", PADDING, AXES_BBOX)
        assert result is not None
        dx, dy = result
        assert abs(dx) + abs(dy) == pytest.approx(25.0)


class TestBestDisplacementBounds:
    def test_out_of_bounds_returns_none(self) -> None:
        # Tiny axes (30x30), mov 20x20, fix 10x10 centered, padding=10
        # dy_up = 20+10-5 = 25 -> new_y1=50 > 30. Out of bounds.
        # dy_down = 10-10-25 = -25 -> new_y0=-20 < 0. Out of bounds.
        small_axes = Bbox.from_extents(0, 0, 30, 30)
        mov = Bbox.from_extents(5, 5, 25, 25)
        fix = Bbox.from_extents(10, 10, 20, 20)
        result = _best_displacement(mov, fix, "y", 10.0, small_axes)
        assert result is None

    def test_padding_respected(self) -> None:
        mov = Bbox.from_extents(100, 100, 150, 120)
        fix = Bbox.from_extents(100, 110, 150, 130)
        result = _best_displacement(mov, fix, "y", PADDING, AXES_BBOX)
        assert result is not None
        dx, dy = result
        new_y0 = mov.y0 + dy
        new_y1 = mov.y1 + dy
        assert new_y0 >= fix.y1 + PADDING or new_y1 <= fix.y0 - PADDING


class TestBestDisplacementEdge:
    def test_equal_bboxes(self) -> None:
        box = Bbox.from_extents(100, 100, 150, 120)
        result = _best_displacement(box, box, "y", PADDING, AXES_BBOX)
        assert result is not None

    def test_no_options_y_only_at_boundary(self) -> None:
        # Moveable fills entire vertical space, fixed overlaps
        mov = Bbox.from_extents(100, 0, 150, 400)
        fix = Bbox.from_extents(100, 100, 150, 300)
        result = _best_displacement(mov, fix, "y", PADDING, AXES_BBOX)
        # Can't move up or down without going out of bounds
        assert result is None
