"""
Engine generica de resolucao de colisao.

Trabalha exclusivamente com bounding boxes (display pixels).
Agnostica a tipos de elemento - qualquer Artist com get_window_extent() funciona.
"""

from __future__ import annotations

from math import sqrt
from collections.abc import Sequence
from typing import Protocol, runtime_checkable
from weakref import WeakKeyDictionary

import matplotlib.dates as mdates
from loguru import logger
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.backend_bases import RendererBase
from matplotlib.transforms import Bbox

from ..settings import get_config
from ..settings.schema import ChartingConfig, CollisionConfig

# Estado de colisao por Axes, liberado automaticamente pelo GC.
_labels: WeakKeyDictionary[Axes, list[Artist]] = WeakKeyDictionary()
_obstacles: WeakKeyDictionary[Axes, list[Artist]] = WeakKeyDictionary()
_passive: WeakKeyDictionary[Axes, list[Artist]] = WeakKeyDictionary()


@runtime_checkable
class PositionableArtist(Protocol):
    """Artist que suporta reposicionamento via get/set_position."""

    def get_position(self) -> tuple[float, float]: ...
    def set_position(self, xy: tuple[float, float]) -> None: ...
    def get_window_extent(self, renderer: RendererBase | None = None) -> Bbox: ...


def register_moveable(ax: Axes, artist: Artist) -> None:
    """Registra Artist que pode ser reposicionado pela engine."""
    _labels.setdefault(ax, []).append(artist)


def register_fixed(ax: Axes, artist: Artist) -> None:
    """Registra Artist que deve ser evitado por moveables."""
    _obstacles.setdefault(ax, []).append(artist)


def register_passive(ax: Axes, artist: Artist) -> None:
    """Registra Artist que nao participa da resolucao de colisao.

    Patches auto-detectados (ax.patches) sao tratados como obstaculos
    por padrao. Use esta funcao para excluir elementos visuais de fundo
    (bandas, areas sombreadas, etc.) da deteccao automatica.
    """
    _passive.setdefault(ax, []).append(artist)


def resolve_collisions(ax: Axes) -> None:
    """Resolve todas as colisoes registradas no axes."""
    moveables = _labels.get(ax, [])
    if not moveables:
        return

    config = get_config()
    collision = config.collision

    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()  # type: ignore[attr-defined]

    # Filtra apenas artists posicionaveis
    positionable = [m for m in moveables if isinstance(m, PositionableArtist)]
    if not positionable:
        return

    # Salva posicoes originais (numerico) para connectors
    original_positions = [_pos_to_numeric(*m.get_position()) for m in positionable]

    # Obstaculos: registrados explicitamente + patches auto-detectados
    fixed = _collect_obstacles(ax, moveables)
    logger.debug(
        "Collision: {} moveable(s), {} obstacle(s)", len(positionable), len(fixed)
    )

    if fixed:
        _resolve_against_fixed(positionable, fixed, renderer, ax, collision)

    if len(positionable) > 1:
        _resolve_between_moveables(positionable, renderer, ax, collision)

    _add_connectors(ax, positionable, original_positions, renderer, collision, config)


def _resolve_against_fixed(
    moveables: Sequence[PositionableArtist],
    fixed: list[Artist],
    renderer: RendererBase,
    ax: Axes,
    collision: CollisionConfig,
) -> None:
    """Resolve colisoes entre moveables e elementos fixos."""
    axes_bbox = ax.get_window_extent(renderer)

    for moveable in moveables:
        # Loop interno para resolver colisoes em cascata
        for _ in range(5):
            mov_bbox = _get_padded_bbox(
                moveable, renderer, collision.obstacle_padding_px
            )
            if mov_bbox.width == 0 and mov_bbox.height == 0:
                break

            resolved = True
            stuck = False
            for obstacle in fixed:
                fix_bbox = _get_padded_bbox(
                    obstacle, renderer, collision.obstacle_padding_px
                )
                if not mov_bbox.overlaps(fix_bbox):
                    continue

                resolved = False
                delta = _best_displacement(
                    mov_bbox,
                    fix_bbox,
                    collision.movement,
                    collision.obstacle_padding_px,
                    axes_bbox,
                )
                if delta is None:
                    stuck = True
                    break

                dx_px, dy_px = delta
                _shift_label(moveable, dx_px, dy_px, ax)
                mov_bbox = _get_padded_bbox(
                    moveable, renderer, collision.obstacle_padding_px
                )

            if resolved or stuck:
                break


