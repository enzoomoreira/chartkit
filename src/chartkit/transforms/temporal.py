"""
Funcoes de transformacao para series temporais.

Uso:
    from chartkit import yoy, mom, accum_12m

    df_yoy = yoy(df)           # Variacao ano contra ano
    df_mom = mom(df)           # Variacao mes contra mes
    df_accum = accum_12m(df)   # Acumulado 12 meses
"""

import pandas as pd

from ..settings import get_config


def mom(df: pd.DataFrame | pd.Series, periods: int | None = None) -> pd.DataFrame | pd.Series:
    """
    Calcula variacao percentual mensal (Month-over-Month).

    Args:
        df: DataFrame ou Series com indice temporal
        periods: Numero de periodos para comparacao (default: config.transforms.mom_periods)

    Returns:
        DataFrame/Series com variacao percentual

    Example:
        >>> df_mom = mom(df)  # Variacao mensal em %
    """
    if periods is None:
        periods = get_config().transforms.mom_periods
    return df.pct_change(periods=periods) * 100


def yoy(df: pd.DataFrame | pd.Series, periods: int | None = None) -> pd.DataFrame | pd.Series:
    """
    Calcula variacao percentual anual (Year-over-Year).

    Assume dados mensais por default (12 periodos = 1 ano).

    Args:
        df: DataFrame ou Series com indice temporal
        periods: Numero de periodos para comparacao (default: config.transforms.yoy_periods)

    Returns:
        DataFrame/Series com variacao percentual

    Example:
        >>> df_yoy = yoy(df)          # YoY para dados mensais
        >>> df_yoy = yoy(df, periods=4)  # YoY para dados trimestrais
    """
    if periods is None:
        periods = get_config().transforms.yoy_periods
    return df.pct_change(periods=periods) * 100


def accum_12m(df: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """
    Calcula variacao acumulada em 12 meses.

    Util para indices de inflacao mensal (ex: IPCA mensal -> IPCA 12m).
    Formula: (Produto(1 + x/100) - 1) * 100

    Args:
        df: DataFrame ou Series com variacoes mensais em %

    Returns:
        DataFrame/Series com variacao acumulada 12 meses

    Example:
        >>> ipca_mensal = sidra.read('ipca')
        >>> ipca_12m = accum_12m(ipca_mensal)
    """
    def _calc_accum(x):
        return ((1 + x / 100).prod() - 1) * 100

    return df.rolling(12).apply(_calc_accum, raw=False)


def diff(df: pd.DataFrame | pd.Series, periods: int = 1) -> pd.DataFrame | pd.Series:
    """
    Calcula diferenca absoluta entre periodos.

    Args:
        df: DataFrame ou Series com indice temporal
        periods: Numero de periodos para diferenca (default: 1)

    Returns:
        DataFrame/Series com diferenca

    Example:
        >>> df_diff = diff(df)  # Diferenca para periodo anterior
    """
    return df.diff(periods=periods)


def normalize(
    df: pd.DataFrame | pd.Series,
    base: int | None = None,
    base_date: str | None = None
) -> pd.DataFrame | pd.Series:
    """
    Normaliza serie para um valor base em uma data especifica.

    Util para comparar series com escalas diferentes.

    Args:
        df: DataFrame ou Series com indice temporal
        base: Valor base para normalizacao (default: config.transforms.normalize_base)
        base_date: Data base para normalizacao. Se None, usa primeira data.

    Returns:
        DataFrame/Series normalizada

    Example:
        >>> df_norm = normalize(df)  # Base 100 na primeira data
        >>> df_norm = normalize(df, base_date='2020-01-01')  # Base 100 em 2020
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
    trading_days: int | None = None
) -> pd.DataFrame | pd.Series:
    """
    Anualiza taxa diaria para taxa anual usando juros compostos.

    Formula: ((1 + r_diaria) ^ dias_uteis - 1) * 100

    Args:
        df: DataFrame ou Series com taxas diarias em %
        trading_days: Dias uteis no ano (default: config.transforms.trading_days_per_year)

    Returns:
        DataFrame/Series com taxas anualizadas em %

    Example:
        >>> cdi_diario = sgs.read('cdi')  # Taxa diaria em %
        >>> cdi_anual = annualize_daily(cdi_diario)
    """
    if trading_days is None:
        trading_days = get_config().transforms.trading_days_per_year
    # Converte % para decimal, aplica formula, retorna em %
    rate_decimal = df / 100
    annualized = (1 + rate_decimal) ** trading_days - 1
    return annualized * 100


def compound_rolling(
    df: pd.DataFrame | pd.Series,
    window: int | None = None
) -> pd.DataFrame | pd.Series:
    """
    Calcula retorno composto em janela movel.

    Multiplica os fatores (1 + taxa) ao longo da janela.
    Util para calcular Selic acumulada 12 meses a partir de taxas mensais.

    Args:
        df: DataFrame ou Series com taxas em % (ex: Selic mensal)
        window: Tamanho da janela em periodos (default: config.transforms.rolling_window)

    Returns:
        DataFrame/Series com retorno composto em %

    Example:
        >>> selic_mensal = sgs.read('selic_acumm_mensal')
        >>> selic_12m = compound_rolling(selic_mensal)
    """
    if window is None:
        window = get_config().transforms.rolling_window
    # Converte % para fator, aplica produto rolling, retorna em %
    factor = 1 + (df / 100)

    def _rolling_prod(x):
        return x.prod()

    compounded = factor.rolling(window).apply(_rolling_prod, raw=True) - 1
    return compounded * 100


def to_month_end(df: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """
    Normaliza indice temporal para fim do mes.

    Util para alinhar series com frequencias diferentes antes de operacoes.

    Args:
        df: DataFrame ou Series com DatetimeIndex

    Returns:
        DataFrame/Series com indice normalizado para fim do mes

    Example:
        >>> selic = sgs.read('selic')
        >>> selic_me = to_month_end(selic)  # Indice no ultimo dia do mes
    """
    result = df.copy()
    result.index = result.index.to_period("M").to_timestamp("M")
    return result
