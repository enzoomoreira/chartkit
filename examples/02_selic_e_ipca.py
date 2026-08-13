"""Policy rate against inflation: the chart every Brazilian macro deck opens with.

Two series on two scales -- Selic in percent per year, IPCA in percent per
month -- which is what ``compose()`` and ``axis='right'`` exist for. The
palette advances across both layers, so the consolidated legend never shows
one colour standing for two series.
"""

from __future__ import annotations

from pathlib import Path

from _data import ipca_monthly, selic_target

import chartkit  # noqa: F401  -- registers the .chartkit accessor
from chartkit import compose

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "assets" / "gallery"


def main() -> None:
    selic = selic_target().chartkit.layer(units="%", highlight=["last"])
    ipca = ipca_monthly().chartkit.layer(kind="bar", units="%", axis="right")

    compose(
        selic,
        ipca,
        title="Selic e IPCA mensal",
        source="Dados ilustrativos",
        ylabel="Selic (% a.a.)",
    ).save(str(OUTPUT / "selic_e_ipca.png")).close()


if __name__ == "__main__":
    main()
