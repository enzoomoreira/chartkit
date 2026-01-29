"""
Deteccao e resolucao de colisao de labels em graficos.

Este modulo detecta quando labels de highlight (gerados por highlight_last_bar
ou highlight_last_point) colidem com elementos visuais como barras, e
reposiciona automaticamente os labels para evitar sobreposicao.
"""

from matplotlib.text import Annotation

from ..settings import get_config
from ..styling.theme import theme


def resolve_collisions(
    ax,
    margin_px: int = None,
    guide_threshold_px: int = None,
) -> None:
    """
    Detecta e resolve colisoes entre annotations e patches (barras).

    Itera sobre todos os annotations registrados em ax._charting_annotations
    e verifica se algum colide com patches (barras) do grafico. Se houver
    colisao, reposiciona o annotation para cima e adiciona uma linha guia
    quando a distancia for grande.

    Args:
        ax: Matplotlib Axes com annotations registrados em _charting_annotations
        margin_px: Margem em pixels para detectar colisao. Se None, usa config.
        guide_threshold_px: Distancia minima em pixels para adicionar linha guia.
                           Se None, usa config.
    """
    config = get_config().collision

    # Usa valores da config se nao especificados
    if margin_px is None:
        margin_px = config.margin_px
    if guide_threshold_px is None:
        guide_threshold_px = config.guide_threshold_px

    annotations = getattr(ax, "_charting_annotations", [])
    if not annotations:
        return

    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    # Coleta patches (barras) do grafico
    patches = list(ax.patches)
    if not patches:
        return

    for annot in annotations:
        _resolve_single_collision(
            ax, annot, patches, renderer, margin_px, guide_threshold_px
        )


def _resolve_single_collision(
    ax,
    annot: Annotation,
    patches: list,
    renderer,
    margin_px: int,
    guide_threshold_px: int,
) -> None:
    """
    Resolve colisao de um annotation individual com patches.

    Verifica se o bounding box do annotation (expandido pela margem) colide
    com algum patch. Se colidir, move o annotation para acima do patch mais
    alto e adiciona uma linha guia se a distancia for significativa.

    Args:
        ax: Matplotlib Axes
        annot: Annotation a ser verificado/reposicionado
        patches: Lista de patches (barras) do grafico
        renderer: Renderer do matplotlib para calculo de bounding boxes
        margin_px: Margem em pixels para deteccao de colisao
        guide_threshold_px: Distancia minima para adicionar linha guia
    """
    config = get_config().collision
    colors = get_config().colors

    annot_bbox = annot.get_window_extent(renderer)

    # Evita divisao por zero se bbox tiver dimensao nula
    if annot_bbox.width == 0 or annot_bbox.height == 0:
        return

    # Expande bbox com margem
    annot_bbox_expanded = annot_bbox.expanded(
        1 + margin_px / annot_bbox.width, 1 + margin_px / annot_bbox.height
    )

    # Encontra patches que colidem com o annotation
    colliding_patches = []
    for patch in patches:
        patch_bbox = patch.get_window_extent(renderer)
        if annot_bbox_expanded.overlaps(patch_bbox):
            colliding_patches.append((patch, patch_bbox))

    if not colliding_patches:
        return

    # Encontra o topo mais alto entre patches colidindo (em pixels)
    max_top_px = max(bbox.y1 for _, bbox in colliding_patches)

    # Posicao atual do annotation em pixels (base do texto)
    annot_pos_px = annot_bbox.y0

    # Nova posicao: acima do patch mais alto + margem + folga extra
    new_top_px = max_top_px + margin_px + config.extra_padding_px
    offset_needed = new_top_px - annot_pos_px

    if offset_needed <= 0:
        return  # Ja esta acima, nao precisa ajustar

    # Converte offset de pixels para pontos
    offset_points = offset_needed * config.px_to_points_ratio

    # Atualiza posicao do annotation
    current_xytext = annot.xyann
    new_xytext = (current_xytext[0], current_xytext[1] + offset_points)
    annot.xyann = new_xytext

    # Adiciona linha guia se distancia for grande
    if offset_needed > guide_threshold_px:
        # Cria nova annotation com apenas a linha guia (texto vazio)
        ax.annotate(
            "",  # Texto vazio - apenas a linha
            xy=annot.xy,  # Ponto de dados original
            xytext=new_xytext,
            textcoords="offset points",
            arrowprops=dict(
                arrowstyle="-",
                color=colors.grid,
                alpha=0.6,
                lw=1,
            ),
            zorder=1,  # Atras do texto
        )
