"""IPCA: monthly prints compounded into the headline 12-month rate.

The transform chain does the arithmetic this series always needs. ``accum``
compounds the monthly changes rather than summing them, and takes its window
from the detected frequency, so ``ma:12`` lands on a comparable scale without
the window being restated.
"""

from __future__ import annotations

from pathlib import Path

from _data import ipca_monthly

import chartkit  # noqa: F401  -- registers the .chartkit accessor

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "assets" / "gallery"


def main() -> None:
    (
        ipca_monthly()
        .chartkit.accum()
        .plot(
            title="IPCA acumulado em 12 meses",
            units="%",
            source="Dados ilustrativos",
            ylabel="Variação acumulada",
            highlight=["last", "max"],
            metrics=["ma:12|Média do período"],
        )
        .save(str(OUTPUT / "ipca_acumulado.png"))
        .close()
    )


if __name__ == "__main__":
    main()
