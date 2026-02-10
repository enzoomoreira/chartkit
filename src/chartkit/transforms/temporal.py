"""Transformacoes puras de series temporais.

Todas as funcoes seguem o contrato:
- Aceitam DataFrame, Series, dict, list ou ndarray (coercao automatica).
- Validam que dados sao numericos (warning + filtragem para non-numeric).
- Protegem contra inf (substituem por NaN no resultado).
- Funcoes que dependem de frequencia (mom, yoy, accum, annualize, compound_rolling)
  resolvem periods via auto-detect ou exigem freq=/periods= explicito.
"""

from __future__ import annotations

from typing import overload

import numpy as np
import pandas as pd

from ..exceptions import TransformError
from ..settings import get_config
from ._validation import (
    _NormalizeParams,
    _PctChangeParams,
    _RollingParams,
    coerce_input,
    resolve_periods,
    sanitize_result,
    validate_numeric,
    validate_params,
)


# ---------------------------------------------------------------------------
# mom / yoy -- variacao percentual
# ---------------------------------------------------------------------------


@overload
def mom(
    df: pd.DataFrame, periods: int | None = None, freq: str | None = None
) -> pd.DataFrame: ...
@overload
def mom(
    df: pd.Series, periods: int | None = None, freq: str | None = None
) -> pd.Series: ...
def mom(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    periods: int | None = None,
    freq: str | None = None,
) -> pd.DataFrame | pd.Series:
    """Variacao percentual mensal (Month-over-Month).

    Em dados mensais, ``periods=1`` compara com o mes anterior.
    A frequencia e detectada automaticamente; use ``freq=`` ou ``periods=``
    para override explicito.

    Args:
        df: Dados de entrada.
        periods: Numero de periodos para comparacao.
            Mutuamente exclusivo com ``freq``.
        freq: Frequencia dos dados (``'D'``, ``'B'``, ``'W'``, ``'M'``, ``'Q'``, ``'Y'``).
            Mutuamente exclusivo com ``periods``.
    """
    params = validate_params(_PctChangeParams, periods=periods, freq=freq)
    data = validate_numeric(coerce_input(df))
    resolved = resolve_periods(data, "mom", params.periods, params.freq)
    result = data.pct_change(periods=resolved) * 100
    return sanitize_result(result)


@overload
def yoy(
    df: pd.DataFrame, periods: int | None = None, freq: str | None = None
) -> pd.DataFrame: ...
@overload
def yoy(
    df: pd.Series, periods: int | None = None, freq: str | None = None
) -> pd.Series: ...
def yoy(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    periods: int | None = None,
    freq: str | None = None,
) -> pd.DataFrame | pd.Series:
    """Variacao percentual anual (Year-over-Year).

    Em dados mensais, ``periods=12`` compara com o mesmo mes do ano anterior.
    A frequencia e detectada automaticamente; use ``freq=`` ou ``periods=``
    para override explicito.

    Args:
        df: Dados de entrada.
        periods: Numero de periodos para comparacao.
            Mutuamente exclusivo com ``freq``.
        freq: Frequencia dos dados (``'D'``, ``'B'``, ``'W'``, ``'M'``, ``'Q'``, ``'Y'``).
            Mutuamente exclusivo com ``periods``.
    """
    params = validate_params(_PctChangeParams, periods=periods, freq=freq)
    data = validate_numeric(coerce_input(df))
    resolved = resolve_periods(data, "yoy", params.periods, params.freq)
    result = data.pct_change(periods=resolved) * 100
    return sanitize_result(result)


# ---------------------------------------------------------------------------
# accum -- variacao acumulada em janela movel
# ---------------------------------------------------------------------------


