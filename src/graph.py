"""Модуль построения графа зависимостей с помощью рекурсивного DFS."""

from typing import Callable, Dict, List, Optional, Set, Tuple

EMPTY_LENGTH = 0
START_DEPTH = 0


class GraphCycleError(Exception):
    """Исключение при обнаружении циклической зависимости."""


class DependencyGraph:
    """Структура данных для хранения графа зависимостей."""

    def __init__(self, root: str, filter_substring: str = "") -> None:
        """Инициализирует граф зависимостей.

        Args:
            root: Корневой пакет.
            filter_substring: Подстрока для фильтрации пакетов.
        """
        self.root = root
        self.filter_substring = filter_substring
        self.adjacency: Dict[str, List[str]] = {}
        self.cycles: List[Tuple[str, str]] = []
        self.nodes: Set[str] = set()

    def add_node(self, node: str) -> None:
        """Добавляет вершину в граф, если её еще нет."""
        self.nodes.add(node)
        if node not in self.adjacency:
            self.adjacency[node] = []

    def add_edge(self, from_node: str, to_node: str) -> None:
        """Добавляет направленное ребро в граф."""
        self.add_node(from_node)
        self.add_node(to_node)
        if to_node not in self.adjacency[from_node]:
            self.adjacency[from_node].append(to_node)

    def add_cycle(self, from_node: str, to_node: str) -> None:
        """Регистрирует обнаруженную циклическую зависимость."""
        pair = (from_node, to_node)
        if pair not in self.cycles:
            self.cycles.append(pair)


class DfsContext:
    """Контекст для хранения состояния рекурсивного обхода DFS."""

    def __init__(
        self,
        graph: DependencyGraph,
        fetcher: Callable[[str], List[str]],
        max_depth: Optional[int] = None,
    ) -> None:
        """Инициализирует контекст обхода DFS.

        Args:
            graph: Граф для заполнения.
            fetcher: Функция получения списка прямых зависимостей.
            max_depth: Ограничение глубины рекурсии.
        """
        self.graph = graph
        self.fetcher = fetcher
        self.max_depth = max_depth
        self.call_stack: List[str] = []
        self.visited: Set[str] = set()


def _is_filtered(name: str, filter_sub: str) -> bool:
    """Проверяет, должен ли пакет быть отфильтрован по подстроке.

    Args:
        name: Имя пакета.
        filter_sub: Фильтрующая подстрока.

    Returns:
        True, если пакет подлежит исключению, иначе False.
    """
    if len(filter_sub) == EMPTY_LENGTH:
        return False
    return filter_sub in name


def _dfs_visit(pkg: str, depth: int, ctx: DfsContext) -> None:
    """Рекурсивный шаг обхода в глубину (DFS) для построения графа.

    Args:
        pkg: Текущий анализируемый пакет.
        depth: Текущая глубина рекурсии.
        ctx: Контекст обхода DFS.
    """
    ctx.graph.add_node(pkg)
    ctx.visited.add(pkg)
    ctx.call_stack.append(pkg)

    if ctx.max_depth is not None and depth >= ctx.max_depth:
        ctx.call_stack.pop()
        return

    deps = ctx.fetcher(pkg)
    for dep in sorted(deps):
        if _is_filtered(dep, ctx.graph.filter_substring):
            continue

        ctx.graph.add_edge(pkg, dep)

        if dep in ctx.call_stack:
            ctx.graph.add_cycle(pkg, dep)
            continue

        if dep not in ctx.visited:
            _dfs_visit(dep, depth + 1, ctx)

    ctx.call_stack.pop()


def build_dependency_graph(
    root_package: str,
    fetcher: Callable[[str], List[str]],
    filter_substring: str = "",
    max_depth: Optional[int] = None,
) -> DependencyGraph:
    """Строит граф зависимостей с помощью рекурсивного алгоритма DFS.

    Args:
        root_package: Исходный пакет.
        fetcher: Функция поставщика зависимостей по имени пакета.
        filter_substring: Подстрока для исключения пакетов из анализа.
        max_depth: Максимальная глубина обхода графа.

    Returns:
        Построенный объект DependencyGraph.
    """
    graph = DependencyGraph(
        root=root_package,
        filter_substring=filter_substring,
    )
    ctx = DfsContext(graph, fetcher, max_depth)
    _dfs_visit(root_package, START_DEPTH, ctx)
    return graph
