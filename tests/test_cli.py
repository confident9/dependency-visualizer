"""Модульные тесты для командного интерфейса (CLI)."""

import os
import tempfile
from typing import Tuple
import unittest
from src.cli import (
    FAILURE_EXIT,
    STAGE_1,
    STAGE_ALL,
    SUCCESS_EXIT,
    main,
    parse_args,
    run_stage_1,
    run_stage_2,
    run_stage_3,
    run_stage_4,
    run_stage_5,
)


def _create_test_files(dir_path: str) -> Tuple[str, str]:
    """Создает временные файлы для тестирования CLI.

    Args:
        dir_path: Путь к временной директории.

    Returns:
        Кортеж из пути к файлу конфигурации и пути к выходному файлу.
    """
    repo_file = os.path.join(dir_path, "repo.json")
    with open(repo_file, "w", encoding="utf-8") as f:
        f.write('{"A": ["B"], "B": []}')
    out_svg = os.path.join(dir_path, "graph.svg")
    config_file = os.path.join(dir_path, "config.ini")
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(
            "[visualizer]\n"
            "package_name = A\n"
            f"repo_url = {repo_file}\n"
            "test_mode = true\n"
            "package_version = 1.0.0\n"
            f"output_file = {out_svg}\n"
            "filter_substring = \n"
        )
    return config_file, out_svg


class TestCli(unittest.TestCase):
    """Набор тестов для проверки функций CLI."""

    def test_parse_args_defaults(self) -> None:
        """Проверяет значения по умолчанию аргументов CLI."""
        args = parse_args([])
        self.assertEqual(args.config, "config.ini")
        self.assertEqual(args.stage, STAGE_ALL)

    def test_parse_args_custom(self) -> None:
        """Проверяет разбор переданных аргументов CLI."""
        args = parse_args(["-c", "my.ini", "-s", STAGE_1])
        self.assertEqual(args.config, "my.ini")
        self.assertEqual(args.stage, STAGE_1)

    def test_run_stage_1(self) -> None:
        """Проверяет успешное выполнение этапа 1."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            cfg_file, _ = _create_test_files(tmp_dir)
            code = run_stage_1(cfg_file)
            self.assertEqual(code, SUCCESS_EXIT)

    def test_run_stage_1_invalid_config(self) -> None:
        """Проверяет обработку ошибки на этапе 1 при неверном файле."""
        code = run_stage_1("non_existent_file.ini")
        self.assertEqual(code, FAILURE_EXIT)

    def test_run_stage_2(self) -> None:
        """Проверяет успешное выполнение этапа 2."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            cfg_file, _ = _create_test_files(tmp_dir)
            code = run_stage_2(cfg_file)
            self.assertEqual(code, SUCCESS_EXIT)

    def test_run_stage_3(self) -> None:
        """Проверяет успешное выполнение этапа 3."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            cfg_file, _ = _create_test_files(tmp_dir)
            code = run_stage_3(cfg_file)
            self.assertEqual(code, SUCCESS_EXIT)

    def test_run_stage_4(self) -> None:
        """Проверяет успешное выполнение этапа 4."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            cfg_file, _ = _create_test_files(tmp_dir)
            code = run_stage_4(cfg_file)
            self.assertEqual(code, SUCCESS_EXIT)

    def test_run_stage_5(self) -> None:
        """Проверяет успешное выполнение этапа 5 и создание SVG."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            cfg_file, out_svg = _create_test_files(tmp_dir)
            code = run_stage_5(cfg_file)
            self.assertEqual(code, SUCCESS_EXIT)
            self.assertTrue(os.path.exists(out_svg))

    def test_main_dispatch_all(self) -> None:
        """Проверяет вызов всех этапов через функцию main."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            cfg_file, _ = _create_test_files(tmp_dir)
            code = main(["-c", cfg_file, "-s", STAGE_ALL])
            self.assertEqual(code, SUCCESS_EXIT)


if __name__ == "__main__":
    unittest.main()
