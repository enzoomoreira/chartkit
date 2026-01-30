import pandas as pd
from .engine import ChartingPlotter


@pd.api.extensions.register_dataframe_accessor("chartkit")
class ChartingAccessor:
    """
    Pandas Accessor para funcionalidade de charting.
    Uso: df.chartkit.plot()

    Nota: O plotter e armazenado como atributo do DataFrame para persistir
    entre multiplos acessos ao accessor (pandas cria nova instancia a cada acesso).
    """

    # Nome do atributo usado para cachear o plotter no DataFrame
    _PLOTTER_ATTR = "_chartkit_plotter"

    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    @property
    def plotter(self) -> ChartingPlotter:
        """Retorna plotter cacheado ou cria um novo."""
        # Cacheia o plotter no DataFrame para persistir entre acessos ao accessor
        if not hasattr(self._obj, self._PLOTTER_ATTR):
            object.__setattr__(self._obj, self._PLOTTER_ATTR, ChartingPlotter(self._obj))
        return getattr(self._obj, self._PLOTTER_ATTR)

    def plot(
        self,
        x: str = None,
        y: str | list[str] = None,
        kind: str = "line",
        title: str = None,
        units: str = None,
        source: str = None,
        highlight_last: bool = False,
        y_origin: str = "zero",
        save_path: str = None,
        moving_avg: int = None,
        show_ath: bool = False,
        show_atl: bool = False,
        overlays: dict = None,
        **kwargs,
    ):
        """
        Cria um grafico padronizado.

        Args:
            x: Coluna para eixo X. Se None, usa o index do DataFrame.
            y: Coluna(s) para eixo Y. Se None, usa todas as colunas numericas.
            kind: Tipo de grafico ('line' ou 'bar').
            title: Titulo do grafico (opcional).
            units: Formatacao do eixo Y (ex: '%', 'BRL', 'USD', 'human').
            source: Fonte dos dados para exibir no rodape.
            highlight_last: Se True, destaca o ultimo valor da serie.
            y_origin: Origem do eixo Y para barras ('zero' ou 'auto').
            save_path: Se fornecido, salva o grafico neste caminho.
            moving_avg: Janela da media movel (ex: 12 para MM12).
            show_ath: Se True, mostra linha no All-Time High.
            show_atl: Se True, mostra linha no All-Time Low.
            overlays: Dicionario com overlays customizados:
                - 'hlines': Lista de dicts com {value, label, color, linestyle}
                - 'band': Dict com {lower, upper, color, alpha, label}
            **kwargs: Argumentos extras passados para matplotlib.

        Returns:
            matplotlib.axes.Axes: Objeto Axes do grafico gerado.
        """
        return self.plotter.plot(
            x=x,
            y=y,
            kind=kind,
            title=title,
            units=units,
            source=source,
            highlight_last=highlight_last,
            y_origin=y_origin,
            save_path=save_path,
            moving_avg=moving_avg,
            show_ath=show_ath,
            show_atl=show_atl,
            overlays=overlays,
            **kwargs
        )
        
    def save(self, path: str, dpi: int = None):
        """
        Salva o grafico atual (se existir).

        Args:
            path: Caminho do arquivo (ex: 'grafico.png')
            dpi: Resolucao em DPI (default: config.layout.dpi)

        Raises:
            RuntimeError: Se nenhum grafico foi gerado ainda
        """
        plotter = getattr(self._obj, self._PLOTTER_ATTR, None)
        if plotter and plotter._fig is not None:
            plotter.save(path, dpi=dpi)
        else:
            raise RuntimeError("Nenhum grafico gerado ainda. Chame .plot() primeiro.")
