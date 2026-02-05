# Estendendo o chartkit

Guia para desenvolvedores que querem estender a funcionalidade do chartkit.

---

## MetricRegistry - Sistema de Metricas

O chartkit usa um sistema declarativo de metricas que permite adicionar
elementos visuais aos graficos via strings simples:

```python
df.chartkit.plot(metrics=['ath', 'atl', 'ma:12', 'hline:5.0'])
```

### Registrando Metricas Customizadas

Use o decorator `@MetricRegistry.register()` para criar novas metricas:

```python
from chartkit.metrics import MetricRegistry

@MetricRegistry.register('minha_metrica', param_names=['threshold'])
def minha_metrica(ax, x_data, y_data, threshold: float):
    """
    Adiciona linha horizontal customizada.

    Args:
        ax: Matplotlib Axes.
        x_data: Dados do eixo X.
        y_data: Dados do eixo Y (Series ou DataFrame).
        threshold: Valor onde a linha sera desenhada.
    """
    ax.axhline(threshold, color='purple', linestyle='--', linewidth=1.5)

# Uso:
df.chartkit.plot(metrics=['minha_metrica:10.0'])
```

### Anatomia do Decorator

```python
@MetricRegistry.register(
    name='nome_da_metrica',      # Nome usado na string de especificacao
    param_names=['param1', 'param2']  # Nomes dos parametros posicionais
)
def funcao(ax, x_data, y_data, param1, param2, **kwargs):
    ...
```

**Parametros obrigatorios da funcao:**
- `ax`: Matplotlib Axes onde desenhar
- `x_data`: Dados do eixo X (indice do DataFrame)
- `y_data`: Dados do eixo Y (Series ou DataFrame)

**Parametros adicionais:**
- Definidos em `param_names`, serao extraidos da string de especificacao
- Formato da string: `'nome:valor1:valor2'`
- Valores sao automaticamente convertidos para numeros se possivel

### Exemplos de Metricas Complexas

**Metrica com multiplos parametros:**

```python
@MetricRegistry.register('range', param_names=['min_val', 'max_val', 'color'])
def range_metric(ax, x_data, y_data, min_val: float, max_val: float, color: str = 'gray'):
    """Adiciona banda entre dois valores."""
    ax.axhspan(min_val, max_val, alpha=0.2, color=color)

# Uso:
df.chartkit.plot(metrics=['range:1.5:4.5:blue'])
```

**Metrica que calcula valores dinamicamente:**

```python
@MetricRegistry.register('percentile', param_names=['p'])
def percentile_metric(ax, x_data, y_data, p: int):
    """Adiciona linha no percentil especificado."""
    import numpy as np

    if hasattr(y_data, 'values'):
        values = y_data.values.flatten()
    else:
        values = y_data.values

    percentile_value = np.nanpercentile(values, p)
    ax.axhline(percentile_value, color='orange', linestyle=':', label=f'P{p}')

# Uso:
df.chartkit.plot(metrics=['percentile:90', 'percentile:10'])
```

### API do MetricRegistry

```python
from chartkit.metrics import MetricRegistry, MetricSpec

# Listar metricas disponiveis
MetricRegistry.available()  # ['ath', 'atl', 'band', 'hline', 'ma', ...]

# Parse manual de especificacao
spec = MetricRegistry.parse('ma:12')
print(spec.name)    # 'ma'
print(spec.params)  # {'window': 12}

# Aplicar metricas manualmente
MetricRegistry.apply(ax, x_data, y_data, ['ath', 'ma:12'])

# Limpar registro (util para testes)
MetricRegistry.clear()
```

---

## Criando Transforms Customizados

Transforms sao funcoes que transformam DataFrames/Series e podem ser
encadeadas via o accessor.

### Funcao Standalone

Crie uma funcao que aceita DataFrame/Series e retorna o mesmo tipo:

```python
# Em src/chartkit/transforms/meu_transform.py

import pandas as pd

def meu_transform(
    df: pd.DataFrame | pd.Series,
    param1: int = 10
) -> pd.DataFrame | pd.Series:
    """
    Descricao do transform.

    Args:
        df: DataFrame ou Series com indice temporal.
        param1: Descricao do parametro.

    Returns:
        DataFrame/Series transformado.

    Example:
        >>> df_transformado = meu_transform(df)
    """
    # Sua logica aqui
    return df.rolling(param1).mean()
```

### Integrando ao TransformAccessor

Para permitir encadeamento via `.chartkit.meu_transform()`:

**1. Adicione o import em `transforms/__init__.py`:**

