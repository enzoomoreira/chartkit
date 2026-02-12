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

    obstacles = _collect_obstacles(ax_left, [left_label])

    # Lines are excluded: their bbox spans the entire data area
    assert left_line not in obstacles
    # Patches from sibling axes are detected
    assert right_bar in obstacles
    # Labels from sibling axes are obstacles for cross-axis avoidance
    assert right_label in obstacles

    plt.close(fig)
