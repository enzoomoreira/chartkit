# Examples

Brazilian macro series rendered with chartkit. Each script is a complete,
runnable file: read one top to bottom and you have the whole recipe.

```bash
uv run python examples/render_all.py      # render every chart
uv run python examples/01_ipca_acumulado.py   # or just one
```

Output goes to `docs/assets/gallery/`.

## The data is illustrative

`_data.py` generates synthetic series from a fixed seed. Their orders of
magnitude follow the real indicators closely enough that the formatting and
frequency handling on display are the ones you would actually hit, but **they
are not observations and must not be cited**. For real data use the BCB SGS
or IBGE SIDRA APIs.

## The charts

| Script | Chart | What it shows |
|--------|-------|---------------|
| `01_ipca_acumulado.py` | `ipca_acumulado.png` | Transform chain: `accum()` compounds monthly prints into the headline 12-month rate, with a moving average and highlighted extremes |
| `02_selic_e_ipca.py` | `selic_e_ipca.png` | `compose()` with dual axes: policy rate as a line, monthly inflation as bars, one consolidated legend |
| `03_cambio_drawdown.py` | `cambio_banda.png`, `cambio_drawdown.png` | BRL currency formatting, `ath`/`atl`/`std_band` metrics, and the same series re-read as a drawdown |
| `04_pib_trimestral.py` | `pib_trimestral.png` | Quarterly bars on a categorical axis with a zero reference line |

## Why these are committed

The rendered PNGs are tracked, so re-running `render_all.py` after a change
produces a visual diff. The structural snapshots in `tests/visual/` assert
that a footer exists and that a series has the colour it was given; they
cannot assert that the result looks right. Spacing, weight and palette
contrast are only reviewable by eye, and this is where that review happens.
