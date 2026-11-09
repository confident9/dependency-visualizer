"""Модульные тесты для рекурсивного алгоритма построения графа DFS (Этап 3)."""

import os
import unittest

from src.collector import get_direct_dependencies
from src.graph import build_dependency_graph


class TestGraph(unittest.TestCase):
    """Набор тестов для проверки построения графа зависимостей."""

    def setUp(self) -> None:
        """Находит путь к тестовым данным."""
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.data_dir = os.path.join(self.base_dir, "test_data")

    def _make_fetcher(self, filename: str):
        """Создает функцию получения зависимостей из файла тестовых данных."""
        path = os.path.join(self.data_dir, filename)

        def fetcher(pkg: str):
            deps = get_direct_dependencies(
                package_name=pkg,
                repo_url=path,
                test_mode=True,
            )
            return [d.name for d in deps]

        return fetcher

    def test_linear_graph(self) -> None:
        """Проверка построения линейного графа A -> B -> C -> D."""
        fetcher = self._make_fetcher("linear.json")
        graph = build_dependency_graph("A", fetcher)
        self.assertEqual(graph.nodes, {"A", "B", "C", "D"})
        self.assertEqual(graph.adjacency["A"], ["B"])
        self.assertEqual(graph.adjacency["B"], ["C"])
        self.assertEqual(graph.adjacency["C"], ["D"])
        self.assertEqual(graph.adjacency["D"], [])
        self.assertEqual(len(graph.cycles), 0)

    def test_diamond_graph(self) -> None:
        """Проверка построения ромбовидного графа A -> B, C; B, C -> D."""
        fetcher = self._make_fetcher("diamond.json")
        graph = build_dependency_graph("A", fetcher)
        self.assertEqual(graph.nodes, {"A", "B", "C", "D"})
        self.assertEqual(graph.adjacency["A"], ["B", "C"])
        self.assertEqual(graph.adjacency["B"], ["D"])
        self.assertEqual(graph.adjacency["C"], ["D"])
        self.assertEqual(len(graph.cycles), 0)

    def test_cycle_detection(self) -> None:
        """Проверка корректной обработки циклических зависимостей."""
        fetcher = self._make_fetcher("cycle.json")
        graph = build_dependency_graph("A", fetcher)
        self.assertIn("A", graph.nodes)
        self.assertIn("B", graph.nodes)
        self.assertIn("C", graph.nodes)
        self.assertIn("D", graph.nodes)
        self.assertIn(("C", "A"), graph.cycles)

    def test_filter_substring(self) -> None:
        """Проверка исключения пакетов с заданной подстрокой."""
        fetcher = self._make_fetcher("filter.json")
        graph = build_dependency_graph("A", fetcher, filter_substring="TEST_")
        self.assertIn("A", graph.nodes)
        self.assertIn("B", graph.nodes)
        self.assertIn("C", graph.nodes)
        self.assertIn("D", graph.nodes)
        self.assertNotIn("TEST_X", graph.nodes)
        self.assertNotIn("TEST_Y", graph.nodes)

    def test_max_depth(self) -> None:
        """Проверка ограничения максимальной глубины обхода."""
        fetcher = self._make_fetcher("linear.json")
        graph = build_dependency_graph("A", fetcher, max_depth=1)
        self.assertIn("A", graph.nodes)
        self.assertIn("B", graph.nodes)
        self.assertNotIn("C", graph.nodes)
        self.assertNotIn("D", graph.nodes)


if __name__ == "__main__":
    unittest.main()
