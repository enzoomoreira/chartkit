"""Render every gallery example into docs/assets/gallery.

Run from the repository root:

    uv run python examples/render_all.py

The rendered files are committed, so the diff of a run is a visual review of
whatever changed in the theme -- the one kind of regression the structural
snapshots in tests/visual cannot catch.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

EXAMPLES = Path(__file__).resolve().parent
OUTPUT = EXAMPLES.parent / "docs" / "assets" / "gallery"


def main() -> None:
    sys.path.insert(0, str(EXAMPLES))
    OUTPUT.mkdir(parents=True, exist_ok=True)

    scripts = sorted(p.stem for p in EXAMPLES.glob("[0-9]*.py"))
    for name in scripts:
        module = importlib.import_module(name)
        module.main()
        print(f"rendered: {name}")

    written = sorted(p.name for p in OUTPUT.glob("*.png"))
    print(f"\n{len(written)} chart(s) in {OUTPUT.relative_to(EXAMPLES.parent)}:")
    for filename in written:
        print(f"  {filename}")


if __name__ == "__main__":
    main()
