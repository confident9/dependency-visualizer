"""Модульные тесты для модуля конфигурации INI (Этап 1)."""

import os
import tempfile
import unittest

from src.config import AppConfig, ConfigError, load_config


def _write_ini_file(dir_path: str, content: str) -> str:
    """Вспомогательная функция для записи INI-файла.

    Args:
        dir_path: Каталог для размещения файла.
        content: Содержимое файла.

    Returns:
        Путь к созданному файлу.
    """
    path = os.path.join(dir_path, "config.ini")
    with open(path, "w", encoding="utf-8") as file:
        file.write(content)
    return path


class TestConfig(unittest.TestCase):
    """Набор тестов для проверки загрузки и валидации конфигурации."""

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
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = _write_ini_file(tmp_dir, content)
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
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_path = os.path.join(tmp_dir, "missing.ini")
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
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = _write_ini_file(tmp_dir, content)
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
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = _write_ini_file(tmp_dir, content)
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
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = _write_ini_file(tmp_dir, content)
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
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = _write_ini_file(tmp_dir, content)
            with self.assertRaises(ConfigError):
                load_config(path)

    def test_valid_test_mode_repo(self) -> None:
        """Проверка валидации тестового репозитория."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = os.path.join(tmp_dir, "graph.json")
            with open(test_file, "w", encoding="utf-8") as file:
                file.write("{}")

            content = (
                f"[settings]\n"
                f"package_name = A\n"
                f"repo_url = {test_file}\n"
                f"test_mode = true\n"
                f"output_file = out.svg\n"
            )
            path = _write_ini_file(tmp_dir, content)
            cfg = load_config(path)
            self.assertTrue(cfg.test_mode)
            self.assertEqual(cfg.package_name, "A")


if __name__ == "__main__":
    unittest.main()
