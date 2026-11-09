"""Модуль определения порядка загрузки зависимостей (Этап 4)."""

from typing import List, Set
from src.graph import DependencyGraph

EMPTY_LENGTH = 0


def _post_order_dfs(
    node: str,
    graph: DependencyGraph,
    visited: Set[str],
    visiting: Set[str],
    order: List[str],
) -> None:
    """Вспомогательный рекурсивный обход для построения порядка загрузки.

    Args:
        node: Текущий узел графа.
        graph: Граф зависимостей.
        visited: Множество полностью обработанных узлов.
        visiting: Множество узлов в текущем стеке рекурсии.
        order: Результирующий список порядка загрузки.
    """
    visiting.add(node)
    children = graph.adjacency.get(node, [])
    for child in sorted(children):
        if child in visiting:
            continue
        if child not in visited:
            _post_order_dfs(child, graph, visited, visiting, order)
    visiting.remove(node)
    visited.add(node)
    if node not in order:
        order.append(node)


def compute_loading_order(graph: DependencyGraph) -> List[str]:
    """Вычисляет порядок загрузки зависимостей для целевого пакета.

    Зависимости без потомков загружаются первыми, а корневой пакет — последним.

    Args:
        graph: Построенный граф зависимостей.

    Returns:
        Список имен пакетов в порядке их загрузки и инициализации.
    """
    if not graph.nodes:
        return []
    visited: Set[str] = set()
    visiting: Set[str] = set()
    order: List[str] = []
    _post_order_dfs(graph.root, graph, visited, visiting, order)
    return order


def format_loading_order(order: List[str]) -> str:
    """Форматирует порядок загрузки зависимостей для отображения.

    Args:
        order: Список имен пакетов в порядке загрузки.

    Returns:
        Строка с пронумерованным порядком загрузки пакетов.
    """
    if len(order) == EMPTY_LENGTH:
        return "Порядок загрузки пуст."
    lines = ["Порядок загрузки зависимостей (снизу вверх):"]
    for idx, pkg in enumerate(order):
        step = idx + 1
        lines.append(f"  {step}. {pkg}")
    return "\n".join(lines)
