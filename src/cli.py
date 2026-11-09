"""Модуль командной строки (CLI) визуализатора зависимостей."""

import argparse
import os
import sys
from typing import List, Optional
from src.collector import (
    create_dependency_fetcher,
    format_direct_dependencies,
    get_direct_dependencies,
)
from src.config import AppConfig, ConfigError, format_config, load_config
from src.graph import DependencyGraph, build_dependency_graph
from src.order import compute_loading_order, format_loading_order
from src.visualizer import export_graph, generate_dot

STAGE_1 = "1"
STAGE_2 = "2"
STAGE_3 = "3"
STAGE_4 = "4"
STAGE_5 = "5"
STAGE_ALL = "all"
DEFAULT_CONFIG = "config.ini"
EMPTY_LENGTH = 0
SUCCESS_EXIT = 0
FAILURE_EXIT = 1


def run_stage_1(config_path: str) -> int:
    """Выполняет этап 1: парсинг конфигурации и вывод параметров.

    Args:
        config_path: Путь к файлу конфигурации INI.

    Returns:
        Код возврата (0 - успешно, 1 - ошибка).
    """
    try:
        cfg = load_config(config_path)
        print("=== Этап 1: Чтение конфигурации ===")
        print(format_config(cfg))
        return SUCCESS_EXIT
    except ConfigError as err:
        print(f"Ошибка конфигурации: {err}", file=sys.stderr)
        return FAILURE_EXIT


def run_stage_2(config_path: str) -> int:
    """Выполняет этап 2: извлечение прямых зависимостей пакета.

    Args:
        config_path: Путь к файлу конфигурации INI.

    Returns:
        Код возврата (0 - успешно, 1 - ошибка).
    """
    try:
        cfg = load_config(config_path)
        print("=== Этап 2: Сбор прямых зависимостей ===")
        deps = get_direct_dependencies(
            package_name=cfg.package_name,
            repo_url=cfg.repo_url,
            test_mode=cfg.test_mode,
            package_version=cfg.package_version,
        )
        print(format_direct_dependencies(
            cfg.package_name, cfg.package_version, deps
        ))
        return SUCCESS_EXIT
    except Exception as err:
        print(f"Ошибка сбора зависимостей: {err}", file=sys.stderr)
        return FAILURE_EXIT


def _build_graph(cfg: AppConfig) -> DependencyGraph:
    """Создает граф зависимостей по данным конфигурации.

    Args:
        cfg: Объект конфигурации приложения.

    Returns:
        Построенный граф зависимостей.
    """
    fetcher = create_dependency_fetcher(
        repo_url=cfg.repo_url,
        test_mode=cfg.test_mode,
        root_version=cfg.package_version,
    )
    return build_dependency_graph(
        root_package=cfg.package_name,
        fetcher=fetcher,
        filter_substring=cfg.filter_substring,
    )


def run_stage_3(config_path: str) -> int:
    """Выполняет этап 3: построение графа зависимостей с помощью DFS.

    Args:
        config_path: Путь к файлу конфигурации INI.

    Returns:
        Код возврата (0 - успешно, 1 - ошибка).
    """
    try:
        cfg = load_config(config_path)
        print("=== Этап 3: Построение графа зависимостей (DFS) ===")
        graph = _build_graph(cfg)
        print(f"Корневой пакет: {graph.root}")
        print(f"Всего узлов в графе: {len(graph.nodes)}")
        print(f"Узлы: {', '.join(sorted(graph.nodes))}")
        print("Ребра графа:")
        for src in sorted(graph.adjacency.keys()):
            for dst in sorted(graph.adjacency[src]):
                print(f"  {src} -> {dst}")
        if graph.cycles:
            print("Обнаруженные циклы:")
            for c_src, c_dst in graph.cycles:
                print(f"  [цикл] {c_src} -> {c_dst}")
        return SUCCESS_EXIT
    except Exception as err:
        print(f"Ошибка построения графа: {err}", file=sys.stderr)
        return FAILURE_EXIT


def run_stage_4(config_path: str) -> int:
    """Выполняет этап 4: вычисление порядка загрузки зависимостей.

    Args:
        config_path: Путь к файлу конфигурации INI.

    Returns:
        Код возврата (0 - успешно, 1 - ошибка).
    """
    try:
        cfg = load_config(config_path)
        print("=== Этап 4: Порядок загрузки зависимостей ===")
        graph = _build_graph(cfg)
        order = compute_loading_order(graph)
        print(format_loading_order(order))
        return SUCCESS_EXIT
    except Exception as err:
        print(f"Ошибка вычисления порядка: {err}", file=sys.stderr)
        return FAILURE_EXIT


def run_stage_5(config_path: str) -> int:
    """Выполняет этап 5: генерация Graphviz DOT и экспорт SVG.

    Args:
        config_path: Путь к файлу конфигурации INI.

    Returns:
        Код возврата (0 - успешно, 1 - ошибка).
    """
    try:
        cfg = load_config(config_path)
        print("=== Этап 5: Визуализация графа (Graphviz / SVG) ===")
        graph = _build_graph(cfg)
        dot_path = os.path.splitext(cfg.output_file)[0] + ".dot"
        msg = export_graph(graph, cfg.output_file, dot_path)
        print(msg)
        print(f"DOT файл сохранен: {dot_path}")
        print("\nСодержимое DOT:")
        print(generate_dot(graph))
        return SUCCESS_EXIT
    except Exception as err:
        print(f"Ошибка визуализации: {err}", file=sys.stderr)
        return FAILURE_EXIT


def run_all_stages(config_path: str) -> int:
    """Выполняет последовательно все этапы 1-5.

    Args:
        config_path: Путь к файлу конфигурации INI.

    Returns:
        Код возврата.
    """
    stages = [
        run_stage_1,
        run_stage_2,
        run_stage_3,
        run_stage_4,
        run_stage_5,
    ]
    for stage_fn in stages:
        code = stage_fn(config_path)
        if code != SUCCESS_EXIT:
            return code
        print()
    return SUCCESS_EXIT


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Разбирает аргументы командной строки CLI.

    Args:
        argv: Список аргументов или None для sys.argv.

    Returns:
        Объект Namespace с аргументами.
    """
    parser = argparse.ArgumentParser(
        description="Инструмент визуализации графа зависимостей пакетов Rust."
    )
    parser.add_argument(
        "--config",
        "-c",
        default=DEFAULT_CONFIG,
        help="Путь к INI-файлу конфигурации (по умолчанию config.ini)",
    )
    parser.add_argument(
        "--stage",
        "-s",
        choices=[
            STAGE_1,
            STAGE_2,
            STAGE_3,
            STAGE_4,
            STAGE_5,
            STAGE_ALL,
        ],
        default=STAGE_ALL,
        help="Номер этапа (1..5) или all для запуска всех этапов",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    """Точка входа CLI приложения.

    Args:
        argv: Список аргументов командной строки.

    Returns:
        Код завершения процесса.
    """
    args = parse_args(argv)
    dispatch = {
        STAGE_1: run_stage_1,
        STAGE_2: run_stage_2,
        STAGE_3: run_stage_3,
        STAGE_4: run_stage_4,
        STAGE_5: run_stage_5,
        STAGE_ALL: run_all_stages,
    }
    handler = dispatch.get(args.stage, run_all_stages)
    return handler(args.config)
