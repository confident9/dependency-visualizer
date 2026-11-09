"""Модульные тесты для модуля сбора зависимостей Cargo (Этап 2)."""

import json
import os
import tempfile
import unittest

from src.collector import (
    CollectorError,
    DependencyInfo,
    _parse_dependencies_payload,
    format_direct_dependencies,
    get_direct_dependencies,
)


class TestCollector(unittest.TestCase):
    """Набор тестов для проверки извлечения прямых зависимостей."""

    def setUp(self) -> None:
        """Создает временную директорию для тестовых данных."""
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        """Очищает временную директорию."""
        self.temp_dir.cleanup()

    def _create_test_repo(self, data: dict) -> str:
        """Создает тестовый JSON-файл репозитория.

        Args:
            data: Данные графа зависимостей.

        Returns:
            Путь к созданному файлу.
        """
        path = os.path.join(self.temp_dir.name, "test_repo.json")
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file)
        return path

    def test_direct_deps_test_mode(self) -> None:
        """Проверка получения прямых зависимостей в тестовом режиме."""
        data = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": [],
            "D": [],
        }
        path = self._create_test_repo(data)
        deps = get_direct_dependencies(
            package_name="A",
            repo_url=path,
            test_mode=True,
        )
        dep_names = [d.name for d in deps]
        self.assertEqual(dep_names, ["B", "C"])

    def test_package_not_in_test_repo(self) -> None:
        """Проверка ошибки при отсутствии пакета в тестовом репозитории."""
        data = {"A": ["B"]}
        path = self._create_test_repo(data)
        with self.assertRaises(CollectorError):
            get_direct_dependencies(
                package_name="Z",
                repo_url=path,
                test_mode=True,
            )

    def test_parse_crates_io_payload(self) -> None:
        """Проверка парсинга ответа Crates.io API."""
        sample_payload = {
            "dependencies": [
                {
                    "crate_id": "serde",
                    "req": "^1.0",
                    "kind": "normal",
                    "optional": False,
                },
                {
                    "crate_id": "dev_test",
                    "req": "^0.1",
                    "kind": "dev",
                    "optional": False,
                },
                {
                    "crate_id": "opt_crate",
                    "req": "^2.0",
                    "kind": "normal",
                    "optional": True,
                },
            ]
        }
        deps = _parse_dependencies_payload(sample_payload)
        self.assertEqual(len(deps), 1)
        self.assertEqual(deps[0].name, "serde")
        self.assertEqual(deps[0].req, "^1.0")

    def test_format_direct_dependencies(self) -> None:
        """Проверка строкового форматирования прямых зависимостей."""
        deps = [
            DependencyInfo(name="libc", req="^0.2"),
            DependencyInfo(name="log", req="^0.4"),
        ]
        out = format_direct_dependencies("my_pkg", "1.0.0", deps)
        self.assertIn("Прямые зависимости пакета 'my_pkg'", out)
        self.assertIn("libc (^0.2)", out)
        self.assertIn("log (^0.4)", out)

    def test_format_empty_dependencies(self) -> None:
        """Проверка форматирования пустого списка зависимостей."""
        out = format_direct_dependencies("leaf", "1.0.0", [])
        self.assertIn("(зависимостей нет)", out)


if __name__ == "__main__":
    unittest.main()
