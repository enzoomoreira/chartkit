# Referencia da API

Referencia tecnica completa do chartkit.

---

## Pandas Accessor

### df.chartkit.plot()

```python
def plot(
    x: str | None = None,
    y: str | list[str] | None = None,
    *,
    kind: ChartKind = "line",
    title: str | None = None,
    units: UnitFormat | None = None,
    source: str | None = None,
    highlight: HighlightInput = False,
    metrics: str | list[str] | None = None,
    fill_between: tuple[str, str] | None = None,
    legend: bool | None = None,
    **kwargs,
) -> PlotResult
```

#### Parametros

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `x` | `str \| None` | `None` | Coluna para eixo X. Se `None`, usa o index |
| `y` | `str \| list[str] \| None` | `None` | Coluna(s) para eixo Y. Se `None`, usa colunas numericas |
| `kind` | `ChartKind` | `"line"` | Tipo de grafico registrado no `ChartRegistry` (ex: `"line"`, `"bar"`, `"stacked_bar"`) |
| `title` | `str \| None` | `None` | Titulo do grafico |
| `units` | `UnitFormat \| None` | `None` | Formatacao do eixo Y (ver tabela abaixo) |
| `source` | `str \| None` | `None` | Fonte dos dados para rodape. Quando `None`, usa `branding.default_source` como fallback |
| `highlight` | `HighlightInput` | `False` | Modo(s) de destaque. `True` / `'last'` = ultimo valor; `'max'` / `'min'` = extremos. Aceita lista para combinar modos (ex: `['max', 'min']`) |
| `metrics` | `str \| list[str] \| None` | `None` | Metrica(s) a aplicar (string ou lista) |
| `fill_between` | `tuple[str, str] \| None` | `None` | Tupla `(col1, col2)` para sombrear area entre duas colunas |
| `legend` | `bool \| None` | `None` | Controle da legenda. `None` = auto (mostra com 2+ artists), `True` = forca, `False` = suprime |
| `**kwargs` | - | - | Parametros chart-specific (ex: `y_origin='auto'`) e extras matplotlib |

#### Metricas Disponiveis

| Sintaxe | Descricao | Exemplo |
|---------|-----------|---------|
| `"ath"` | All-Time High (linha no maximo historico) | `metrics=["ath"]` |
| `"atl"` | All-Time Low (linha no minimo historico) | `metrics=["atl"]` |
| `"ma:N"` | Media movel de N periodos | `metrics=["ma:12"]` |
| `"hline:V"` | Linha horizontal no valor V | `metrics=["hline:3.0"]` |
| `"band:L:U"` | Banda sombreada entre L e U | `metrics=["band:1.5:4.5"]` |
| `"target:V"` | Linha de meta no valor V | `metrics=["target:1000"]` |
| `"std_band:W:N"` | Banda de N desvios padrao com janela W | `metrics=["std_band:20:2"]` |
| `"avg"` | Linha horizontal na media dos dados | `metrics=["avg"]` |
| `"vband:D1:D2"` | Banda vertical entre datas D1 e D2 | `metrics=["vband:2020-03-01:2020-06-30"]` |

Metricas suportam label customizado via sintaxe `|`: `'ath|Maximo'`, `'ma:12@col|Media 12M'`, `'hline:100|Meta: Q1'`.

#### Tipos

```python
ChartKind = Literal["line", "bar", "stacked_bar"]
UnitFormat = Literal["BRL", "USD", "BRL_compact", "USD_compact", "%", "human", "points"]
HighlightMode = Literal["last", "max", "min"]
HighlightInput = bool | HighlightMode | list[HighlightMode]
```

---

## PlotResult

Resultado de plotagem com method chaining.

```python
@dataclass
class PlotResult:
    fig: Figure
    ax: Axes
    plotter: ChartingPlotter
```

### Metodos e Properties

| Membro | Tipo | Retorno | Descricao |
|--------|------|---------|-----------|
| `save(path, dpi=None)` | metodo | `PlotResult` | Salva grafico em arquivo |
| `show()` | metodo | `PlotResult` | Exibe grafico interativo |
| `axes` | property | `Axes` | Acesso ao matplotlib Axes |
| `figure` | property | `Figure` | Acesso ao matplotlib Figure |

