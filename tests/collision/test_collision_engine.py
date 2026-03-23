"""Collision engine tests: PathObstacle, registration, and resolution.

Consolidates: test_pos_to_numeric.py + test_collect_obstacles.py.
Adds new tests for PathObstacle intersection, register_artist_obstacle storage,
colocate skip behavior, post-resolution label bounds, proactive candidates,
and cost function.
"""

from __future__ import annotations

from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import pytest
from matplotlib.path import Path as MplPath
from matplotlib.transforms import Bbox

matplotlib.use("Agg")

from chartkit._internal.collision import (
    _PathObstacle,
    _collect_obstacles,
    _pos_to_numeric,
    register_artist_obstacle,
    register_moveable,
    resolve_collisions,
    _artist_obstacles,
    _labels,
)
from chartkit._internal.collision._engine import (
    _compute_placement_cost,
    _edge_proximity_cost,
    _generate_proactive_candidates,
)


@pytest.fixture(autouse=True)
def _cleanup_collision_state() -> None:
    """Clear global collision state before and after each test."""
    _labels.clear()  # type: ignore[attr-defined]
    _artist_obstacles.clear()  # type: ignore[attr-defined]
    yield  # type: ignore[misc]
    _labels.clear()  # type: ignore[attr-defined]
    _artist_obstacles.clear()  # type: ignore[attr-defined]


class TestPosToNumeric:
    def test_float_passthrough(self) -> None:
        x, y = _pos_to_numeric(1.0, 2.0)
        assert x == 1.0
        assert y == 2.0

    def test_datetime_converted(self) -> None:
        dt = datetime(2023, 6, 15)
        x, y = _pos_to_numeric(dt, 5.0)
        assert isinstance(x, float)
        assert x > 0

    def test_timestamp_converted(self) -> None:
        ts = pd.Timestamp("2023-06-15")
        x, y = _pos_to_numeric(ts, 10.0)
        assert isinstance(x, float)
        assert x > 0


class TestPathObstacle:
    def test_filled_rectangle_intersects_overlapping_bbox(self) -> None:
        """A filled PathObstacle from a bar-like rectangle detects overlap."""
        fig, ax = plt.subplots()
        bar = ax.bar([1], [5], width=1.0)[0]
        fig.draw_without_rendering()

        rect_path = MplPath(
            [[100, 100], [200, 100], [200, 300], [100, 300], [100, 100]]
        )
        obs = _PathObstacle(ax, bar, [rect_path], filled=True, debug_color="red")
        renderer = fig.canvas.get_renderer()

        overlapping = Bbox.from_extents(150, 150, 250, 250)
        assert obs.intersects(overlapping, renderer) is True

        distant = Bbox.from_extents(500, 500, 600, 600)
        assert obs.intersects(distant, renderer) is False
        plt.close(fig)

    def test_unfilled_line_intersects_only_on_path(self) -> None:
        """An unfilled PathObstacle (line) only intersects where the path crosses."""
        fig, ax = plt.subplots()
        line = ax.plot([0, 10], [0, 10])[0]
        fig.draw_without_rendering()

        line_path = MplPath([[0, 0], [100, 100]])
        obs = _PathObstacle(ax, line, [line_path], filled=False, debug_color="orange")
        renderer = fig.canvas.get_renderer()

        # Bbox on the diagonal line path
        on_path = Bbox.from_extents(40, 40, 60, 60)
        assert obs.intersects(on_path, renderer) is True

        # Bbox far from the line path
        off_path = Bbox.from_extents(0, 80, 20, 100)
        assert obs.intersects(off_path, renderer) is False
        plt.close(fig)


class TestRegisterArtistObstacle:
    def test_stores_in_dict(self) -> None:
        """register_artist_obstacle appends to the global WeakKeyDictionary."""
        fig, ax = plt.subplots()
        line = ax.plot([1, 2], [3, 4])[0]

        register_artist_obstacle(ax, line, filled=False, colocate=True)

        entries = _artist_obstacles.get(ax, [])
        assert len(entries) == 1
        artist, filled, colocate = entries[0]
        assert artist is line
        assert filled is False
        assert colocate is True
        plt.close(fig)