def _best_displacement(
    mov_bbox: Bbox,
    fix_bbox: Bbox,
    movement: str,
    padding_px: float,
    axes_bbox: Bbox,
) -> tuple[float, float] | None:
    """Calcula menor deslocamento para resolver colisao, respeitando eixo e limites."""
    options: list[tuple[float, float, float]] = []  # (dx, dy, abs_distance)

    if movement in ("y", "xy"):
        # UP: mover base do moveable acima do topo do fixed
        dy_up = fix_bbox.y1 + padding_px - mov_bbox.y0
        # DOWN: mover topo do moveable abaixo da base do fixed
        dy_down = fix_bbox.y0 - padding_px - mov_bbox.y1

        new_y0_up = mov_bbox.y0 + dy_up
        new_y1_up = mov_bbox.y1 + dy_up
        if new_y0_up >= axes_bbox.y0 and new_y1_up <= axes_bbox.y1:
            options.append((0, dy_up, abs(dy_up)))

        new_y0_down = mov_bbox.y0 + dy_down
        new_y1_down = mov_bbox.y1 + dy_down
        if new_y0_down >= axes_bbox.y0 and new_y1_down <= axes_bbox.y1:
            options.append((0, dy_down, abs(dy_down)))

    if movement in ("x", "xy"):
        # RIGHT
        dx_right = fix_bbox.x1 + padding_px - mov_bbox.x0
        new_x0_right = mov_bbox.x0 + dx_right
        new_x1_right = mov_bbox.x1 + dx_right
        if new_x0_right >= axes_bbox.x0 and new_x1_right <= axes_bbox.x1:
            options.append((dx_right, 0, abs(dx_right)))

        # LEFT
        dx_left = fix_bbox.x0 - padding_px - mov_bbox.x1
        new_x0_left = mov_bbox.x0 + dx_left
        new_x1_left = mov_bbox.x1 + dx_left
        if new_x0_left >= axes_bbox.x0 and new_x1_left <= axes_bbox.x1:
            options.append((dx_left, 0, abs(dx_left)))

    if not options:
        return None

    # Menor deslocamento absoluto
    options.sort(key=lambda o: o[2])
    return (options[0][0], options[0][1])


def _resolve_between_moveables(
    moveables: Sequence[PositionableArtist],
    renderer: RendererBase,
    ax: Axes,
    collision: CollisionConfig,
) -> None:
    """Resolve colisoes entre moveables via push-apart iterativo."""
    movement = collision.movement
    label_padding_px = collision.label_padding_px

    for _ in range(collision.max_iterations):
        moved = False
        for i in range(len(moveables)):
            for j in range(i + 1, len(moveables)):
                bbox_a = _get_padded_bbox(moveables[i], renderer, label_padding_px)
                bbox_b = _get_padded_bbox(moveables[j], renderer, label_padding_px)
                if not bbox_a.overlaps(bbox_b):
                    continue

                overlap_x = min(bbox_a.x1, bbox_b.x1) - max(bbox_a.x0, bbox_b.x0)
                overlap_y = min(bbox_a.y1, bbox_b.y1) - max(bbox_a.y0, bbox_b.y0)

                if movement == "y":
                    shift_axis = "y"
                    shift_amount = overlap_y / 2 + label_padding_px / 2
                elif movement == "x":
                    shift_axis = "x"
                    shift_amount = overlap_x / 2 + label_padding_px / 2
                else:  # "xy"
                    if overlap_x <= overlap_y:
                        shift_axis = "x"
                        shift_amount = overlap_x / 2 + label_padding_px / 2
                    else:
                        shift_axis = "y"
                        shift_amount = overlap_y / 2 + label_padding_px / 2

                if shift_axis == "y":
                    if bbox_a.y0 >= bbox_b.y0:
                        _shift_label(moveables[i], 0, +shift_amount, ax)
                        _shift_label(moveables[j], 0, -shift_amount, ax)
                    else:
                        _shift_label(moveables[i], 0, -shift_amount, ax)
                        _shift_label(moveables[j], 0, +shift_amount, ax)
                else:
                    if bbox_a.x0 >= bbox_b.x0:
                        _shift_label(moveables[i], +shift_amount, 0, ax)
                        _shift_label(moveables[j], -shift_amount, 0, ax)
                    else:
                        _shift_label(moveables[i], -shift_amount, 0, ax)
                        _shift_label(moveables[j], +shift_amount, 0, ax)

                moved = True

        if not moved:
            break


