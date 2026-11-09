"""Модульные тесты для модуля конфигурации INI (Этап 1)."""

import os
import tempfile
import unittest

from src.config import AppConfig, ConfigError, load_config


class TestConfig(unittest.TestCase):
    """Набор тестов для проверки загрузки и валидации конфигурации."""

    def setUp(self) -> None:
        """Создает временный каталог для тестовых файлов."""
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        """Очищает временный каталог."""
        self.temp_dir.cleanup()

    def _write_ini(self, content: str) -> str:
        """Вспомогательный метод для записи INI-файла.

        Args:
            content: Содержимое файла.

        Returns:
            Путь к созданному файлу.
        """
        path = os.path.join(self.temp_dir.name, "config.ini")
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)
        return path

    def test_valid_real_config(self) -> None:
        """Проверка корректной конфигурации для реального репозитория."""
        content = (
            "[settings]\n"
            "package_name = rand\n"
            "repo_url = https://crates.io/api/v1/crates\n"
            "test_mode = false\n"
            "package_version = 0.8.5\n"
            "output_file = result.svg\n"
            "filter_substring = libc\n"
        )
        path = self._write_ini(content)
        cfg = load_config(path)
        self.assertEqual(cfg.package_name, "rand")
        self.assertEqual(cfg.repo_url, "https://crates.io/api/v1/crates")
        self.assertFalse(cfg.test_mode)
        self.assertEqual(cfg.package_version, "0.8.5")
        self.assertEqual(cfg.output_file, "result.svg")
        self.assertEqual(cfg.filter_substring, "libc")

    def test_format_key_value(self) -> None:
        """Проверка форматирования параметров в виде ключ-значение."""
        cfg = AppConfig(
            package_name="serde",
            repo_url="https://crates.io",
            test_mode=False,
            package_version="1.0.0",
            output_file="out.svg",
            filter_substring="",
        )
        formatted = cfg.format_key_value()
        self.assertIn("package_name = serde", formatted)
        self.assertIn("test_mode = false", formatted)
        self.assertIn("output_file = out.svg", formatted)

    def test_missing_file(self) -> None:
        """Проверка ошибки при отсутствии файла."""
        bad_path = os.path.join(self.temp_dir.name, "missing.ini")
        with self.assertRaises(ConfigError):
            load_config(bad_path)

    def test_empty_package_name(self) -> None:
        """Проверка ошибки при пустом имени пакета."""
        content = (
            "[settings]\n"
            "package_name = \n"
            "repo_url = https://crates.io\n"
            "package_version = 1.0.0\n"
            "output_file = graph.svg\n"
        )
        path = self._write_ini(content)
        with self.assertRaises(ConfigError):
            load_config(path)

    def test_invalid_output_extension(self) -> None:
        """Проверка ошибки при неверном расширении выходного файла."""
        content = (
            "[settings]\n"
            "package_name = rand\n"
            "repo_url = https://crates.io\n"
            "package_version = 1.0.0\n"
            "output_file = graph.png\n"
        )
        path = self._write_ini(content)
        with self.assertRaises(ConfigError):
            load_config(path)

    def test_invalid_boolean(self) -> None:
        """Проверка ошибки при некорректном булевом значении."""
        content = (
            "[settings]\n"
            "package_name = rand\n"
            "repo_url = https://crates.io\n"
            "test_mode = invalid_bool\n"
            "package_version = 1.0.0\n"
            "output_file = graph.svg\n"
        )
        path = self._write_ini(content)
        with self.assertRaises(ConfigError):
            load_config(path)

    def test_missing_version_for_real_repo(self) -> None:
        """Проверка ошибки отсутствия версии для реального репозитория."""
        content = (
            "[settings]\n"
            "package_name = rand\n"
            "repo_url = https://crates.io\n"
            "test_mode = false\n"
            "package_version = \n"
            "output_file = graph.svg\n"
        )
        path = self._write_ini(content)
        with self.assertRaises(ConfigError):
            load_config(path)

    def test_valid_test_mode_repo(self) -> None:
        """Проверка валидации тестового репозитория."""
        test_file = os.path.join(self.temp_dir.name, "graph.json")
        with open(test_file, "w", encoding="utf-8") as file:
            file.write("{}")

        content = (
            f"[settings]\n"
            f"package_name = A\n"
            f"repo_url = {test_file}\n"
            f"test_mode = true\n"
            f"output_file = out.svg\n"
        )
        path = self._write_ini(content)
        cfg = load_config(path)
        self.assertTrue(cfg.test_mode)
        self.assertEqual(cfg.package_name, "A")


if __name__ == "__main__":
    unittest.main()
