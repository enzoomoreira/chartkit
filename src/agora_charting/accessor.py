import pandas as pd
from .engine import AgoraPlotter

@pd.api.extensions.register_dataframe_accessor("agora")
class AgoraAccessor:
    """
    Pandas Accessor para funcionalidade de charting.
    Uso: df.agora.plot()

    Nota: O plotter e armazenado como atributo do DataFrame para persistir
    entre multiplos acessos ao accessor (pandas cria nova instancia a cada acesso).
    """
    # Nome do atributo usado para cachear o plotter no DataFrame
    _PLOTTER_ATTR = '_agora_plotter'

    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    @property
    def plotter(self) -> AgoraPlotter:
        """Retorna plotter cacheado ou cria um novo."""
        # Cacheia o plotter no DataFrame para persistir entre acessos ao accessor
        if not hasattr(self._obj, self._PLOTTER_ATTR):
            object.__setattr__(self._obj, self._PLOTTER_ATTR, AgoraPlotter(self._obj))
        return getattr(self._obj, self._PLOTTER_ATTR)

    def plot(
        self,
        kind: str = 'line',
        title: str = None,
        save_path: str = None,
        moving_avg: int = None,
        show_ath: bool = False,
        show_atl: bool = False,
        overlays: dict = None,
        **kwargs
    ):
        """
        Cria um grafico estilo Agora-Database.

        Args:
            kind: 'line' ou 'bar'
            title: Titulo do grafico (opcional)
            save_path: Se fornecido, salva o grafico neste caminho
            moving_avg: Janela da media movel (ex: 12 para MM12)
            show_ath: Se True, mostra linha no All-Time High
            show_atl: Se True, mostra linha no All-Time Low
            overlays: Dicionario com overlays customizados:
                - 'hlines': Lista de dicts com {value, label, color, linestyle}
                - 'band': Dict com {lower, upper, color, alpha, label}
            **kwargs: Argumentos extras passados para matplotlib
        """
        return self.plotter.plot(
            kind=kind,
            title=title,
            save_path=save_path,
            moving_avg=moving_avg,
            show_ath=show_ath,
            show_atl=show_atl,
            overlays=overlays,
            **kwargs
        )
        
    def save(self, path: str, dpi: int = 300):
        """
        Salva o grafico atual (se existir).

        Args:
            path: Caminho do arquivo (ex: 'grafico.png')
            dpi: Resolucao em DPI (default: 300)

        Raises:
            RuntimeError: Se nenhum grafico foi gerado ainda
        """
        plotter = getattr(self._obj, self._PLOTTER_ATTR, None)
        if plotter and plotter._fig is not None:
            plotter.save(path, dpi=dpi)
        else:
            raise RuntimeError("Nenhum grafico gerado ainda. Chame .plot() primeiro.")
