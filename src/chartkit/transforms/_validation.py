"""Validacao, coercao e resolucao de frequencia para transforms.

Modulo interno -- nao faz parte da API publica.
"""

from __future__ import annotations

from typing import Literal

__all__ = [
    "coerce_input",
    "resolve_periods",
    "sanitize_result",
    "validate_numeric",
    "validate_params",
    "_PctChangeParams",
    "_RollingParams",
    "_NormalizeParams",
    "_AnnualizeParams",
]

import numpy as np
import pandas as pd
from loguru import logger
from pydantic import BaseModel, PositiveInt, model_validator

from ..exceptions import TransformError

# ---------------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------------

FreqLiteral = Literal[
    "D",
    "B",
    "W",
    "M",
    "Q",
    "Y",
    "daily",
    "business",
    "weekly",
    "monthly",
    "quarterly",
    "yearly",
    "annual",
]

TransformName = Literal["mom", "yoy", "accum", "rolling"]

# ---------------------------------------------------------------------------
# Constantes de mapeamento freq -> periods
# ---------------------------------------------------------------------------

# Aliases amigaveis que o usuario pode passar no parametro freq=
FREQ_ALIASES: dict[str, str] = {
    "D": "D",
    "daily": "D",
    "B": "B",
    "business": "B",
    "W": "W",
    "weekly": "W",
    "M": "ME",
    "monthly": "ME",
    "Q": "QE",
    "quarterly": "QE",
    "Y": "YE",
    "yearly": "YE",
    "annual": "YE",
}

# Mapeamento de freq code normalizado -> periods por tipo de transform.
# Os codes aqui sao os retornados por pd.infer_freq() ou normalizados via FREQ_ALIASES.
FREQ_PERIODS_MAP: dict[str, dict[TransformName, int]] = {
    "D": {"mom": 30, "yoy": 365, "accum": 365, "rolling": 365},
    "B": {"mom": 21, "yoy": 252, "accum": 252, "rolling": 252},
    "W": {"mom": 4, "yoy": 52, "accum": 52, "rolling": 52},
    "ME": {"mom": 1, "yoy": 12, "accum": 12, "rolling": 12},
    "MS": {"mom": 1, "yoy": 12, "accum": 12, "rolling": 12},
    "QE": {"mom": 1, "yoy": 4, "accum": 4, "rolling": 4},
    "QS": {"mom": 1, "yoy": 4, "accum": 4, "rolling": 4},
    "YE": {"mom": 1, "yoy": 1, "accum": 1, "rolling": 1},
    "YS": {"mom": 1, "yoy": 1, "accum": 1, "rolling": 1},
}

# Prefixos de freq codes ancorados que pd.infer_freq() pode retornar.
# Ex: "W-SUN" -> "W", "QE-DEC" -> "QE", "YE-DEC" -> "YE"
_ANCHORED_PREFIXES = ("W-", "QE-", "QS-", "BQE-", "BQS-", "YE-", "YS-", "BYE-", "BYS-")


# ---------------------------------------------------------------------------
# Pydantic models para validacao de parametros
# ---------------------------------------------------------------------------


class _PctChangeParams(BaseModel):
    """Validacao para mom/yoy."""

    periods: PositiveInt | None = None
    freq: FreqLiteral | None = None

    @model_validator(mode="after")
    def _periods_xor_freq(self) -> _PctChangeParams:
        if self.periods is not None and self.freq is not None:
            raise ValueError("Cannot specify both 'periods' and 'freq'")
        return self


class _RollingParams(BaseModel):
    """Validacao para accum / compound_rolling."""

    window: PositiveInt | None = None
    freq: FreqLiteral | None = None

    @model_validator(mode="after")
    def _window_xor_freq(self) -> _RollingParams:
        if self.window is not None and self.freq is not None:
            raise ValueError("Cannot specify both 'window' and 'freq'")
        return self


class _NormalizeParams(BaseModel):
    """Validacao para normalize."""

    base: PositiveInt | None = None
    base_date: str | None = None


class _AnnualizeParams(BaseModel):
    """Validacao para annualize_daily."""

    trading_days: PositiveInt | None = None


# ---------------------------------------------------------------------------
# Validacao de parametros (wrapper pydantic -> TransformError)
# ---------------------------------------------------------------------------


def validate_params[T: BaseModel](model_class: type[T], **kwargs) -> T:
    """Valida parametros escalares via pydantic model.

    Captura ``ValidationError`` e re-raises como ``TransformError``
    com mensagem limpa.
    """
    from pydantic import ValidationError

    try:
        return model_class(**kwargs)
    except ValidationError as exc:
        errors = exc.errors()
        messages = [
            f"  {e['loc'][0]}: {e['msg']}" if e.get("loc") else f"  {e['msg']}"
            for e in errors
        ]
        raise TransformError(
            f"Invalid parameters for {model_class.__name__}:\n" + "\n".join(messages)
        ) from exc


# ---------------------------------------------------------------------------
# Coercao de input
# ---------------------------------------------------------------------------


