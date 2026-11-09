"""Тесты для модуля визуализации графа зависимостей (Этап 5)."""

import os
import tempfile
import unittest
from src.graph import DependencyGraph
from src.visualizer import export_graph, generate_dot, generate_svg_text

EMPTY_SIZE = 0


class TestVisualizer(unittest.TestCase):
    """Набор тестов для генератора DOT и SVG."""

    def setUp(self) -> None:
        """Создает тестовый граф перед каждым тестом."""
        self.graph = DependencyGraph(root="A")
        self.graph.add_edge("A", "B")
        self.graph.add_edge("B", "C")
        self.graph.add_edge("C", "A")
        self.graph.add_cycle("C", "A")

    def test_generate_dot_structure(self) -> None:
        """Проверяет общую структуру сгенерированного DOT файла."""
        dot = generate_dot(self.graph)
        self.assertIn("digraph dependencies {", dot)
        self.assertIn('"A" [fillcolor="#a8d5e5"', dot)
        self.assertIn('"A" -> "B";', dot)
        self.assertIn('"B" -> "C";', dot)
        self.assertIn('color="red"', dot)
        self.assertIn('style="dashed"', dot)
        self.assertIn('label="cycle"', dot)

    def test_generate_svg_text(self) -> None:
        """Проверяет генерацию SVG разметки автономным генератором."""
        svg = generate_svg_text(self.graph)
        self.assertTrue(svg.startswith("<svg"))
        self.assertTrue(svg.strip().endswith("</svg>"))
        self.assertIn("<rect", svg)
        self.assertIn("<text", svg)
        self.assertIn(">A<", svg)
        self.assertIn(">B<", svg)
        self.assertIn(">C<", svg)
        self.assertIn('marker id="arrow"', svg)
        self.assertIn('marker id="arrow-cycle"', svg)

    def test_export_graph_creates_files(self) -> None:
        """Проверяет создание файлов DOT и SVG на диске."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dot_path = os.path.join(tmp_dir, "graph.dot")
            svg_path = os.path.join(tmp_dir, "graph.svg")
            msg = export_graph(self.graph, svg_path, dot_path)
            self.assertIn("Граф сохранен", msg)
            self.assertTrue(os.path.exists(dot_path))
            self.assertTrue(os.path.exists(svg_path))
            self.assertGreater(os.path.getsize(dot_path), EMPTY_SIZE)
            self.assertGreater(os.path.getsize(svg_path), EMPTY_SIZE)


if __name__ == "__main__":
    unittest.main()
