"""Модуль визуализации графа зависимостей в форматах Graphviz DOT и SVG."""

import os
import shutil
import subprocess
from typing import Dict, List, Optional, Set, Tuple
from src.graph import DependencyGraph

EMPTY_COUNT = 0
SUCCESS_RETURN_CODE = 0
BOX_WIDTH = 140
BOX_HEIGHT = 40
LAYER_STEP_Y = 90
BOX_STEP_X = 170
OFFSET_X = 50
OFFSET_Y = 50
MIN_CANVAS_WIDTH = 400
MIN_CANVAS_HEIGHT = 200
HALF_DIVISOR = 2
CYCLE_CURVE_OFFSET = 40


def generate_dot(graph: DependencyGraph) -> str:
    """Формирует текстовое описание графа в формате Graphviz DOT.

    Args:
        graph: Граф зависимостей.

    Returns:
        Строка с описанием графа на языке DOT.
    """
    lines = [
        "digraph dependencies {",
        "    rankdir=TB;",
        '    node [shape=box, style="rounded,filled", '
        'fillcolor="#e8f0fe", fontname="sans-serif"];',
        '    edge [fontname="sans-serif", fontsize=10];',
    ]
    if graph.root in graph.nodes:
        lines.append(
            f'    "{graph.root}" [fillcolor="#a8d5e5", '
            'style="rounded,filled,bold"];'
        )
    for node in sorted(graph.nodes):
        if node != graph.root:
            lines.append(f'    "{node}";')
    for src in sorted(graph.adjacency.keys()):
        for dst in sorted(graph.adjacency[src]):
            is_cycle = (src, dst) in graph.cycles
            if is_cycle:
                lines.append(
                    f'    "{src}" -> "{dst}" [color="red", '
                    'style="dashed", label="cycle"];'
                )
            else:
                lines.append(f'    "{src}" -> "{dst}";')
    lines.append("}")
    return "\n".join(lines)


def _compute_node_levels(graph: DependencyGraph) -> Dict[str, int]:
    """Вычисляет уровни узлов графа от корня для визуализации.

    Args:
        graph: Граф зависимостей.

    Returns:
        Словарь соответствия имени узла его уровню глубины.
    """
    levels: Dict[str, int] = {}
    queue: List[str] = []
    visited: Set[str] = set()
    if graph.root in graph.nodes:
        levels[graph.root] = 0
        queue.append(graph.root)
        visited.add(graph.root)
    while queue:
        curr = queue.pop(0)
        curr_lvl = levels.get(curr, 0)
        for child in graph.adjacency.get(curr, []):
            if (curr, child) in graph.cycles:
                continue
            if child not in visited:
                visited.add(child)
                levels[child] = curr_lvl + 1
                queue.append(child)
    for node in sorted(graph.nodes):
        if node not in levels:
            levels[node] = 0
    return levels


def _build_node_coordinates(
    graph: DependencyGraph, levels: Dict[str, int]
) -> Dict[str, Tuple[int, int]]:
    """Вычисляет 2D координаты для каждого узла графа.

    Args:
        graph: Граф зависимостей.
        levels: Словарь уровней узлов.

    Returns:
        Словарь координат (x, y) верхнего левого угла прямоугольника.
    """
    layer_nodes: Dict[int, List[str]] = {}
    for node in sorted(graph.nodes):
        lvl = levels.get(node, 0)
        layer_nodes.setdefault(lvl, []).append(node)
    coords: Dict[str, Tuple[int, int]] = {}
    for lvl, n_list in layer_nodes.items():
        y = OFFSET_Y + lvl * LAYER_STEP_Y
        for idx, node in enumerate(n_list):
            x = OFFSET_X + idx * BOX_STEP_X
            coords[node] = (x, y)
    return coords


def _render_svg_markers() -> str:
    """Генерирует SVG-определения наконечников стрелок."""
    return (
        "  <defs>\n"
        '    <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">\n'
        '      <path d="M 0 0 L 10 5 L 0 10 z" fill="#333333" />\n'
        "    </marker>\n"
        '    <marker id="arrow-cycle" viewBox="0 0 10 10" refX="10" '
        'refY="5" markerWidth="6" markerHeight="6" '
        'orient="auto-start-reverse">\n'
        '      <path d="M 0 0 L 10 5 L 0 10 z" fill="#d32f2f" />\n'
        "    </marker>\n"
        "  </defs>"
    )


