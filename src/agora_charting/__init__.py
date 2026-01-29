"""
Biblioteca de Charting padronizado estilo Agora Investimentos.

Fornece capacidades de plotagem padronizada via Pandas Accessor.

Configuracao (opcional - funciona automaticamente na maioria dos casos):
    # Auto-discovery: detecta project root via pyproject.toml, .git, etc
    # e usa convencoes de pasta (outputs/, data/outputs/)

    # Opcao 1: Path direto
    from agora_charting import configure
    configure(outputs_path=Path('./meus_outputs'))

    # Opcao 2: Variavel de ambiente
    # $env:AGORA_CHARTING_OUTPUTS_PATH = "C:/caminho/outputs"

    # Opcao 3: Sem configuracao (usa auto-discovery)
    from agora_charting import CHARTS_PATH
    print(CHARTS_PATH)  # -> /path/to/project/outputs/charts

Uso:
    import agora_charting  # Registra o accessor 'agora'

    # Plotagem
    df.agora.plot()
    df.agora.plot(kind='bar', title='Titulo', units='%')

    # Transformacoes
    from agora_charting import yoy, mom, accum_12m, annualize_daily
    df_yoy = yoy(df)
    cdi_anual = annualize_daily(cdi_diario)
"""

from .accessor import AgoraAccessor
from .engine import AgoraPlotter
from .styling.theme import theme
from .transforms import (
    yoy,
    mom,
    accum_12m,
    diff,
    normalize,
    annualize_daily,
    compound_rolling,
    real_rate,
    to_month_end,
)
from .config import CHARTS_PATH, OUTPUTS_PATH, configure, get_settings

__all__ = [
    # Configuracao
    'configure',
    'get_settings',
    'CHARTS_PATH',
    'OUTPUTS_PATH',
    # Classes principais
    'AgoraAccessor',
    'AgoraPlotter',
    'theme',
    # Transforms
    'yoy',
    'mom',
    'accum_12m',
    'diff',
    'normalize',
    'annualize_daily',
    'compound_rolling',
    'real_rate',
    'to_month_end',
]