@overload
def accum(
    df: pd.DataFrame, window: int | None = None, freq: str | None = None
) -> pd.DataFrame: ...
@overload
def accum(
    df: pd.Series, window: int | None = None, freq: str | None = None
) -> pd.Series: ...
def accum(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    window: int | None = None,
    freq: str | None = None,
) -> pd.DataFrame | pd.Series:
    """Variacao acumulada via produto composto em janela movel.

    Formula: ``(prod(1 + x/100) - 1) * 100`` sobre a janela.

    A janela e resolvida automaticamente pela frequencia dos dados
    (ex: 12 para mensal, 252 para diario). Use ``window=`` ou ``freq=``
    para override.

    Args:
        df: Dados de entrada (taxas em percentual).
        window: Tamanho da janela em numero de periodos.
            Mutuamente exclusivo com ``freq``.
        freq: Frequencia dos dados (``'D'``, ``'B'``, ``'W'``, ``'M'``, ``'Q'``, ``'Y'``).
            Mutuamente exclusivo com ``window``.
    """
    params = validate_params(_RollingParams, window=window, freq=freq)
    data = validate_numeric(coerce_input(df))
    resolved = resolve_periods(data, "accum", params.window, params.freq)

    factor = 1 + data / 100

    def _nanprod(x: np.ndarray) -> float:
        return float(np.nanprod(x))

    result = factor.rolling(resolved, min_periods=resolved).apply(  # type: ignore[union-attr]
        _nanprod, raw=True
    )
    result = (result - 1) * 100
    return sanitize_result(result)


# ---------------------------------------------------------------------------
# diff -- diferenca absoluta
# ---------------------------------------------------------------------------


@overload
def diff(df: pd.DataFrame, periods: int = 1) -> pd.DataFrame: ...
@overload
def diff(df: pd.Series, periods: int = 1) -> pd.Series: ...
def diff(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    periods: int = 1,
) -> pd.DataFrame | pd.Series:
    """Diferenca absoluta entre periodos.

    Args:
        df: Dados de entrada.
        periods: Numero de periodos para o diff.
    """
    data = validate_numeric(coerce_input(df))
    return data.diff(periods=periods)


# ---------------------------------------------------------------------------
# normalize -- rebase para valor base
# ---------------------------------------------------------------------------


@overload
def normalize(
    df: pd.DataFrame,
    base: int | None = None,
    base_date: str | None = None,
) -> pd.DataFrame: ...
@overload
def normalize(
    df: pd.Series,
    base: int | None = None,
    base_date: str | None = None,
) -> pd.Series: ...
def normalize(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    base: int | None = None,
    base_date: str | None = None,
) -> pd.DataFrame | pd.Series:
    """Normaliza serie para um valor base.

    Usa o primeiro valor nao-NaN como referencia. Se ``base_date`` for
    fornecido, usa o valor naquela data.

    Args:
        df: Dados de entrada.
        base: Valor base para normalizacao (default: config ``normalize_base``).
        base_date: Data de referencia (string parseable por ``pd.Timestamp``).
            Se a data exata nao existir no index, usa a mais proxima.
    """
    params = validate_params(_NormalizeParams, base=base, base_date=base_date)
    data = validate_numeric(coerce_input(df))

    effective_base = (
        params.base
        if params.base is not None
        else get_config().transforms.normalize_base
    )

    if params.base_date is not None:
        ts = pd.Timestamp(params.base_date)
        if ts in data.index:
            base_value = data.loc[ts]
        else:
            idx = data.index.get_indexer([ts], method="nearest")
            if idx[0] == -1:
                raise TransformError(
                    f"base_date '{params.base_date}' could not be matched "
                    f"to any date in the index"
                )
            base_value = data.iloc[idx[0]]
    else:
        # Primeiro valor nao-NaN
        if isinstance(data, pd.DataFrame):
            base_value = data.apply(
                lambda s: s.dropna().iloc[0] if not s.dropna().empty else np.nan
            )
        else:
            clean = data.dropna()
            if clean.empty:
                raise TransformError("Cannot normalize: all values are NaN")
            base_value = clean.iloc[0]

    # Validar base_value
    if isinstance(base_value, (int, float, np.integer, np.floating)):
        if np.isnan(base_value) or base_value == 0:
            raise TransformError(
                f"Base value for normalization is {'NaN' if np.isnan(base_value) else 'zero'}. "
                f"Cannot divide by {'NaN' if np.isnan(base_value) else 'zero'}."
            )
    elif isinstance(base_value, pd.Series):
        # DataFrame: base_value e uma Series (uma entrada por coluna)
        zero_cols = base_value[base_value == 0].index.tolist()
        nan_cols = base_value[base_value.isna()].index.tolist()
        problem_cols = zero_cols + nan_cols
        if problem_cols:
            raise TransformError(
                f"Base value is zero or NaN for columns: {problem_cols}. "
                f"Cannot normalize these columns."
            )

    result = (data / base_value) * effective_base
    return sanitize_result(result)


