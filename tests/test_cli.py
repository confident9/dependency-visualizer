"""Модульные тесты для командного интерфейса (CLI)."""

import os
import tempfile
import unittest
from unittest.mock import patch
from src.cli import (
    FAILURE_EXIT,
    STAGE_1,
    STAGE_2,
    STAGE_3,
    STAGE_4,
    STAGE_5,
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


class TestCli(unittest.TestCase):
    """Набор тестов для проверки функций CLI."""

    def setUp(self) -> None:
        """Подготавливает временную конфигурацию для тестирования."""
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.repo_file = os.path.join(self.tmp_dir.name, "repo.json")
        with open(self.repo_file, "w", encoding="utf-8") as f:
            f.write('{"A": ["B"], "B": []}')
        self.out_svg = os.path.join(self.tmp_dir.name, "graph.svg")
        self.config_file = os.path.join(self.tmp_dir.name, "config.ini")
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.write(
                "[visualizer]\n"
                "package_name = A\n"
                f"repo_url = {self.repo_file}\n"
                "test_mode = true\n"
                "package_version = 1.0.0\n"
                f"output_file = {self.out_svg}\n"
                "filter_substring = \n"
            )

    def tearDown(self) -> None:
        """Очищает временные файлы."""
        self.tmp_dir.cleanup()

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
        code = run_stage_1(self.config_file)
        self.assertEqual(code, SUCCESS_EXIT)

    def test_run_stage_1_invalid_config(self) -> None:
        """Проверяет обработку ошибки на этапе 1 при неверном файле."""
        code = run_stage_1("non_existent_file.ini")
        self.assertEqual(code, FAILURE_EXIT)

    def test_run_stage_2(self) -> None:
        """Проверяет успешное выполнение этапа 2."""
        code = run_stage_2(self.config_file)
        self.assertEqual(code, SUCCESS_EXIT)

    def test_run_stage_3(self) -> None:
        """Проверяет успешное выполнение этапа 3."""
        code = run_stage_3(self.config_file)
        self.assertEqual(code, SUCCESS_EXIT)

    def test_run_stage_4(self) -> None:
        """Проверяет успешное выполнение этапа 4."""
        code = run_stage_4(self.config_file)
        self.assertEqual(code, SUCCESS_EXIT)

    def test_run_stage_5(self) -> None:
        """Проверяет успешное выполнение этапа 5 и создание SVG."""
        code = run_stage_5(self.config_file)
        self.assertEqual(code, SUCCESS_EXIT)
        self.assertTrue(os.path.exists(self.out_svg))

    def test_main_dispatch_all(self) -> None:
        """Проверяет вызов всех этапов через функцию main."""
        code = main(["-c", self.config_file, "-s", STAGE_ALL])
        self.assertEqual(code, SUCCESS_EXIT)


if __name__ == "__main__":
    unittest.main()
