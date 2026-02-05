import pandas as pd

from ..settings import get_config


def mom(df: pd.DataFrame | pd.Series, periods: int | None = None) -> pd.DataFrame | pd.Series:
    """Variacao percentual mensal (Month-over-Month)."""
    if periods is None:
        periods = get_config().transforms.mom_periods
    return df.pct_change(periods=periods) * 100


def yoy(df: pd.DataFrame | pd.Series, periods: int | None = None) -> pd.DataFrame | pd.Series:
    """Variacao percentual anual (Year-over-Year).

    Assume dados mensais por default (12 periodos = 1 ano).
    Use ``periods=4`` para dados trimestrais.
    """
    if periods is None:
        periods = get_config().transforms.yoy_periods
    return df.pct_change(periods=periods) * 100


def accum_12m(df: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """Variacao acumulada em 12 meses via produto composto.

    Formula: ``(prod(1 + x/100) - 1) * 100``
    """
    def _calc_accum(x):
        return ((1 + x / 100).prod() - 1) * 100

    return df.rolling(12).apply(_calc_accum, raw=False)


def diff(df: pd.DataFrame | pd.Series, periods: int = 1) -> pd.DataFrame | pd.Series:
    """Diferenca absoluta entre periodos."""
    return df.diff(periods=periods)


def normalize(
    df: pd.DataFrame | pd.Series,
    base: int | None = None,
    base_date: str | None = None,
) -> pd.DataFrame | pd.Series:
    """Normaliza serie para um valor base.

    Args:
        base: Valor base (default: ``config.transforms.normalize_base``).
        base_date: Data de referencia. Se None, usa a primeira data da serie.
    """
    if base is None:
        base = get_config().transforms.normalize_base
    if base_date is not None:
        base_date = pd.Timestamp(base_date)
        base_value = df.loc[base_date]
    else:
        base_value = df.iloc[0]

    return (df / base_value) * base


def annualize_daily(
    df: pd.DataFrame | pd.Series,
    trading_days: int | None = None,
) -> pd.DataFrame | pd.Series:
    """Anualiza taxa diaria via juros compostos.

    Formula: ``((1 + r) ^ dias_uteis - 1) * 100``
    """
    if trading_days is None:
        trading_days = get_config().transforms.trading_days_per_year
    rate_decimal = df / 100
    annualized = (1 + rate_decimal) ** trading_days - 1
    return annualized * 100


def compound_rolling(
    df: pd.DataFrame | pd.Series,
    window: int | None = None,
) -> pd.DataFrame | pd.Series:
    """Retorno composto em janela movel.

    Multiplica fatores ``(1 + taxa/100)`` ao longo da janela.
    """
    if window is None:
        window = get_config().transforms.rolling_window
    factor = 1 + (df / 100)

    def _rolling_prod(x):
        return x.prod()

    compounded = factor.rolling(window).apply(_rolling_prod, raw=True) - 1
    return compounded * 100


def to_month_end(df: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """Normaliza indice temporal para fim do mes."""
    result = df.copy()
    result.index = result.index.to_period("M").to_timestamp("M")
    return result