def _render_svg_nodes(
    graph: DependencyGraph, coords: Dict[str, Tuple[int, int]]
) -> List[str]:
    """Формирует SVG-элементы прямоугольников и подписей для узлов."""
    elements: List[str] = []
    text_y_offset = 24
    for node in sorted(graph.nodes):
        x, y = coords.get(node, (OFFSET_X, OFFSET_Y))
        is_root = node == graph.root
        fill = "#a8d5e5" if is_root else "#e8f0fe"
        stroke = "#1a73e8" if is_root else "#70757a"
        weight = "2" if is_root else "1"
        elements.append(
            f'  <rect x="{x}" y="{y}" width="{BOX_WIDTH}" '
            f'height="{BOX_HEIGHT}" rx="6" ry="6" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{weight}" />'
        )
        tx = x + BOX_WIDTH // HALF_DIVISOR
        ty = y + text_y_offset
        elements.append(
            f'  <text x="{tx}" y="{ty}" font-family="sans-serif" '
            f'font-size="12" text-anchor="middle" '
            f'fill="#202124">{node}</text>'
        )
    return elements


def _render_svg_edges(
    graph: DependencyGraph, coords: Dict[str, Tuple[int, int]]
) -> List[str]:
    """Формирует SVG-элементы ребер графа со стрелками."""
    elements: List[str] = []
    half_w = BOX_WIDTH // HALF_DIVISOR
    for src in sorted(graph.adjacency.keys()):
        for dst in sorted(graph.adjacency[src]):
            sx, sy = coords.get(src, (OFFSET_X, OFFSET_Y))
            dx, dy = coords.get(dst, (OFFSET_X, OFFSET_Y))
            is_cycle = (src, dst) in graph.cycles
            if is_cycle:
                cx1 = sx - CYCLE_CURVE_OFFSET
                cy1 = (sy + dy) // HALF_DIVISOR
                elements.append(
                    f'  <path d="M {sx} {sy + BOX_HEIGHT // HALF_DIVISOR} '
                    f'Q {cx1} {cy1} {dx} {dy + BOX_HEIGHT // HALF_DIVISOR}" '
                    'fill="none" stroke="#d32f2f" stroke-width="1.5" '
                    'stroke-dasharray="4,4" marker-end="url(#arrow-cycle)" />'
                )
            else:
                x1, y1 = sx + half_w, sy + BOX_HEIGHT
                x2, y2 = dx + half_w, dy
                elements.append(
                    f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                    'stroke="#333333" stroke-width="1.5" '
                    'marker-end="url(#arrow)" />'
                )
    return elements


def generate_svg_text(graph: DependencyGraph) -> str:
    """Генерирует полное SVG-изображение графа без внешних зависимостей.

    Args:
        graph: Граф зависимостей.

    Returns:
        Строка с XML-разметкой SVG.
    """
    levels = _compute_node_levels(graph)
    coords = _build_node_coordinates(graph, levels)
    max_x = max((c[0] for c in coords.values()), default=MIN_CANVAS_WIDTH)
    max_y = max((c[1] for c in coords.values()), default=MIN_CANVAS_HEIGHT)
    width = max(max_x + BOX_WIDTH + OFFSET_X, MIN_CANVAS_WIDTH)
    height = max(max_y + BOX_HEIGHT + OFFSET_Y, MIN_CANVAS_HEIGHT)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        _render_svg_markers(),
    ]
    parts.extend(_render_svg_edges(graph, coords))
    parts.extend(_render_svg_nodes(graph, coords))
    parts.append("</svg>")
    return "\n".join(parts)


def _try_render_with_dot(dot_path: str, svg_path: str) -> bool:
    """Пытается отрендерить SVG с помощью системной утилиты dot.

    Args:
        dot_path: Путь к исходному файлу DOT.
        svg_path: Путь к результирующему файлу SVG.

    Returns:
        True, если утилита dot завершилась успешно, иначе False.
    """
    dot_tool = shutil.which("dot")
    if not dot_tool:
        return False
    cmd = [dot_tool, "-Tsvg", dot_path, "-o", svg_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode == SUCCESS_RETURN_CODE


def export_graph(
    graph: DependencyGraph,
    output_svg_path: str,
    dot_output_path: Optional[str] = None,
) -> str:
    """Экспортирует граф в файлы DOT и SVG.

    При наличии утилиты dot в системе используется она. В противном случае
    применяется встроенный автономный генератор SVG.

    Args:
        graph: Граф зависимостей.
        output_svg_path: Путь для сохранения SVG файла.
        dot_output_path: Опциональный путь для сохранения DOT файла.

    Returns:
        Сообщение о способе сохранения и путях к файлам.
    """
    if dot_output_path:
        out_dir = os.path.dirname(dot_output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(dot_output_path, "w", encoding="utf-8") as f:
            f.write(generate_dot(graph))

    svg_dir = os.path.dirname(output_svg_path)
    if svg_dir:
        os.makedirs(svg_dir, exist_ok=True)

    if dot_output_path and _try_render_with_dot(
        dot_output_path, output_svg_path
    ):
        return f"Граф сохранен через Graphviz dot: {output_svg_path}"

    with open(output_svg_path, "w", encoding="utf-8") as f:
        f.write(generate_svg_text(graph))
    return f"Граф сохранен через автономный SVG рендерер: {output_svg_path}"