# ---------------------------------------------------------------------------
# annualize -- anualizacao de taxa periodica
# ---------------------------------------------------------------------------


@overload
def annualize(
    df: pd.DataFrame, periods: int | None = None, freq: str | None = None
) -> pd.DataFrame: ...
@overload
def annualize(
    df: pd.Series, periods: int | None = None, freq: str | None = None
) -> pd.Series: ...
def annualize(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    periods: int | None = None,
    freq: str | None = None,
) -> pd.DataFrame | pd.Series:
    """Anualiza taxa periodica via juros compostos.

    Formula: ``((1 + r/100) ^ periods_per_year - 1) * 100``

    O numero de periodos por ano e resolvido automaticamente pela
    frequencia dos dados (ex: 252 para diario, 12 para mensal).
    Use ``periods=`` ou ``freq=`` para override.

    Args:
        df: Dados de entrada (taxas em percentual).
        periods: Numero de periodos por ano para composicao.
            Mutuamente exclusivo com ``freq``.
        freq: Frequencia dos dados (``'D'``, ``'B'``, ``'W'``, ``'M'``, ``'Q'``, ``'Y'``).
            Mutuamente exclusivo com ``periods``.
    """
    params = validate_params(_PctChangeParams, periods=periods, freq=freq)
    data = validate_numeric(coerce_input(df))
    resolved = resolve_periods(data, "annualize", params.periods, params.freq)
    rate_decimal = data / 100
    annualized = (1 + rate_decimal) ** resolved - 1
    return sanitize_result(annualized * 100)


# ---------------------------------------------------------------------------
# compound_rolling -- retorno composto em janela movel
# ---------------------------------------------------------------------------


@overload
def compound_rolling(
    df: pd.DataFrame, window: int | None = None, freq: str | None = None
) -> pd.DataFrame: ...
@overload
def compound_rolling(
    df: pd.Series, window: int | None = None, freq: str | None = None
) -> pd.Series: ...
def compound_rolling(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    window: int | None = None,
    freq: str | None = None,
) -> pd.DataFrame | pd.Series:
    """Retorno composto em janela movel.

    Multiplica fatores ``(1 + taxa/100)`` ao longo da janela.

    A janela e resolvida automaticamente pela frequencia dos dados.
    Use ``window=`` ou ``freq=`` para override.

    Args:
        df: Dados de entrada (taxas em percentual).
        window: Tamanho da janela em numero de periodos.
            Mutuamente exclusivo com ``freq``.
        freq: Frequencia dos dados (``'D'``, ``'B'``, ``'W'``, ``'M'``, ``'Q'``, ``'Y'``).
            Mutuamente exclusivo com ``window``.
    """
    params = validate_params(_RollingParams, window=window, freq=freq)
    data = validate_numeric(coerce_input(df))

    # Se nenhum dos dois foi passado, tenta config default primeiro, depois auto-detect
    if params.window is not None:
        resolved = params.window
    elif params.freq is not None:
        resolved = resolve_periods(data, "rolling", None, params.freq)
    else:
        config_window = get_config().transforms.rolling_window
        resolved = config_window

    factor = 1 + (data / 100)

    def _nanprod(x: np.ndarray) -> float:
        return float(np.nanprod(x))

    compounded = factor.rolling(resolved, min_periods=resolved).apply(  # type: ignore[union-attr]
        _nanprod, raw=True
    )
    result = (compounded - 1) * 100
    return sanitize_result(result)