class TestCollectObstacles:
    def test_twinx_patches_detected_as_obstacles(self) -> None:
        """Patches from sibling axes (twinx) are detected as obstacles."""
        fig, ax_left = plt.subplots()
        ax_right = ax_left.twinx()

        left_line = ax_left.plot([1, 2, 3], [1, 2, 3])[0]
        right_bar = ax_right.bar([1, 2, 3], [3, 2, 1], width=0.5)[0]

        left_label = ax_left.text(3, 3, "L")
        register_moveable(ax_left, left_label)

        fig.draw_without_rendering()
        renderer = fig.canvas.get_renderer()

        obstacles = _collect_obstacles(ax_left, [left_label], renderer)
        obstacle_artists = {obs._artist for obs in obstacles}

        assert right_bar in obstacle_artists
        assert left_line not in obstacle_artists
        plt.close(fig)


class TestColocateSkip:
    def test_colocate_label_not_repelled_by_own_line(self) -> None:
        """A label with colocate=True is not repelled by its own line."""
        fig, ax = plt.subplots()
        line = ax.plot([0, 1, 2, 3], [10, 20, 30, 40])[0]
        label = ax.text(3, 40, "40")

        register_moveable(ax, label)
        register_artist_obstacle(ax, line, filled=False, colocate=True)

        fig.draw_without_rendering()
        renderer = fig.canvas.get_renderer()

        pos_before = label.get_position()
        resolve_collisions(ax)
        pos_after = label.get_position()

        # Label should stay at or very near its original position
        assert abs(pos_before[0] - pos_after[0]) < 1.0
        assert abs(pos_before[1] - pos_after[1]) < 5.0
        plt.close(fig)


class TestLabelBounds:
    def test_label_stays_within_axes_bbox(self) -> None:
        """After resolution, labels remain within the axes bounding box."""
        fig, ax = plt.subplots()
        ax.plot([0, 1, 2, 3, 4], [10, 20, 15, 25, 30])

        labels = []
        for x, y in [(4, 30), (4, 29)]:
            lbl = ax.text(x, y, f"{y}")
            register_moveable(ax, lbl)
            labels.append(lbl)

        resolve_collisions(ax)

        fig.draw_without_rendering()
        renderer = fig.canvas.get_renderer()
        axes_bbox = ax.get_window_extent(renderer)

        for lbl in labels:
            lbl_bbox = lbl.get_window_extent(renderer)
            assert lbl_bbox.x0 >= axes_bbox.x0 - 1  # small tolerance
            assert lbl_bbox.y0 >= axes_bbox.y0 - 1
        plt.close(fig)


class TestProactiveCandidates:
    def test_generates_8_directions_per_distance(self) -> None:
        """Each distance multiplier yields up to 8 directional candidates."""
        anchor = Bbox.from_extents(100, 100, 130, 120)
        label = Bbox.from_extents(100, 100, 130, 120)
        axes = Bbox.from_extents(0, 0, 1000, 1000)

        candidates = _generate_proactive_candidates(
            anchor, label, axes, distances=(1.0,)
        )
        assert len(candidates) == 8

        candidates_multi = _generate_proactive_candidates(
            anchor, label, axes, distances=(1.0, 2.0)
        )
        assert len(candidates_multi) == 16

    def test_respects_axes_bounds(self) -> None:
        """Candidates that would place the label outside axes are excluded."""
        # Label near the top-left corner
        anchor = Bbox.from_extents(5, 180, 35, 200)
        label = Bbox.from_extents(5, 180, 35, 200)
        axes = Bbox.from_extents(0, 0, 200, 200)

        candidates = _generate_proactive_candidates(
            anchor, label, axes, distances=(1.0,)
        )

        for dx, dy, _ in candidates:
            new_x0 = label.x0 + dx
            new_x1 = label.x1 + dx
            new_y0 = label.y0 + dy
            new_y1 = label.y1 + dy
            assert new_x0 >= axes.x0
            assert new_x1 <= axes.x1
            assert new_y0 >= axes.y0
            assert new_y1 <= axes.y1

        # Should have fewer than 8 (corner clips several directions)
        assert len(candidates) < 8

    def test_diagonal_distance_normalized(self) -> None:
        """Diagonal candidates have the same effective distance as cardinal ones."""
        anchor = Bbox.from_extents(400, 400, 430, 420)
        label = Bbox.from_extents(400, 400, 430, 420)
        axes = Bbox.from_extents(0, 0, 1000, 1000)

        candidates = _generate_proactive_candidates(
            anchor, label, axes, distances=(1.0,)
        )

        distances = [d for _, _, d in candidates]
        # All distances should be approximately equal (label_height = 20)
        assert max(distances) - min(distances) < 1.0