def _add_connectors(
    ax: Axes,
    moveables: Sequence[PositionableArtist],
    original_positions: list[tuple[float, float]],
    renderer: RendererBase,
    collision: CollisionConfig,
    config: ChartingConfig,
) -> None:
    """Adiciona linhas guia para moveables deslocados alem do threshold."""
    # Preserva limites do eixo para ax.plot() nao expandir
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    for label, (orig_x, orig_y) in zip(moveables, original_positions):
        curr_x, curr_y = _pos_to_numeric(*label.get_position())
        orig_px = ax.transData.transform((orig_x, orig_y))
        curr_px = ax.transData.transform((curr_x, curr_y))
        dist_px = sqrt((orig_px[0] - curr_px[0]) ** 2 + (orig_px[1] - curr_px[1]) ** 2)

        if dist_px > collision.connector_threshold_px:
            ax.plot(
                [orig_x, curr_x],
                [orig_y, curr_y],
                color=config.colors.grid,
                alpha=collision.connector_alpha,
                lw=collision.connector_width,
                linestyle=collision.connector_style,
                zorder=config.layout.zorder.reference_lines,
            )

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)


# -- Helpers internos --


def _collect_obstacles(ax: Axes, moveables: list[Artist]) -> list[Artist]:
    """Coleta obstaculos: registrados explicitamente + patches auto-detectados.

    Auto-detecta ax.patches (bars, boxes, areas preenchidas, etc.) como
    obstaculos. Qualquer Artist com bbox local e detectado automaticamente,
    sem necessidade de registro manual em cada tipo de chart.
    """
    moveable_ids = {id(m) for m in moveables}
    passive_ids = {id(p) for p in _passive.get(ax, [])}
    seen: set[int] = set()
    obstacles: list[Artist] = []

    # 1. Obstaculos registrados explicitamente (reference lines, etc.)
    for obs in _obstacles.get(ax, []):
        oid = id(obs)
        if oid not in seen:
            obstacles.append(obs)
            seen.add(oid)

    # 2. Auto-detect: patches (bars, box plots, etc.)
    #    Exclui moveables e passivos (bandas, areas de fundo, etc.)
    for patch in ax.patches:
        pid = id(patch)
        if pid not in moveable_ids and pid not in passive_ids and pid not in seen:
            obstacles.append(patch)
            seen.add(pid)

    return obstacles


def _get_padded_bbox(
    artist: Artist | PositionableArtist,
    renderer: RendererBase,
    padding_px: float,
) -> Bbox:
    """Bbox expandido com padding fixo. Seguro para elementos de 0px."""
    bbox = artist.get_window_extent(renderer)
    if bbox.width < 1 or bbox.height < 1:
        return Bbox.from_extents(
            bbox.x0 - padding_px,
            bbox.y0 - padding_px,
            bbox.x1 + padding_px,
            bbox.y1 + padding_px,
        )
    return bbox.expanded(
        1 + padding_px / bbox.width,
        1 + padding_px / bbox.height,
    )


def _pos_to_numeric(x: object, y: object) -> tuple[float, float]:
    """Converte posicao data-space para numerico (datas -> mdates float)."""
    if not isinstance(x, (int, float)):
        try:
            x = mdates.date2num(x)
        except (TypeError, ValueError, AttributeError):
            x = float(x)  # type: ignore[arg-type]
    return float(x), float(y)  # type: ignore[arg-type]


def _shift_label(
    label: PositionableArtist, dx_px: float, dy_px: float, ax: Axes
) -> None:
    """Move label por delta em pixels, convertendo para data coords."""
    num_x, num_y = _pos_to_numeric(*label.get_position())
    curr_px = ax.transData.transform((num_x, num_y))
    new_px = (curr_px[0] + dx_px, curr_px[1] + dy_px)
    new_data = ax.transData.inverted().transform(new_px)
    # Pin coordenada que nao deve mudar para evitar drift de roundtrip
    final_x = num_x if dx_px == 0 else new_data[0]
    final_y = num_y if dy_px == 0 else new_data[1]
    label.set_position((final_x, final_y))
