# Referencia da API

Referencia tecnica completa do chartkit.

---

## Pandas Accessor

### df.chartkit.plot()

```python
def plot(
    x: str | None = None,
    y: str | list[str] | None = None,
    kind: str = "line",
    title: str | None = None,
    units: str | None = None,
    source: str | None = None,
    highlight_last: bool = False,
    y_origin: str = "zero",
    save_path: str | None = None,
    metrics: list[str] | None = None,
    **kwargs,
) -> PlotResult
```

#### Parametros

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `x` | `str \| None` | `None` | Coluna para eixo X. Se `None`, usa o index |
| `y` | `str \| list[str] \| None` | `None` | Coluna(s) para eixo Y. Se `None`, usa colunas numericas |
| `kind` | `str` | `"line"` | Tipo: `"line"` ou `"bar"` |
| `title` | `str \| None` | `None` | Titulo do grafico |
| `units` | `str \| None` | `None` | Formatacao do eixo Y (ver tabela abaixo) |
| `source` | `str \| None` | `None` | Fonte dos dados para rodape |
| `highlight_last` | `bool` | `False` | Destaca ultimo valor |
| `y_origin` | `str` | `"zero"` | Origem Y para barras: `"zero"` ou `"auto"` |
| `save_path` | `str \| None` | `None` | Caminho para salvar |
| `metrics` | `list[str] \| None` | `None` | Lista de metricas a aplicar |
| `**kwargs` | - | - | Argumentos extras para matplotlib |

#### Metricas Disponiveis

| Sintaxe | Descricao | Exemplo |
|---------|-----------|---------|
| `"ath"` | All-Time High (linha no maximo historico) | `metrics=["ath"]` |
| `"atl"` | All-Time Low (linha no minimo historico) | `metrics=["atl"]` |
| `"ma:N"` | Media movel de N periodos | `metrics=["ma:12"]` |
| `"hline:V"` | Linha horizontal no valor V | `metrics=["hline:3.0"]` |
| `"band:L:U"` | Banda sombreada entre L e U | `metrics=["band:1.5:4.5"]` |

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
| `yoy()` | `yoy(periods: int = 12) -> TransformAccessor` | Variacao percentual anual (Year-over-Year) |
| `mom()` | `mom(periods: int = 1) -> TransformAccessor` | Variacao percentual mensal (Month-over-Month) |
| `accum_12m()` | `accum_12m() -> TransformAccessor` | Variacao acumulada em 12 meses |
| `diff()` | `diff(periods: int = 1) -> TransformAccessor` | Diferenca absoluta entre periodos |
| `normalize()` | `normalize(base: int = 100, base_date: str \| None = None) -> TransformAccessor` | Normaliza serie para valor base |
| `annualize_daily()` | `annualize_daily(trading_days: int = 252) -> TransformAccessor` | Anualiza taxa diaria |
| `compound_rolling()` | `compound_rolling(window: int = 12) -> TransformAccessor` | Retorno composto em janela movel |
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
    kind: str = "line",
    title: str | None = None,
    units: str | None = None,
    source: str | None = None,
    highlight_last: bool = False,
    y_origin: str = "zero",
    save_path: str | None = None,
    metrics: list[str] | None = None,
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

Retorna dataclass tipada com todas as configuracoes.

### reset_config()

```python
def reset_config() -> None
```

Reseta configuracoes para defaults.

### configure_logging()

```python
def configure_logging(level: str = "DEBUG", sink=None) -> None
```

Ativa logging da biblioteca (desabilitado por padrao).

---

## ChartingConfig

Estrutura principal de configuracao.

```python
@dataclass
class ChartingConfig:
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
    paths: PathsConfig
```

### Sub-configuracoes

#### BrandingConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `company_name` | `str` | `""` |
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
| `assets_path` | `str` | `""` |
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
| `footer` | `FooterConfig` | (ver abaixo) |
| `title` | `TitleConfig` | (ver abaixo) |
| `zorder` | `ZOrderConfig` | (ver abaixo) |

#### FooterConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `x` | `float` | `0.01` |
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
| `moving_avg_min_periods` | `int` | `1` |
| `legend` | `LegendConfig` | (ver abaixo) |

#### LegendConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `alpha` | `float` | `0.9` |
| `frameon` | `bool` | `True` |

#### BarsConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `width_default` | `float` | `0.8` |
| `width_monthly` | `int` | `20` |
| `width_annual` | `int` | `300` |
| `auto_margin` | `float` | `0.1` |
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
| `label_offset_x` | `int` | `5` |
| `label_offset_y` | `int` | `8` |

#### CollisionConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `margin_px` | `int` | `5` |
| `guide_threshold_px` | `int` | `30` |
| `extra_padding_px` | `int` | `15` |
| `px_to_points_ratio` | `float` | `0.75` |

#### TransformsConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `mom_periods` | `int` | `1` |
| `yoy_periods` | `int` | `12` |
| `trading_days_per_year` | `int` | `252` |
| `normalize_base` | `int` | `100` |
| `rolling_window` | `int` | `12` |

#### FormattersConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `currency` | `CurrencyConfig` | (ver abaixo) |
| `locale` | `LocaleConfig` | (ver abaixo) |
| `magnitude` | `MagnitudeConfig` | (ver abaixo) |

#### CurrencyConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `BRL` | `str` | `"R$ "` |
| `USD` | `str` | `"$ "` |

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
| `moving_average_format` | `str` | `"MM{window}"` |

#### PathsConfig

| Campo | Tipo | Default |
|-------|------|---------|
| `charts_subdir` | `str` | `"charts"` |
| `outputs_dir` | `str` | `""` |
| `assets_dir` | `str` | `""` |
| `project_root_markers` | `list[str]` | `[".git", "pyproject.toml", ...]` |

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

    # Classes principais
    ChartingAccessor,
    ChartingPlotter,
    PlotResult,
    TransformAccessor,
    MetricRegistry,
    theme,

    # Transforms (funcoes standalone)
    yoy,
    mom,
    accum_12m,
    diff,
    normalize,
    annualize_daily,
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
