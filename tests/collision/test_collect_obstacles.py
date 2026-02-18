from __future__ import annotations

import matplotlib.pyplot as plt

from chartkit._internal.collision import _collect_obstacles, register_moveable


def test_collect_obstacles_includes_twinx_patches_and_labels() -> None:
    """Patches and labels from sibling axes are obstacles; lines are not."""
    fig, ax_left = plt.subplots()
    ax_right = ax_left.twinx()

    left_line = ax_left.plot([1, 2, 3], [1, 2, 3])[0]
    right_bar = ax_right.bar([1, 2, 3], [3, 2, 1], width=0.5)[0]

    left_label = ax_left.text(3, 3, "L")
    right_label = ax_right.text(3, 1, "R")
    register_moveable(ax_left, left_label)
    register_moveable(ax_right, right_label)

    fig.draw_without_rendering()
    renderer = fig.canvas.get_renderer()

    obstacles = _collect_obstacles(ax_left, [left_label], renderer)
    obstacle_artists = {obs._artist for obs in obstacles}

    # Lines are excluded: only registered artist obstacles create line paths
    assert left_line not in obstacle_artists
    # Patches from sibling axes are detected
    assert right_bar in obstacle_artists
    # Labels from sibling axes are obstacles for cross-axis avoidance
    assert right_label in obstacle_artists

    plt.close(fig)
