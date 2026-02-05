"""
Sistema de registro de metricas para graficos.

Permite registrar, parsear e aplicar metricas de forma extensivel.
Metricas sao especificadas como strings (ex: 'ath', 'ma:12', 'band:1.5:4.5')
e convertidas para chamadas de funcao.

Sintaxe '@' para selecionar coluna alvo:
    - 'ath@revenue': ATH da coluna 'revenue'
    - 'ma:12@costs': Media movel 12 periodos da coluna 'costs'

Uso:
    # Registrar metrica customizada
    @MetricRegistry.register('my_metric', param_names=['threshold'])
    def my_metric(ax, x_data, y_data, threshold: float):
        ax.axhline(threshold, color='red')

    # Aplicar metricas (str ou lista)
    MetricRegistry.apply(ax, x_data, y_data, ['ath@revenue', 'ma:12'])
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class MetricSpec:
    """
    Especificacao parseda de uma metrica.

    Attributes:
        name: Nome da metrica (ex: 'ath', 'ma').
        params: Parametros parseados (ex: {'window': 12}).
        series: Coluna alvo (ex: 'revenue'). None usa a primeira coluna.

    Sintaxe de string: 'nome:param1:param2@coluna'
        - 'ath@revenue': ATH da coluna 'revenue'
        - 'ma:12@costs': Media movel 12 periodos da coluna 'costs'
    """

    name: str
    params: dict[str, Any] = field(default_factory=dict)
    series: str | None = None


class MetricRegistry:
    """
    Registro central de metricas.

    Permite registrar metricas com decorator, parsear strings de especificacao
    (ex: 'ma:12', 'ath@revenue') e aplicar metricas a graficos.

    Example:
        >>> @MetricRegistry.register('custom', param_names=['value'])
        ... def custom_metric(ax, x_data, y_data, value: float):
        ...     ax.axhline(value)

        >>> MetricRegistry.apply(ax, x, y, ['ath@revenue', 'custom:10'])
    """

    # Mapeamento: nome -> (funcao, lista de nomes de parametros)
    _metrics: dict[str, tuple[Callable, list[str]]] = {}

    @classmethod
    def register(
        cls, name: str, param_names: list[str] | None = None
    ) -> Callable[[Callable], Callable]:
        """
        Decorator para registrar uma metrica.

        Args:
            name: Nome da metrica (usado na string de especificacao).
            param_names: Nomes dos parametros posicionais.
                         Ex: ['window'] para 'ma:12' -> {'window': 12}

        Returns:
            Decorator que registra a funcao.

        Example:
            >>> @MetricRegistry.register('ma', param_names=['window'])
            ... def metric_ma(ax, x_data, y_data, window: int):
            ...     # implementacao
        """

        def decorator(func: Callable) -> Callable:
            cls._metrics[name] = (func, param_names or [])
            return func

        return decorator

    @classmethod
    def parse(cls, spec: str | MetricSpec) -> MetricSpec:
        """
        Parse de string de especificacao de metrica.

        Formatos suportados:
        - 'ath' -> MetricSpec('ath', {})
        - 'ma:12' -> MetricSpec('ma', {'window': 12})
        - 'band:1.5:4.5' -> MetricSpec('band', {'lower': 1.5, 'upper': 4.5})
        - 'ath@revenue' -> MetricSpec('ath', {}, series='revenue')
        - 'ma:12@costs' -> MetricSpec('ma', {'window': 12}, series='costs')

        O separador '@' indica a coluna alvo. rsplit garante que ':' no
        nome da coluna e preservado (ex: 'ath@col:x' -> series='col:x').

        Args:
            spec: String de especificacao ou MetricSpec ja parseado.

        Returns:
            MetricSpec com nome, parametros e serie opcional.

        Raises:
            ValueError: Se a metrica nao estiver registrada ou series vazio.
        """
        if isinstance(spec, MetricSpec):
            return spec

        # Extrai @series (rsplit preserva ':' no nome da coluna)
        series: str | None = None
        if "@" in spec:
            metric_part, series = spec.rsplit("@", 1)
            if not series:
                raise ValueError(
                    f"Series vazio em '{spec}'. Use 'metrica@coluna' ou "
                    f"MetricSpec(name, series=coluna) para colunas com '@'."
                )
        else:
            metric_part = spec

        parts = metric_part.split(":")
        name = parts[0]

        if name not in cls._metrics:
            available = ", ".join(sorted(cls._metrics.keys()))
            raise ValueError(
                f"Metrica desconhecida: '{name}'. Disponiveis: {available}"
            )

        _, param_names = cls._metrics[name]
        params: dict[str, Any] = {}

        for i, value in enumerate(parts[1:]):
            if i < len(param_names):
                try:
                    parsed_value: Any = float(value)
                    if parsed_value.is_integer():
                        parsed_value = int(parsed_value)
                    params[param_names[i]] = parsed_value
                except ValueError:
                    params[param_names[i]] = value

        return MetricSpec(name, params, series)

    @classmethod
    def apply(
        cls,
        ax,
        x_data,
        y_data,
        specs: list[str | MetricSpec],
    ) -> None:
        """
        Aplica lista de metricas ao grafico.

        Args:
            ax: Matplotlib Axes.
            x_data: Dados do eixo X.
            y_data: Dados do eixo Y (Series ou DataFrame).
            specs: Lista de especificacoes de metricas.

        Example:
            >>> MetricRegistry.apply(ax, x, y, ['ath@revenue', 'ma:12'])
        """
        for spec in specs:
            parsed = cls.parse(spec)
            func, _ = cls._metrics[parsed.name]
            kwargs = parsed.params
            if parsed.series is not None:
                # TODO(errors): validar que series existe em y_data.columns
                kwargs = {**kwargs, "series": parsed.series}
            func(ax, x_data, y_data, **kwargs)

    @classmethod
    def available(cls) -> list[str]:
        """
        Lista metricas disponiveis.

        Returns:
            Lista de nomes de metricas registradas.
        """
        return sorted(cls._metrics.keys())

    @classmethod
    def clear(cls) -> None:
        """Remove todas as metricas registradas. Util para testes."""
        cls._metrics.clear()
