"""USD/BRL and the drawdown of the real against the dollar.

Reference metrics carry the reading: ``ath``/``atl`` mark the extremes of the
period and ``std_band`` shows the range the rate spent most of its time in.
The band is a rolling one, so it opens on its twelfth point rather than
pretending to describe a window it has not seen yet.
"""

from __future__ import annotations

from pathlib import Path

from _data import usd_brl

import chartkit  # noqa: F401  -- registers the .chartkit accessor

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "assets" / "gallery"


def main() -> None:
    df = usd_brl()

    df.chartkit.plot(
        title="USD/BRL com banda de desvio padrão",
        units="BRL",
        source="Dados ilustrativos",
        ylabel="Reais por dólar",
        highlight=["last"],
        metrics=[
            "ath|Máxima do período",
            "atl|Mínima do período",
            "std_band:12:2|Banda 2 desvios",
        ],
    ).save(str(OUTPUT / "cambio_banda.png")).close()

    # Drawdown answers a different question from the level: how far the real
    # sits below its strongest reading, which is what a hedging deck asks.
    df.chartkit.drawdown().plot(
        title="USD/BRL: distância do pico",
        units="%",
        source="Dados ilustrativos",
        ylabel="Queda desde a máxima",
        kind="area",
        highlight=["min"],
    ).save(str(OUTPUT / "cambio_drawdown.png")).close()


if __name__ == "__main__":
    main()