# ---------------------------------------------------------------------------
# drawdown -- distancia percentual do pico historico
# ---------------------------------------------------------------------------


@overload
def drawdown(df: pd.DataFrame) -> pd.DataFrame: ...
@overload
def drawdown(df: pd.Series) -> pd.Series: ...
def drawdown(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
) -> pd.DataFrame | pd.Series:
    """Distancia percentual do pico historico (drawdown).

    Formula: ``(data / cummax - 1) * 100``. Retorna valores <= 0,
    onde 0 indica que o valor esta no pico e valores negativos indicam
    a magnitude da queda em relacao ao maximo acumulado.

    Args:
        df: Dados de entrada.
    """
    data = validate_numeric(coerce_input(df))
    cummax = data.cummax()

    # Drawdown requer valores positivos (precos, indices).
    # cummax <= 0 causa divisao por zero ou resultados invertidos.
    has_non_positive = (
        (cummax <= 0).any().any()
        if isinstance(cummax, pd.DataFrame)
        else (cummax <= 0).any()
    )
    if has_non_positive:
        raise TransformError(
            "drawdown requires strictly positive values. "
            "Data contains zero or negative cumulative maximum."
        )

    result = (data / cummax - 1) * 100
    return sanitize_result(result)


# ---------------------------------------------------------------------------
# zscore -- padronizacao estatistica
# ---------------------------------------------------------------------------


@overload
def zscore(df: pd.DataFrame, window: int | None = None) -> pd.DataFrame: ...
@overload
def zscore(df: pd.Series, window: int | None = None) -> pd.Series: ...
def zscore(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    window: int | None = None,
) -> pd.DataFrame | pd.Series:
    """Padronizacao estatistica (z-score).

    Transforma a serie em unidades de desvio padrao em relacao a media,
    eliminando escala e nivel. Permite comparar series com unidades
    completamente diferentes no mesmo grafico.

    Formula global: ``(data - mean) / std``
    Formula rolling: ``(data - rolling_mean) / rolling_std``

    Args:
        df: Dados de entrada.
        window: Janela rolling opcional. Se fornecido, calcula z-score
            rolling (media e desvio padrao moveis). Se ``None``, calcula
            z-score sobre toda a serie (global).
    """
    data = validate_numeric(coerce_input(df))

    if window is not None:
        rolling = data.rolling(window=window, min_periods=window)
        mean = rolling.mean()
        std = rolling.std()
    else:
        mean = data.mean()
        std = data.std()

    result = (data - mean) / std
    return sanitize_result(result)


# ---------------------------------------------------------------------------
# to_month_end -- normaliza index para fim de mes
# ---------------------------------------------------------------------------


@overload
def to_month_end(df: pd.DataFrame) -> pd.DataFrame: ...
@overload
def to_month_end(df: pd.Series) -> pd.Series: ...
def to_month_end(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
) -> pd.DataFrame | pd.Series:
    """Normaliza indice temporal para fim do mes.

    Cada timestamp e mapeado para o ultimo dia do respectivo mes.
    Dados sub-mensais (ex: diarios) resultarao em indices duplicados.

    Args:
        df: Dados de entrada. Index deve ser DatetimeIndex.

    Raises:
        TypeError: Se o index nao for DatetimeIndex.
    """
    data = coerce_input(df)

    if not isinstance(data.index, pd.DatetimeIndex):
        raise TypeError(
            f"to_month_end requires DatetimeIndex, got {type(data.index).__name__}"
        )

    result = data.copy()
    result.index = result.index.to_period("M").to_timestamp("M")  # type: ignore[attr-defined]
    return result
