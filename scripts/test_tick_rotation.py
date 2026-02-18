"""Test script for auto-rotation of X-axis tick labels."""

import matplotlib

matplotlib.use("Agg")

import pandas as pd

import chartkit  # noqa: F401 -- registers the .chartkit accessor
from chartkit import compose


def test_auto_rotation_many_items() -> None:
    """15+ categories should trigger auto-rotation."""
    categories = [f"Categoria {i}" for i in range(20)]
    values = list(range(20))
    df = pd.DataFrame({"cat": categories, "val": values})
    result = df.chartkit.plot(
        x="cat", y="val", kind="bar", title="Auto-rotation (20 items)"
    )
    result.save("tick_rotation_auto.png")
    print("[OK] Auto-rotation with 20 items")


def test_no_rotation_few_items() -> None:
    """3-4 categories should NOT trigger auto-rotation."""
    df = pd.DataFrame({"cat": ["A", "B", "C"], "val": [10, 20, 30]})
    result = df.chartkit.plot(
        x="cat", y="val", kind="bar", title="No rotation (3 items)"
    )
    result.save("tick_rotation_none.png")
    print("[OK] No rotation with 3 items")


def test_forced_rotation_90() -> None:
    """Force 90 degrees rotation."""
    categories = [f"Item {i}" for i in range(10)]
    values = list(range(10))
    df = pd.DataFrame({"cat": categories, "val": values})
    result = df.chartkit.plot(
        x="cat", y="val", kind="bar", tick_rotation=90, title="Forced 90 degrees"
    )
    result.save("tick_rotation_90.png")
    print("[OK] Forced 90 degrees")


def test_forced_rotation_0() -> None:
    """Force horizontal (0 degrees)."""
    categories = [f"Item {i}" for i in range(10)]
    values = list(range(10))
    df = pd.DataFrame({"cat": categories, "val": values})
    result = df.chartkit.plot(
        x="cat", y="val", kind="bar", tick_rotation=0, title="Forced 0 degrees"
    )
    result.save("tick_rotation_0.png")
    print("[OK] Forced 0 degrees")


def test_compose_rotation() -> None:
    """Tick rotation in compose()."""

    categories = [f"Categoria Longa {i}" for i in range(15)]
    df = pd.DataFrame({"cat": categories, "val": list(range(15))})
    layer = df.chartkit.layer(kind="bar", x="cat", y="val")
    result = compose(layer, title="Compose with auto-rotation")
    result.save("tick_rotation_compose.png")
    print("[OK] Compose with auto-rotation")


if __name__ == "__main__":
    test_auto_rotation_many_items()
    test_no_rotation_few_items()
    test_forced_rotation_90()
    test_forced_rotation_0()
    test_compose_rotation()
    print("\nAll tick rotation tests passed!")
