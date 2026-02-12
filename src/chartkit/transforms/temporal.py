"""Transformacoes puras de series temporais.

Todas as funcoes seguem o contrato:
- Aceitam DataFrame, Series, dict, list ou ndarray (coercao automatica).
- Validam que dados sao numericos (warning + filtragem para non-numeric).
- Protegem contra inf (substituem por NaN no resultado).
- Funcoes que dependem de frequencia (variation, accum, annualize)
  resolvem periods via auto-detect ou exigem freq=/periods= explicito.
"""

from __future__ import annotations

from typing import overload

import numpy as np
import pandas as pd
from loguru import logger

from ..exceptions import TransformError
from ..settings import get_config
from ._validation import (
    _DiffParams,
    _FreqResolvedParams,
    _NormalizeParams,
    _RollingParams,
    _ZScoreParams,
    _infer_freq,
    _normalize_freq_code,
    coerce_input,
    resolve_periods,
    sanitize_result,
    validate_numeric,
    validate_params,
)


# ---------------------------------------------------------------------------
# variation -- variacao percentual por horizonte
# ---------------------------------------------------------------------------

_VALID_HORIZONS = {"month", "year"}


@overload
def variation(
    df: pd.DataFrame,
    horizon: str = "month",
    periods: int | None = None,
    freq: str | None = None,
) -> pd.DataFrame: ...
@overload
def variation(
    df: pd.Series,
    horizon: str = "month",
    periods: int | None = None,
    freq: str | None = None,
) -> pd.Series: ...
def variation(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    horizon: str = "month",
    periods: int | None = None,
    freq: str | None = None,
) -> pd.DataFrame | pd.Series:
    """Variacao percentual entre periodos.

    Calcula a variacao percentual comparando cada ponto com um ponto anterior,
    determinado pelo ``horizon``. O numero de periodos de comparacao e resolvido
    automaticamente com base na frequencia dos dados.

    Args:
        df: Dados de entrada.
        horizon: Horizonte de comparacao (``'month'`` ou ``'year'``).
            Em dados mensais, ``'month'`` compara com o mes anterior (periods=1)
            e ``'year'`` compara com o mesmo mes do ano anterior (periods=12).
            Para dados trimestrais/anuais, ``'month'`` compara com o periodo
            anterior (period-over-period).
        periods: Override explicito do numero de periodos.
            Mutuamente exclusivo com ``freq``.
        freq: Frequencia dos dados (``'D'``, ``'B'``, ``'W'``, ``'M'``, ``'Q'``, ``'Y'``).
            Mutuamente exclusivo com ``periods``.
    """
    if horizon not in _VALID_HORIZONS:
        raise TransformError(
            f"Invalid horizon '{horizon}'. Use: {', '.join(sorted(_VALID_HORIZONS))}"
        )
    params = validate_params(_FreqResolvedParams, periods=periods, freq=freq)
    data = validate_numeric(coerce_input(df))
    resolved = resolve_periods(data, horizon, params.periods, params.freq)
    logger.debug("variation: horizon='{}', resolved_periods={}", horizon, resolved)

    # Alerta quando horizon='month' nao significa "mes calendario"
    if horizon == "month" and resolved == 1 and params.periods is None:
        detected = (
            _infer_freq(data)
            if params.freq is None
            else _normalize_freq_code(params.freq)
        )
        if detected in ("QE", "QS", "YE", "YS"):
            logger.warning(
                "horizon='month' with {} data resolves to periods=1 "
                "(period-over-period, not calendar month-over-month)",
                detected,
            )

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

    A janela e resolvida pela seguinte precedencia:

    1. ``window=`` explicito
    2. ``freq=`` explicito (resolve via mapeamento)
    3. Auto-detect via ``pd.infer_freq``
    4. Fallback para ``config.transforms.accum_window``

    Args:
        df: Dados de entrada (taxas em percentual).
        window: Tamanho da janela em numero de periodos.
            Mutuamente exclusivo com ``freq``.
        freq: Frequencia dos dados (``'D'``, ``'B'``, ``'W'``, ``'M'``, ``'Q'``, ``'Y'``).
            Mutuamente exclusivo com ``window``.
    """
    params = validate_params(_RollingParams, window=window, freq=freq)
    data = validate_numeric(coerce_input(df))

    try:
        resolved = resolve_periods(data, "accum", params.window, params.freq)
        logger.debug("accum: resolved_window={}", resolved)
    except TransformError:
        if params.window is not None or params.freq is not None:
            raise
        resolved = get_config().transforms.accum_window
        logger.info(
            "Could not auto-detect frequency for accum. Using config accum_window={}",
            resolved,
        )

    factor = 1 + data / 100

    def _prod(x: np.ndarray) -> float:
        return float(np.prod(x))

    result = factor.rolling(resolved, min_periods=resolved).apply(  # type: ignore[union-attr]
        _prod, raw=True
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
        periods: Numero de periodos para o diff. Negativo para forward diff.
    """
    params = validate_params(_DiffParams, periods=periods)
    data = validate_numeric(coerce_input(df))
    return sanitize_result(data.diff(periods=params.periods))


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
            Deve ser positivo.
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
        try:
            ts = pd.Timestamp(params.base_date)
        except (ValueError, TypeError) as exc:
            raise TransformError(
                f"Invalid base_date '{params.base_date}': {exc}"
            ) from exc
        if ts in data.index:
            base_value = data.loc[ts]
        else:
            idx = data.index.get_indexer([ts], method="nearest")
            if idx[0] == -1:
                raise TransformError(
                    f"base_date '{params.base_date}' could not be matched "
                    f"to any date in the index"
                )
            matched_date = data.index[idx[0]]
            logger.debug(
                "normalize: base_date '{}' matched to nearest '{}'", ts, matched_date
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
    else:
        raise TransformError(f"Unexpected base value type: {type(base_value).__name__}")

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
    params = validate_params(_FreqResolvedParams, periods=periods, freq=freq)
    data = validate_numeric(coerce_input(df))
    resolved = resolve_periods(data, "annualize", params.periods, params.freq)
    logger.debug("annualize: resolved_periods_per_year={}", resolved)
    rate_decimal = data / 100
    annualized = (1 + rate_decimal) ** resolved - 1
    return sanitize_result(annualized * 100)


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
    params = validate_params(_ZScoreParams, window=window)
    data = validate_numeric(coerce_input(df))

    if params.window is not None:
        rolling = data.rolling(window=params.window, min_periods=params.window)
        mean = rolling.mean()
        std = rolling.std()
    else:
        mean = data.mean()
        std = data.std()

    result = (data - mean) / std

    # Alerta quando std=0 (dados constantes) produz all-NaN
    if isinstance(data, pd.DataFrame):
        all_nan_cols = result.columns[result.isna().all()].tolist()
        if all_nan_cols:
            logger.warning(
                "zscore produced all-NaN for columns {} (constant data, std=0)",
                all_nan_cols,
            )
    elif result.isna().all():
        logger.warning("zscore produced all-NaN (constant data, std=0)")

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
        TransformError: Se os dados forem vazios ou o index nao for DatetimeIndex.
    """
    data = coerce_input(df)

    if data.empty:
        raise TransformError("Input data is empty")

    if not isinstance(data.index, pd.DatetimeIndex):
        raise TransformError(
            f"to_month_end requires DatetimeIndex, got {type(data.index).__name__}"
        )

    result = data.copy()
    result.index = result.index.to_period("M").to_timestamp("M")  # type: ignore[attr-defined]
    return result
