from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class MetricSpec:
    """Especificacao parseada de uma metrica.

    Sintaxe de string: ``nome:param1:param2@coluna``
    """

    name: str
    params: dict[str, Any] = field(default_factory=dict)
    series: str | None = None


class MetricRegistry:
    """Registro central de metricas com parse de string specs e aplicacao em batch."""

    _metrics: dict[str, tuple[Callable, list[str]]] = {}

    @classmethod
    def register(
        cls, name: str, param_names: list[str] | None = None
    ) -> Callable[[Callable], Callable]:
        """Decorator para registrar uma metrica.

        Args:
            name: Nome da metrica (usado na string spec).
            param_names: Nomes dos parametros posicionais extraidos da string.
                Ex: ``['window']`` faz ``'ma:12'`` virar ``{'window': 12}``.
        """

        def decorator(func: Callable) -> Callable:
            cls._metrics[name] = (func, param_names or [])
            return func

        return decorator

    @classmethod
    def parse(cls, spec: str | MetricSpec) -> MetricSpec:
        """Converte string spec em MetricSpec.

        Formatos: ``'ath'``, ``'ma:12'``, ``'band:1.5:4.5'``, ``'ath@revenue'``.
        ``rsplit('@', 1)`` preserva ``:`` no nome da coluna.

        Raises:
            ValueError: Metrica nao registrada ou series vazio apos ``@``.
        """
        if isinstance(spec, MetricSpec):
            return spec

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
        """Aplica lista de metricas ao grafico."""
        for spec in specs:
            parsed = cls.parse(spec)
            func, _ = cls._metrics[parsed.name]
            kwargs = parsed.params
            if parsed.series is not None:
                kwargs = {**kwargs, "series": parsed.series}
            func(ax, x_data, y_data, **kwargs)

    @classmethod
    def available(cls) -> list[str]:
        return sorted(cls._metrics.keys())

    @classmethod
    def clear(cls) -> None:
        """Remove todas as metricas registradas."""
        cls._metrics.clear()
