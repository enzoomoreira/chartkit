"""Quarterly GDP change, where the sign of each bar is the story.

The index is turned into "1T24" labels first, which is how quarterly GDP is
read in a Brazilian deck and also what bar charts want: on a categorical axis
each bar is one slot wide, whereas a datetime axis needs a width in days.
``hline:0`` draws the line between growth and contraction, which a reader
looks for before anything else.
"""

from __future__ import annotations

from pathlib import Path

from _data import gdp_quarterly

import chartkit  # noqa: F401  -- registers the .chartkit accessor

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "assets" / "gallery"


def main() -> None:
    df = gdp_quarterly()
    df.index = [f"{d.quarter}T{d.year % 100:02d}" for d in df.index]

    df.chartkit.plot(
        kind="bar",
        title="PIB: variação trimestral",
        units="%",
        source="Dados ilustrativos",
        ylabel="Variação sobre o trimestre anterior",
        highlight=["last", "min"],
        metrics=["hline:0"],
        y_origin="auto",
        # Twenty quarter labels sit flush against each other, and auto-rotation
        # tests for strict overlap, so it does not fire on labels that merely
        # touch. Ask for the angle instead of hoping it is detected.
        tick_rotation=45,
    ).save(str(OUTPUT / "pib_trimestral.png")).close()


if __name__ == "__main__":
    main()
