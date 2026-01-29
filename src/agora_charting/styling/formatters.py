"""
Formatadores de eixo para matplotlib.

Fornece formatadores para valores monetarios, percentuais e
notacao compacta (1k, 1M, etc.).
"""

from matplotlib.ticker import FuncFormatter

from ..settings import get_config


def currency_formatter(currency: str = "BRL"):
    """
    Formatador para valores monetarios.

    Usa prefixos e locale configurados em settings.

    Args:
        currency: Codigo da moeda ('BRL', 'USD')

    Returns:
        FuncFormatter para uso com matplotlib.

    Example:
        >>> ax.yaxis.set_major_formatter(currency_formatter('BRL'))
        # R$ 1.234,56
    """
    config = get_config()
    locale = config.formatters.locale
    prefixes = config.formatters.currency

    def _format(x, pos):
        # Obtem prefixo da moeda
        prefix = getattr(prefixes, currency, "")

        if currency == "BRL":
            # Formato brasileiro: R$ 1.234,56
            formatted = f"{x:,.2f}"
            formatted = formatted.replace(",", "X").replace(".", locale.decimal).replace("X", locale.thousands)
            return f"{prefix}{formatted}"
        elif currency == "USD":
            # Formato americano: $ 1,234.56
            return f"{prefix}{x:,.2f}"

        return f"{x:,.2f}"

    return FuncFormatter(_format)


def percent_formatter(decimals: int = 1):
    """
    Formatador para porcentagens com separador de milhar.

    Usa locale configurado em settings.

    Args:
        decimals: Numero de casas decimais (default: 1)

    Returns:
        FuncFormatter para uso com matplotlib.

    Example:
        >>> ax.yaxis.set_major_formatter(percent_formatter())
        # 10.234,5%
    """
    config = get_config()
    locale = config.formatters.locale

    def _format(x, pos):
        # Formata com separador de milhar e converte para locale configurado
        formatted = f"{x:,.{decimals}f}%"
        formatted = formatted.replace(",", "X").replace(".", locale.decimal).replace("X", locale.thousands)
        return formatted

    return FuncFormatter(_format)


def human_readable_formatter(decimals: int = 1):
    """
    Formatador para grandes numeros (1k, 1M, 1B, 1T).

    Usa sufixos configurados em settings.

    Args:
        decimals: Numero de casas decimais (default: 1)

    Returns:
        FuncFormatter para uso com matplotlib.

    Example:
        >>> ax.yaxis.set_major_formatter(human_readable_formatter())
        # 1,5M
    """
    config = get_config()
    suffixes = config.formatters.magnitude.suffixes
    locale = config.formatters.locale

    def _format(x, pos):
        if x == 0:
            return "0"

        magnitude = 0
        # Limita magnitude ao maximo disponivel para evitar IndexError
        while abs(x) >= 1000 and magnitude < len(suffixes) - 1:
            magnitude += 1
            x /= 1000.0

        suffix = suffixes[magnitude]
        # Remove decimais se for inteiro (ex: 10k e nao 10.0k)
        if x == int(x):
            return f"{int(x)}{suffix}"

        formatted = f"{x:.{decimals}f}{suffix}"
        return formatted.replace(".", locale.decimal)

    return FuncFormatter(_format)


def points_formatter(decimals: int = 0):
    """
    Formatador para valores numericos com separador de milhar.

    Usado para unidades como pontos de indice, saldo de empregos, etc.
    Usa locale configurado em settings.

    Args:
        decimals: Numero de casas decimais (default: 0)

    Returns:
        FuncFormatter para uso com matplotlib.

    Example:
        >>> ax.yaxis.set_major_formatter(points_formatter())
        # 1.234.567
    """
    config = get_config()
    locale = config.formatters.locale

    def _format(x, pos):
        if x == 0:
            return "0"

        # Verifica se o valor e inteiro ou tem decimais significativos
        if decimals == 0 or x == int(x):
            # Formata como inteiro com separador de milhar
            formatted = f"{int(x):,}"
            return formatted.replace(",", locale.thousands)
        else:
            # Formata com decimais
            formatted = f"{x:,.{decimals}f}"
            formatted = formatted.replace(",", "X").replace(".", locale.decimal).replace("X", locale.thousands)
            return formatted

    return FuncFormatter(_format)
