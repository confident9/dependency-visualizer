"""Модульные тесты для вычисления порядка загрузки зависимостей (Этап 4)."""

import os
import unittest
from typing import Callable, List

from src.collector import get_direct_dependencies
from src.graph import build_dependency_graph
from src.order import compute_loading_order, format_loading_order

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "test_data")


def _make_data_fetcher(filename: str) -> Callable[[str], List[str]]:
    """Создает функцию получения зависимостей из файла тестовых данных.

    Args:
        filename: Имя файла в test_data.

    Returns:
        Функция, возвращающая список зависимостей.
    """
    path = os.path.join(DATA_DIR, filename)

    def fetcher(pkg: str) -> List[str]:
        """Извлекает имена зависимостей для пакета."""
        deps = get_direct_dependencies(
            package_name=pkg,
            repo_url=path,
            test_mode=True,
        )
        return [d.name for d in deps]

    return fetcher


class TestOrder(unittest.TestCase):
    """Набор тестов для проверки порядка загрузки зависимостей."""

    def test_linear_order(self) -> None:
        """Проверка порядка загрузки для линейного графа."""
        fetcher = _make_data_fetcher("linear.json")
        graph = build_dependency_graph("A", fetcher)
        order = compute_loading_order(graph)
        self.assertEqual(order, ["D", "C", "B", "A"])

    def test_diamond_order(self) -> None:
        """Проверка порядка загрузки для ромбовидного графа."""
        fetcher = _make_data_fetcher("diamond.json")
        graph = build_dependency_graph("A", fetcher)
        order = compute_loading_order(graph)
        self.assertEqual(order[0], "D")
        self.assertIn("B", order[1:3])
        self.assertIn("C", order[1:3])
        self.assertEqual(order[-1], "A")

    def test_cycle_order(self) -> None:
        """Проверка порядка загрузки при наличии цикла."""
        fetcher = _make_data_fetcher("cycle.json")
        graph = build_dependency_graph("A", fetcher)
        order = compute_loading_order(graph)
        self.assertIn("D", order)
        self.assertIn("C", order)
        self.assertIn("B", order)
        self.assertIn("A", order)

    def test_format_loading_order(self) -> None:
        """Проверка форматирования вывода порядка загрузки."""
        order = ["D", "C", "B", "A"]
        text = format_loading_order(order)
        self.assertIn("Порядок загрузки зависимостей", text)
        self.assertIn("1. D", text)
        self.assertIn("4. A", text)


if __name__ == "__main__":
    unittest.main()