### Assinaturas

```python
def save(self, path: str, dpi: int | None = None) -> PlotResult
def show(self) -> PlotResult

@property
def axes(self) -> Axes

@property
def figure(self) -> Figure
```

---

## TransformAccessor

Accessor encadeavel para transformacoes. Cada metodo retorna novo `TransformAccessor`.

### Metodos

| Metodo | Assinatura | Descricao |
|--------|------------|-----------|
| `yoy()` | `yoy(periods: int \| None = None, freq: str \| None = None) -> TransformAccessor` | Variacao percentual anual (auto-detect de frequencia) |
| `mom()` | `mom(periods: int \| None = None, freq: str \| None = None) -> TransformAccessor` | Variacao percentual mensal (auto-detect de frequencia) |
| `accum()` | `accum(window: int \| None = None, freq: str \| None = None) -> TransformAccessor` | Acumulado via produto composto em janela movel |
| `diff()` | `diff(periods: int = 1) -> TransformAccessor` | Diferenca absoluta entre periodos |
| `normalize()` | `normalize(base: int \| None = None, base_date: str \| None = None) -> TransformAccessor` | Normaliza serie (default: `config.transforms.normalize_base`) |
| `drawdown()` | `drawdown() -> TransformAccessor` | Distancia percentual do pico historico |
| `zscore()` | `zscore(window: int \| None = None) -> TransformAccessor` | Padronizacao estatistica (global ou rolling) |
| `annualize()` | `annualize(periods: int \| None = None, freq: str \| None = None) -> TransformAccessor` | Anualiza taxa periodica via juros compostos (auto-detect de frequencia) |
| `compound_rolling()` | `compound_rolling(window: int \| None = None, freq: str \| None = None) -> TransformAccessor` | Retorno composto (auto-detect de frequencia) |
| `to_month_end()` | `to_month_end() -> TransformAccessor` | Normaliza indice para fim do mes |
| `plot()` | `plot(**kwargs) -> PlotResult` | Finaliza cadeia e plota |
| `df` | `@property -> pd.DataFrame` | Acesso ao DataFrame transformado |

---

## Formatadores (units)

| Valor | Formato | Exemplo |
|-------|---------|---------|
| `"BRL"` | Real brasileiro | R$ 1.234,56 |
| `"USD"` | Dolar americano | $1,234.56 |
| `"BRL_compact"` | Real compacto | R$ 1,2 mi |
| `"USD_compact"` | Dolar compacto | $1.2M |
| `"%"` | Percentual | 10,5% |
| `"points"` | Inteiros BR | 1.234.567 |
| `"human"` | Notacao compacta | 1,2M |

Formatadores de moeda usam Babel. Locale configuravel via `formatters.locale.babel_locale`.

---

## ChartRegistry

Sistema plugavel de chart types via decorator.

### Registrar novo tipo

```python
from chartkit.charts.registry import ChartRegistry

@ChartRegistry.register("scatter")
def plot_scatter(ax, x, y_data, highlight=None, **kwargs):
    ...
```

### Metodos

| Metodo | Retorno | Descricao |
|--------|---------|-----------|
| `register(name)` | decorator | Registra funcao como chart type |
| `get(name)` | `ChartFunc` | Retorna funcao registrada |
| `available()` | `list[str]` | Lista nomes registrados |

---

## ChartingPlotter

Uso avancado para controle total.

### Construtor

```python
class ChartingPlotter:
    def __init__(self, df: pd.DataFrame) -> None
```

### Metodos

```python
def plot(
    x: str | None = None,
    y: str | list[str] | None = None,
    *,
    kind: ChartKind = "line",
    title: str | None = None,
    units: UnitFormat | None = None,
    source: str | None = None,
    highlight: HighlightInput = False,
    metrics: str | list[str] | None = None,
    fill_between: tuple[str, str] | None = None,
    legend: bool | None = None,
    **kwargs,
) -> PlotResult

def save(self, path: str, dpi: int | None = None) -> None
```

---

## Configuracao

### configure()

```python
def configure(
    config_path: Path | None = None,
    outputs_path: Path | None = None,
    assets_path: Path | None = None,
    **section_overrides,
) -> None
```