```python
from .temporal import (
    # ... existentes ...
)
from .meu_transform import meu_transform

__all__ = [
    # ... existentes ...
    "meu_transform",
]
```

**2. Adicione o metodo em `transforms/accessor.py`:**

```python
from .meu_transform import meu_transform

class TransformAccessor:
    # ... metodos existentes ...

    def meu_transform(self, param1: int = 10) -> TransformAccessor:
        """
        Descricao do transform.

        Args:
            param1: Descricao do parametro.

        Returns:
            Novo TransformAccessor com dados transformados.

        Example:
            >>> df.chartkit.meu_transform().plot()
        """
        return TransformAccessor(meu_transform(self._df, param1))
```

**3. Opcional - Exponha no ChartingAccessor (`accessor.py`):**

```python
def meu_transform(self, param1: int = 10) -> TransformAccessor:
    """..."""
    return TransformAccessor(self._obj).meu_transform(param1)
```

Agora voce pode usar:

```python
# Standalone
from chartkit import meu_transform
df_novo = meu_transform(df)

# Encadeado
df.chartkit.meu_transform().plot()
df.chartkit.meu_transform().yoy().plot()
```

---

## Criando Novos Tipos de Grafico

### 1. Crie o arquivo do chart

```python
# Em src/chartkit/charts/scatter.py

import pandas as pd
from ..settings import get_config
from ..styling import theme

def plot_scatter(
    ax,
    x_data,
    y_data: pd.DataFrame | pd.Series,
    size: int = 50,
    alpha: float = 0.7,
    **kwargs
) -> None:
    """
    Renderiza grafico de dispersao.

    Args:
        ax: Matplotlib Axes.
        x_data: Dados do eixo X.
        y_data: Dados do eixo Y.
        size: Tamanho dos pontos.
        alpha: Transparencia.
        **kwargs: Argumentos extras para ax.scatter().
    """
    config = get_config()

    if isinstance(y_data, pd.Series):
        y_data = y_data.to_frame()

    colors = theme.colors.cycle()

    for i, col in enumerate(y_data.columns):
        color = colors[i % len(colors)]
        ax.scatter(
            x_data,
            y_data[col],
            s=size,
            alpha=alpha,
            color=color,
            label=col,
            **kwargs
        )

    if len(y_data.columns) > 1:
        ax.legend()
```

### 2. Exporte em `charts/__init__.py`

```python
from .line import plot_line
from .bar import plot_bar
from .scatter import plot_scatter  # Novo

__all__ = ["plot_line", "plot_bar", "plot_scatter"]
```

### 3. Adicione ao switch em `engine.py`

```python
from .charts.scatter import plot_scatter

class ChartingPlotter:
    def plot(self, ..., kind: str = "line", ...):
        # ...
        if kind == "line":
            plot_line(ax, x_data, y_data, highlight_last, **kwargs)
        elif kind == "bar":
            plot_bar(ax, x_data, y_data, highlight=highlight_last, y_origin=y_origin, **kwargs)
        elif kind == "scatter":  # Novo
            plot_scatter(ax, x_data, y_data, **kwargs)
        else:
            raise ValueError(f"Chart type '{kind}' not supported.")
```

Uso:

```python
df.chartkit.plot(kind='scatter', size=100, alpha=0.5)
```

---

## Criando Novos Overlays

Overlays sao elementos visuais secundarios (medias moveis, linhas de referencia, etc.).

### 1. Crie o arquivo do overlay

```python
# Em src/chartkit/overlays/trend_line.py

import numpy as np
from ..settings import get_config

def add_trend_line(
    ax,
    x_data,
    y_data,
    color: str = None,
    linestyle: str = '--',
    **kwargs
) -> None:
    """
    Adiciona linha de tendencia linear.

    Args:
        ax: Matplotlib Axes.
        x_data: Dados do eixo X.
        y_data: Dados do eixo Y.
        color: Cor da linha.
        linestyle: Estilo da linha.
    """
    config = get_config()
    color = color or config.colors.secondary

    # Converte x para numerico se necessario
    x_numeric = np.arange(len(x_data))
    y_values = y_data.values.flatten() if hasattr(y_data, 'values') else y_data

    # Remove NaNs para fit
    mask = ~np.isnan(y_values)
    coeffs = np.polyfit(x_numeric[mask], y_values[mask], 1)
    trend = np.poly1d(coeffs)(x_numeric)

    ax.plot(
        x_data,
        trend,
        color=color,
        linestyle=linestyle,
        zorder=2,
        label='Tendencia',
        **kwargs
    )
```

### 2. Exporte em `overlays/__init__.py`

