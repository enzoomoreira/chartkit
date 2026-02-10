from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Callable

import pandas as pd
from loguru import logger
from matplotlib.axes import Axes


@dataclass
class MetricSpec:
    """Especificacao parseada de uma metrica.

    Sintaxe de string: ``nome:param1:param2@coluna|label``
    """

    name: str
    params: dict[str, Any] = field(default_factory=dict)
    series: str | None = None
    label: str | None = None


class MetricRegistry:
    """Registro central de metricas com parse de string specs e aplicacao em batch."""

    _metrics: dict[str, tuple[Callable, list[str], bool]] = {}

    @classmethod
    def register(
        cls,
        name: str,
        param_names: list[str] | None = None,
        uses_series: bool = True,
    ) -> Callable[[Callable], Callable]:
        """Decorator para registrar uma metrica.

        Args:
            name: Nome da metrica (usado na string spec).
            param_names: Nomes dos parametros posicionais extraidos da string.
                Ex: ``['window']`` faz ``'ma:12'`` virar ``{'window': 12}``.
            uses_series: Se a metrica usa o parametro ``series`` para
                selecionar coluna em DataFrames multi-serie.
        """

        def decorator(func: Callable) -> Callable:
            cls._metrics[name] = (func, param_names or [], uses_series)
            return func

        return decorator

    @classmethod
    def parse(cls, spec: str | MetricSpec) -> MetricSpec:
        """Converte string spec em MetricSpec.

        Formatos: ``'ath'``, ``'ma:12'``, ``'band:1.5:4.5'``, ``'ath@revenue'``,
        ``'ath|Maximo'``, ``'ma:12@revenue|Media 12M'``.
        ``|`` separa label customizado; ``@`` seleciona coluna; ``:`` separa params.

        Raises:
            ValueError: Metrica nao registrada ou series vazio apos ``@``.
        """
        if isinstance(spec, MetricSpec):
            return spec

        label: str | None = None
        if "|" in spec:
            spec, label = spec.split("|", 1)
            label = label.strip() or None

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

        _, param_names, _ = cls._metrics[name]
        params: dict[str, Any] = {}

        raw_params = parts[1:]
        extra = raw_params[len(param_names) :]
        if extra:
            logger.warning("Parametros extras ignorados em '{}': {}", spec, extra)

        for i, value in enumerate(raw_params):
            if i < len(param_names):
                try:
                    parsed_value: Any = float(value)
                    if parsed_value.is_integer():
                        parsed_value = int(parsed_value)
                    params[param_names[i]] = parsed_value
                except ValueError:
                    params[param_names[i]] = value

        return MetricSpec(name, params, series, label)

    @classmethod
    def apply(
        cls,
        ax: Axes,
        x_data: pd.Index | pd.Series,
        y_data: pd.Series | pd.DataFrame,
        specs: Sequence[str | MetricSpec],
    ) -> None:
        """Aplica lista de metricas ao grafico."""
        for spec in specs:
            parsed = cls.parse(spec)
            func, _, uses_series = cls._metrics[parsed.name]
            kwargs = parsed.params.copy()
            if parsed.series is not None and uses_series:
                kwargs["series"] = parsed.series
            if parsed.label is not None:
                kwargs["label"] = parsed.label
            func(ax, x_data, y_data, **kwargs)

    @classmethod
    def available(cls) -> list[str]:
        return sorted(cls._metrics.keys())

    @classmethod
    def clear(cls) -> None:
        """Remove todas as metricas registradas."""
        cls._metrics.clear()
