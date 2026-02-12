from __future__ import annotations

from unittest.mock import MagicMock

from matplotlib.transforms import Bbox

from chartkit._internal.collision import _get_padded_bbox


def _mock_artist(bbox: Bbox) -> MagicMock:
    """Create a mock artist that returns the given bbox."""
    artist = MagicMock()
    artist.get_window_extent.return_value = bbox
    return artist


def test_normal_bbox_expanded() -> None:
    bbox = Bbox.from_extents(100, 100, 200, 150)
    artist = _mock_artist(bbox)
    result = _get_padded_bbox(artist, None, 5.0)
    # expanded should increase the bbox
    assert result.x0 < bbox.x0
    assert result.y0 < bbox.y0
    assert result.x1 > bbox.x1
    assert result.y1 > bbox.y1


def test_zero_width_bbox_uses_extents() -> None:
    # Width < 1px
    bbox = Bbox.from_extents(100, 100, 100.5, 150)
    artist = _mock_artist(bbox)
    result = _get_padded_bbox(artist, None, 5.0)
    assert result.x0 == bbox.x0 - 5.0
    assert result.x1 == bbox.x1 + 5.0


def test_zero_height_bbox_uses_extents() -> None:
    # Height < 1px
    bbox = Bbox.from_extents(100, 100, 200, 100.5)
    artist = _mock_artist(bbox)
    result = _get_padded_bbox(artist, None, 5.0)
    assert result.y0 == bbox.y0 - 5.0
    assert result.y1 == bbox.y1 + 5.0


def test_padding_amount_correct() -> None:
    import pytest

    bbox = Bbox.from_extents(100, 100, 200, 200)
    artist = _mock_artist(bbox)
    padding = 10.0
    result = _get_padded_bbox(artist, None, padding)
    # 100x100 bbox: expansion = 1 + 10/100 = 1.1
    # Width/height: 100 -> 110 (5px each side), center stays at (150, 150)
    assert result.width == pytest.approx(110.0)
    assert result.height == pytest.approx(110.0)
    center_x = (result.x0 + result.x1) / 2
    center_y = (result.y0 + result.y1) / 2
    assert center_x == pytest.approx(150.0)
    assert center_y == pytest.approx(150.0)