```python
from .trend_line import add_trend_line  # Novo

__all__ = [
    # ... existentes ...
    "add_trend_line",
]
```

### 3. Integre com a Collision Engine

Overlays que criam elementos visuais devem registra-los na collision engine
para que labels sejam reposicionados automaticamente. Use a categoria
apropriada:

```python
from .._internal.collision import register_fixed, register_moveable, register_passive

# Linhas de referencia: obstaculos que labels devem evitar
line = ax.axhline(y=value, ...)
register_fixed(ax, line)

# Labels de texto: podem ser reposicionados
text = ax.text(x, y, "Label", ...)
register_moveable(ax, text)

# Areas de fundo: existem visualmente mas nao sao obstaculos
patch = ax.axhspan(lower, upper, alpha=0.1, ...)
register_passive(ax, patch)
```

Se o overlay nao cria elementos que interagem com labels (ex: linhas de dados
como media movel), nenhum registro e necessario.

Para mais detalhes, veja o [guia da collision engine](../guide/collision.md).

### 4. Opcional - Crie uma metrica para o overlay

```python
# Em src/chartkit/metrics/builtin.py (ou novo arquivo)

from ..overlays import add_trend_line

@MetricRegistry.register("trend")
def metric_trend(ax, x_data, y_data, **kwargs) -> None:
    """
    Adiciona linha de tendencia.

    Uso: metrics=['trend']
    """
    add_trend_line(ax, x_data, y_data, **kwargs)
```

Agora voce pode usar:

```python
# Via API direta
from chartkit.overlays import add_trend_line
add_trend_line(ax, x_data, y_data)

# Via metrics
df.chartkit.plot(metrics=['ath', 'trend'])
```

---

## Hooks de Configuracao

### Adicionando Novas Secoes de Config

**1. Defina a dataclass em `settings/schema.py`:**

```python
@dataclass
class MeuConfig:
    """Configuracoes para minha feature."""
    enabled: bool
    threshold: float
    color: str
```

**2. Adicione a `ChartingConfig`:**

```python
@dataclass
class ChartingConfig:
    # ... existentes ...
    meu_config: MeuConfig
```

**3. Adicione defaults em `settings/defaults.py`:**

```python
DEFAULT_CONFIG = ChartingConfig(
    # ... existentes ...
    meu_config=MeuConfig(
        enabled=True,
        threshold=0.5,
        color="#FF0000",
    ),
)
```

**4. Use via `get_config()`:**

```python
from chartkit.settings import get_config

def minha_funcao():
    config = get_config()
    if config.meu_config.enabled:
        threshold = config.meu_config.threshold
        # ...
```

**5. Configure via TOML:**

```toml
# .charting.toml
[meu_config]
enabled = true
threshold = 0.75
color = "#00FF00"
```

### Adicionando Novos Formatadores

**1. Implemente em `styling/formatters.py`:**

```python
def my_formatter(prefix: str = ""):
    """
    Formatador customizado.

    Args:
        prefix: Prefixo para valores.

    Returns:
        FuncFormatter para uso com matplotlib.
    """
    config = get_config()
    locale = config.formatters.locale

    def _format(x, pos):
        formatted = f"{x:,.2f}"
        formatted = formatted.replace(",", locale.thousands)
        return f"{prefix}{formatted}"

    return FuncFormatter(_format)
```

**2. Adicione ao mapa em `engine.py`:**

```python
from .styling import my_formatter

_FORMATTERS = {
    # ... existentes ...
    'custom': my_formatter,
    'prefix_R': lambda: my_formatter('R '),
}
```

Uso:

```python
df.chartkit.plot(units='custom')
df.chartkit.plot(units='prefix_R')
```

---

## Boas Praticas

### Imports

- Use imports relativos dentro do package (`from ..settings import get_config`)
- Evite imports circulares (consulte o grafo de dependencias em architecture.md)

### Documentacao

- Docstrings em formato Google
- Type hints em todas as funcoes
- Exemplos de uso nos docstrings

### Testes

- Limpe caches entre testes:

```python
import pytest
from chartkit.settings import reset_config
from chartkit.settings.discovery import reset_project_root_cache
from chartkit.metrics import MetricRegistry

@pytest.fixture(autouse=True)
def clean_state():
    yield
    reset_config()
    reset_project_root_cache()
    MetricRegistry.clear()
```

### Defaults de Parametros

Quando um parametro pode vir da config, use `None` como default:

```python
def minha_funcao(alpha=None):
    config = get_config()
    alpha = alpha if alpha is not None else config.minha_secao.alpha
```