class TestPlacementCost:
    def test_distance_monotonicity(self) -> None:
        """Larger displacement from anchor yields higher cost."""
        anchor = Bbox.from_extents(100, 100, 130, 120)
        label = Bbox.from_extents(100, 100, 130, 120)
        axes = Bbox.from_extents(0, 0, 1000, 1000)

        cost_near = _compute_placement_cost(0, 20, anchor, label, axes, "y", 20.0)
        cost_far = _compute_placement_cost(0, 60, anchor, label, axes, "y", 20.0)
        assert cost_far > cost_near

    def test_axis_preference_y_movement(self) -> None:
        """Y-only movement is cheaper than X-only when movement='y'."""
        anchor = Bbox.from_extents(100, 100, 130, 120)
        label = Bbox.from_extents(100, 100, 130, 120)
        axes = Bbox.from_extents(0, 0, 1000, 1000)

        # Same magnitude, different axis
        cost_y = _compute_placement_cost(0, 30, anchor, label, axes, "y", 20.0)
        cost_x = _compute_placement_cost(30, 0, anchor, label, axes, "y", 20.0)
        assert cost_y < cost_x

    def test_axis_preference_x_movement(self) -> None:
        """X-only movement is cheaper than Y-only when movement='x'."""
        anchor = Bbox.from_extents(100, 100, 130, 120)
        label = Bbox.from_extents(100, 100, 130, 120)
        axes = Bbox.from_extents(0, 0, 1000, 1000)

        cost_x = _compute_placement_cost(30, 0, anchor, label, axes, "x", 20.0)
        cost_y = _compute_placement_cost(0, 30, anchor, label, axes, "x", 20.0)
        assert cost_x < cost_y

    def test_edge_penalty(self) -> None:
        """Labels near the axes edge get penalized."""
        anchor = Bbox.from_extents(100, 100, 130, 120)
        label = Bbox.from_extents(100, 100, 130, 120)
        axes = Bbox.from_extents(0, 0, 500, 500)
        margin = 20.0

        # Move to center vs move near bottom edge
        cost_center = _compute_placement_cost(0, 100, anchor, label, axes, "y", margin)
        # Move near bottom edge (label at y=5..25, within 20px margin)
        cost_edge = _compute_placement_cost(0, -95, anchor, label, axes, "y", margin)
        assert cost_edge > cost_center

    def test_edge_proximity_cost_zero_when_far(self) -> None:
        """No edge penalty when label is far from all edges."""
        bbox = Bbox.from_extents(200, 200, 230, 220)
        axes = Bbox.from_extents(0, 0, 500, 500)
        assert _edge_proximity_cost(bbox, axes, 20.0) == 0.0

    def test_edge_proximity_cost_max_at_border(self) -> None:
        """Edge penalty is 1.0 when label touches the axes border."""
        bbox = Bbox.from_extents(0, 200, 30, 220)
        axes = Bbox.from_extents(0, 0, 500, 500)
        assert _edge_proximity_cost(bbox, axes, 20.0) == 1.0


class TestBestCostSelection:
    def test_two_labels_find_reasonable_positions(self) -> None:
        """Two overlapping labels both find positions without extreme displacement."""
        fig, ax = plt.subplots()
        ax.plot([0, 1, 2, 3, 4], [10, 20, 15, 25, 30])

        labels = []
        for x, y in [(4, 30), (4, 29)]:
            lbl = ax.text(x, y, f"{y}")
            register_moveable(ax, lbl)
            labels.append(lbl)

        resolve_collisions(ax)

        fig.draw_without_rendering()
        renderer = fig.canvas.get_renderer()

        bboxes = [lbl.get_window_extent(renderer) for lbl in labels]
        # Labels should not overlap after resolution
        assert not bboxes[0].overlaps(bboxes[1])

        # Neither label should be excessively displaced (> 100px from original)
        for lbl in labels:
            pos = lbl.get_position()
            assert abs(pos[1] - 30) < 20 or abs(pos[1] - 29) < 20
        plt.close(fig)