Overrides por secao:

```python
configure(branding={"company_name": "Empresa"})
configure(colors={"primary": "#FF0000"})
configure(layout={"figsize": [12.0, 8.0], "dpi": 150})
```

### get_config()

```python
def get_config() -> ChartingConfig
```

Retorna pydantic BaseSettings com todas as configuracoes.

### reset_config()

```python
def reset_config() -> None
```

Reseta configuracoes para defaults.

### configure_logging()

```python
def configure_logging(level: str = "DEBUG", sink: Any = None) -> None
```

Ativa logging da biblioteca (desabilitado por padrao).

---

## ChartingConfig

Estrutura principal de configuracao.

```python
class ChartingConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CHARTKIT_",
        env_nested_delimiter="__",
    )

    branding: BrandingConfig
    colors: ColorsConfig
    fonts: FontsConfig
    layout: LayoutConfig
    lines: LinesConfig
    bars: BarsConfig
    bands: BandsConfig
    markers: MarkersConfig
    collision: CollisionConfig
    transforms: TransformsConfig
    formatters: FormattersConfig
    labels: LabelsConfig
    legend: LegendConfig
    paths: PathsConfig
```

#### LegendConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `loc` | `str` | `"best"` |
| `alpha` | `float` | `0.9` |
| `frameon` | `bool` | `True` |

### Sub-configuracoes

#### BrandingConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `company_name` | `str` | `""` |
| `default_source` | `str` | `""` |
| `footer_format` | `str` | `"Fonte: {source}, {company_name}"` |
| `footer_format_no_source` | `str` | `"{company_name}"` |

#### ColorsConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `primary` | `str` | `"#00464D"` |
| `secondary` | `str` | `"#006B6B"` |
| `tertiary` | `str` | `"#008B8B"` |
| `quaternary` | `str` | `"#20B2AA"` |
| `quinary` | `str` | `"#5F9EA0"` |
| `senary` | `str` | `"#2E8B57"` |
| `text` | `str` | `"#00464D"` |
| `grid` | `str` | `"lightgray"` |
| `background` | `str` | `"white"` |
| `positive` | `str` | `"#00464D"` |
| `negative` | `str` | `"#8B0000"` |
| `moving_average` | `str` | `"#888888"` |

#### FontsConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `file` | `str` | `""` |
| `fallback` | `str` | `"sans-serif"` |
| `sizes` | `FontSizesConfig` | (ver abaixo) |

#### FontSizesConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `default` | `int` | `11` |
| `title` | `int` | `18` |
| `footer` | `int` | `9` |
| `axis_label` | `int` | `11` |

#### LayoutConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `figsize` | `tuple[float, float]` | `(10.0, 6.0)` |
| `dpi` | `int` | `300` |
| `base_style` | `str` | `"seaborn-v0_8-white"` |
| `grid` | `bool` | `False` |
| `spines` | `SpinesConfig` | (ver abaixo) |
| `footer` | `FooterConfig` | (ver abaixo) |
| `title` | `TitleConfig` | (ver abaixo) |
| `zorder` | `ZOrderConfig` | (ver abaixo) |

#### SpinesConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `top` | `bool` | `False` |
| `right` | `bool` | `False` |
| `left` | `bool` | `True` |
| `bottom` | `bool` | `True` |

#### FooterConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `y` | `float` | `0.01` |
| `color` | `str` | `"gray"` |

#### TitleConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `padding` | `int` | `20` |
| `weight` | `str` | `"bold"` |

#### ZOrderConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `bands` | `int` | `0` |
| `reference_lines` | `int` | `1` |
| `moving_average` | `int` | `2` |
| `data` | `int` | `3` |
| `markers` | `int` | `5` |

#### LinesConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `main_width` | `float` | `2.0` |
| `overlay_width` | `float` | `1.5` |
| `reference_style` | `str` | `"--"` |
| `target_style` | `str` | `"-."` |
| `moving_avg_min_periods` | `int` | `1` |

#### BarsConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `width_default` | `float` | `0.8` |
| `width_monthly` | `int` | `20` |
| `width_annual` | `int` | `300` |
| `auto_margin` | `float` | `0.1` |
| `warning_threshold` | `int` | `500` |
| `frequency_detection` | `FrequencyDetectionConfig` | (ver abaixo) |

#### FrequencyDetectionConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `monthly_threshold` | `int` | `25` |
| `annual_threshold` | `int` | `300` |

#### BandsConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `alpha` | `float` | `0.15` |

#### MarkersConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `scatter_size` | `int` | `30` |
| `font_weight` | `str` | `"bold"` |

#### CollisionConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `movement` | `str` | `"y"` |
| `obstacle_padding_px` | `float` | `8.0` |
| `label_padding_px` | `float` | `4.0` |
| `max_iterations` | `int` | `50` |
| `connector_threshold_px` | `float` | `30.0` |
| `connector_alpha` | `float` | `0.6` |
| `connector_style` | `str` | `"-"` |
| `connector_width` | `float` | `1.0` |

#### TransformsConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `normalize_base` | `int` | `100` |
| `rolling_window` | `int` | `12` |

#### FormattersConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `locale` | `LocaleConfig` | (ver abaixo) |
| `magnitude` | `MagnitudeConfig` | (ver abaixo) |

#### LocaleConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `decimal` | `str` | `","` |
| `thousands` | `str` | `"."` |
| `babel_locale` | `str` | `"pt_BR"` |

#### MagnitudeConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `suffixes` | `list[str]` | `["", "k", "M", "B", "T"]` |

#### LabelsConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `ath` | `str` | `"ATH"` |
| `atl` | `str` | `"ATL"` |
| `avg` | `str` | `"AVG"` |
| `moving_average_format` | `str` | `"MM{window}"` |
| `target_format` | `str` | `"Meta: {value}"` |
| `std_band_format` | `str` | `"BB({window}, {num_std})"` |

#### PathsConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `charts_subdir` | `str` | `"charts"` |
| `outputs_dir` | `str` | `""` |
| `assets_dir` | `str` | `""` |

---

## Exceptions

| Classe | Base | Descricao |
|--------|------|-----------|
| `ChartKitError` | `Exception` | Excecao base da biblioteca |
| `TransformError` | `ChartKitError` | Erro de validacao ou execucao em transforms |

`TransformError` e levantado quando:
- `drawdown()` recebe dados com valores nao-positivos
- Auto-deteccao de frequencia falha e nenhum `periods=`/`freq=` foi fornecido
- Parametros mutuamente exclusivos (`periods` e `freq`) sao passados simultaneamente

`ValueError` e levantado quando:
- `plot()` recebe modo invalido em `highlight` (ex: `"banana"` em vez de `"last"`, `"max"` ou `"min"`)
- `plot()` recebe valor invalido em `units` (ex: `"EUR"` em vez de `"BRL"`)
- `y_origin` recebe valor fora de `"zero"` / `"auto"` em graficos de barras
- `add_highlight()` recebe `style` nao registrado em `HIGHLIGHT_STYLES`

---

## Exports do Modulo

```python
from chartkit import (
    # Configuracao
    configure,
    configure_logging,
    get_config,
    reset_config,
    ChartingConfig,

    # Paths (lazy evaluation)
    CHARTS_PATH,
    OUTPUTS_PATH,
    ASSETS_PATH,

    # Collision API
    register_fixed,
    register_moveable,
    register_passive,

    # Types
    ChartKind,
    HighlightInput,
    HighlightMode,
    UnitFormat,

    # Classes principais
    ChartingAccessor,
    ChartingPlotter,
    ChartRegistry,
    PlotResult,
    TransformAccessor,
    MetricRegistry,
    theme,

    # Exceptions
    ChartKitError,
    TransformError,

    # Transforms (funcoes standalone)
    yoy,
    mom,
    accum,
    diff,
    normalize,
    drawdown,
    zscore,
    annualize,
    compound_rolling,
    to_month_end,
)
```

### Funcoes de Paths

```python
from chartkit.settings import (
    get_outputs_path,   # -> Path
    get_charts_path,    # -> Path
    get_assets_path,    # -> Path
)
```