def coerce_input(data: object) -> pd.DataFrame | pd.Series:
    """Converte inputs comuns para DataFrame ou Series.

    Aceita: DataFrame, Series, dict, list, np.ndarray.
    Raises ``TypeError`` para tipos nao suportados.
    """
    if isinstance(data, (pd.DataFrame, pd.Series)):
        return data

    if isinstance(data, dict):
        try:
            return pd.DataFrame(data)
        except ValueError:
            return pd.Series(data)

    if isinstance(data, (list, np.ndarray)):
        arr = np.asarray(data)
        if arr.ndim == 1:
            return pd.Series(arr)
        if arr.ndim == 2:
            return pd.DataFrame(arr)
        raise TransformError(f"Arrays with {arr.ndim} dimensions are not supported")

    raise TypeError(
        f"Expected DataFrame, Series, dict, list, or ndarray. Got {type(data).__name__}"
    )


# ---------------------------------------------------------------------------
# Validacao numerica
# ---------------------------------------------------------------------------


def validate_numeric(df: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """Valida e filtra dados para conter apenas colunas numericas.

    - DataFrame: filtra colunas non-numeric com warning, raises se nenhuma sobra.
    - Series: raises se non-numeric.
    - Emite warning se index nao e DatetimeIndex.
    """
    if df.empty:
        raise TransformError("Input data is empty")

    if isinstance(df, pd.Series):
        if not pd.api.types.is_numeric_dtype(df):
            raise TransformError(f"Series must be numeric, got dtype '{df.dtype}'")
        if not isinstance(df.index, pd.DatetimeIndex):
            logger.warning(
                "Series index is {} instead of DatetimeIndex. "
                "Frequency auto-detection will not work.",
                type(df.index).__name__,
            )
        return df

    # DataFrame
    non_numeric = df.select_dtypes(exclude="number").columns.tolist()
    if non_numeric:
        logger.warning(
            "Dropping non-numeric columns: {}",
            non_numeric,
        )
        df = df.select_dtypes(include="number")
        if df.empty:
            raise TransformError("No numeric columns remaining after filtering")

    if not isinstance(df.index, pd.DatetimeIndex):
        logger.warning(
            "DataFrame index is {} instead of DatetimeIndex. "
            "Frequency auto-detection will not work.",
            type(df.index).__name__,
        )

    return df


# ---------------------------------------------------------------------------
# Sanitizacao de resultado
# ---------------------------------------------------------------------------


def sanitize_result(
    result: pd.DataFrame | pd.Series,
) -> pd.DataFrame | pd.Series:
    """Substitui inf/-inf por NaN no resultado."""
    return result.replace([np.inf, -np.inf], np.nan)


# ---------------------------------------------------------------------------
# Resolucao de frequencia -> periods
# ---------------------------------------------------------------------------


def _normalize_freq_code(raw: str) -> str:
    """Normaliza freq code para chave do FREQ_PERIODS_MAP.

    Trata aliases amigaveis ('M' -> 'ME') e freq codes ancorados
    retornados por pd.infer_freq() ('W-SUN' -> 'W', 'QE-DEC' -> 'QE').
    """
    if raw in FREQ_ALIASES:
        return FREQ_ALIASES[raw]

    for prefix in _ANCHORED_PREFIXES:
        if raw.startswith(prefix):
            return prefix.rstrip("-")

    return raw


def _infer_freq(df: pd.DataFrame | pd.Series) -> str | None:
    """Tenta inferir frequencia do index via pandas.

    Retorna freq code normalizado ou None se nao conseguir.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        return None

    if len(df.index) < 3:
        return None

    try:
        raw = pd.infer_freq(df.index)
    except (TypeError, ValueError):
        return None

    if raw is None:
        return None

    return _normalize_freq_code(raw)


def resolve_periods(
    df: pd.DataFrame | pd.Series,
    transform: TransformName,
    periods: int | None,
    freq: str | None,
) -> int:
    """Resolve o numero de periods para um transform.

    Precedencia: ``periods`` (explicito) > ``freq`` (explicito) >
    auto-detect via ``pd.infer_freq`` > ``ValueError``.

    Args:
        df: Dados de input (usado para auto-detect).
        transform: Nome do transform ('mom', 'yoy', 'accum', 'rolling').
        periods: Periods explicito passado pelo usuario.
        freq: Frequencia explicita passada pelo usuario.

    Returns:
        Numero de periods resolvido.

    Raises:
        TransformError: Se frequencia nao pode ser resolvida.
    """
    # 1. periods explicito -> usa direto
    if periods is not None:
        return periods

    # 2. freq explicito -> lookup
    if freq is not None:
        normalized = _normalize_freq_code(freq)
        mapping = FREQ_PERIODS_MAP.get(normalized)
        if mapping is None:
            raise TransformError(
                f"Unknown frequency '{freq}'. "
                f"Supported: {', '.join(sorted(FREQ_ALIASES.keys()))}"
            )
        return mapping[transform]

    # 3. Auto-detect
    detected = _infer_freq(df)
    if detected is not None:
        mapping = FREQ_PERIODS_MAP.get(detected)
        if mapping is not None:
            logger.debug(
                "Auto-detected frequency '{}' for transform '{}'", detected, transform
            )
            return mapping[transform]

    # 4. Nada funcionou
    raise TransformError(
        f"Cannot determine frequency for '{transform}'. "
        f"Pass freq= (e.g. 'M', 'D', 'B') or periods= explicitly."
    )
