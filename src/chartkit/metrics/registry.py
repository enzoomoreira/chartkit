"""
Sistema de registro de metricas para graficos.

Permite registrar, parsear e aplicar metricas de forma extensivel.
Metricas sao especificadas como strings (ex: 'ath', 'ma:12', 'band:1.5:4.5')
e convertidas para chamadas de funcao.

Uso:
    # Registrar metrica customizada
    @MetricRegistry.register('my_metric', param_names=['threshold'])
    def my_metric(ax, x_data, y_data, threshold: float):
        ax.axhline(threshold, color='red')

    # Aplicar metricas
    MetricRegistry.apply(ax, x_data, y_data, ['ath', 'ma:12', 'my_metric:5.0'])
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
    """

    name: str
    params: dict[str, Any] = field(default_factory=dict)


class MetricRegistry:
    """
    Registro central de metricas.

    Permite registrar metricas com decorator, parsear strings de especificacao
    (ex: 'ma:12') e aplicar metricas a graficos.

    Example:
        >>> @MetricRegistry.register('custom', param_names=['value'])
        ... def custom_metric(ax, x_data, y_data, value: float):
        ...     ax.axhline(value)

        >>> MetricRegistry.apply(ax, x, y, ['ath', 'custom:10'])
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

        Args:
            spec: String de especificacao ou MetricSpec ja parseado.

        Returns:
            MetricSpec com nome e parametros.

        Raises:
            ValueError: Se a metrica nao estiver registrada.

        Example:
            >>> spec = MetricRegistry.parse('ma:12')
            >>> spec.name
            'ma'
            >>> spec.params
            {'window': 12}
        """
        if isinstance(spec, MetricSpec):
            return spec

        parts = spec.split(":")
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
                # Tenta converter para numero
                try:
                    parsed_value: Any = float(value)
                    # Converte para int se for numero inteiro
                    if parsed_value.is_integer():
                        parsed_value = int(parsed_value)
                    params[param_names[i]] = parsed_value
                except ValueError:
                    # Mantem como string se nao for numero
                    params[param_names[i]] = value

        return MetricSpec(name, params)

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
            >>> MetricRegistry.apply(ax, x, y, ['ath', 'atl', 'ma:12'])
        """
        for spec in specs:
            parsed = cls.parse(spec)
            func, _ = cls._metrics[parsed.name]
            func(ax, x_data, y_data, **parsed.params)

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
