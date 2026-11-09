"""Модуль загрузки и валидации конфигурации INI для визуализатора."""

import configparser
import os
from typing import Dict, Any

DEFAULT_SECTION = "settings"
SVG_EXTENSION = ".svg"
EMPTY_LENGTH = 0
HTTP_PREFIX = "http://"
HTTPS_PREFIX = "https://"


class ConfigError(Exception):
    """Исключение при ошибках загрузки и валидации конфигурации."""


class AppConfig:
    """Класс настроек приложения, полученных из INI файла."""

    def __init__(
        self,
        package_name: str,
        repo_url: str,
        test_mode: bool,
        package_version: str,
        output_file: str,
        filter_substring: str,
    ) -> None:
        """Инициализирует объект конфигурации.

        Args:
            package_name: Имя анализируемого пакета.
            repo_url: URL или путь к файлу тестового репозитория.
            test_mode: Режим работы с тестовым репозиторием.
            package_version: Версия пакета.
            output_file: Имя сгенерированного SVG файла.
            filter_substring: Подстрока для фильтрации пакетов.
        """
        self.package_name = package_name
        self.repo_url = repo_url
        self.test_mode = test_mode
        self.package_version = package_version
        self.output_file = output_file
        self.filter_substring = filter_substring

    def to_dict(self) -> Dict[str, Any]:
        """Возвращает параметры конфигурации в виде словаря."""
        return {
            "package_name": self.package_name,
            "repo_url": self.repo_url,
            "test_mode": self.test_mode,
            "package_version": self.package_version,
            "output_file": self.output_file,
            "filter_substring": self.filter_substring,
        }

    def format_key_value(self) -> str:
        """Форматирует параметры в виде ключ-значение.

        Returns:
            Текстовое представление всех параметров.
        """
        lines = [
            f"package_name = {self.package_name}",
            f"repo_url = {self.repo_url}",
            f"test_mode = {str(self.test_mode).lower()}",
            f"package_version = {self.package_version}",
            f"output_file = {self.output_file}",
            f"filter_substring = {self.filter_substring}",
        ]
        return "\n".join(lines)


def format_config(config: AppConfig) -> str:
    """Форматирует параметры конфигурации в виде ключ: значение.

    Args:
        config: Объект конфигурации.

    Returns:
        Строка с отформатированными параметрами.
    """
    return config.format_key_value()



def _validate_package_name(name: str) -> None:
    """Проверяет корректность имени пакета."""
    if not name or len(name.strip()) == EMPTY_LENGTH:
        raise ConfigError(
            "Параметр 'package_name' не задан или является пустым."
        )


def _validate_output_file(filename: str) -> None:
    """Проверяет имя выходного файла."""
    if not filename or len(filename.strip()) == EMPTY_LENGTH:
        raise ConfigError(
            "Параметр 'output_file' не задан или является пустым."
        )
    if not filename.lower().endswith(SVG_EXTENSION):
        raise ConfigError(
            f"Параметр 'output_file' должен иметь расширение {SVG_EXTENSION}."
        )


def _validate_repo_url(url: str, test_mode: bool) -> None:
    """Проверяет корректность URL репозитория или пути к файлу."""
    if not url or len(url.strip()) == EMPTY_LENGTH:
        raise ConfigError("Параметр 'repo_url' не задан или пуст.")
    stripped = url.strip()
    if test_mode:
        if not os.path.exists(stripped):
            raise ConfigError(
                f"Файл тестового репозитория не найден: {stripped}"
            )
    else:
        is_http = stripped.startswith(HTTP_PREFIX)
        is_https = stripped.startswith(HTTPS_PREFIX)
        if not (is_http or is_https or os.path.exists(stripped)):
            raise ConfigError(
                "Параметр 'repo_url' должен быть валидным HTTP(S) URL "
                "или путем к существующему файлу."
            )


def _validate_version(version: str, test_mode: bool) -> None:
    """Проверяет корректность версии пакета."""
    if not test_mode:
        if not version or len(version.strip()) == EMPTY_LENGTH:
            raise ConfigError(
                "Параметр 'package_version' обязателен для реального "
                "репозитория."
            )


def _parse_bool(val: str) -> bool:
    """Преобразует строковое значение в булево.

    Args:
        val: Исходная строка.

    Returns:
        Булево значение.

    Raises:
        ConfigError: Если строка не является булевым значением.
    """
    cleaned = val.strip().lower()
    true_values = ("true", "yes", "1", "on")
    false_values = ("false", "no", "0", "off")
    if cleaned in true_values:
        return True
    if cleaned in false_values:
        return False
    raise ConfigError(
        f"Некорректное булево значение для 'test_mode': '{val}'. "
        "Ожидается true или false."
    )


def _read_ini_section(path: str) -> configparser.SectionProxy:
    """Считывает секцию конфигурации из INI файла.

    Args:
        path: Путь к INI-файлу.

    Returns:
        Объект SectionProxy с параметрами.
    """
    if not os.path.exists(path):
        raise ConfigError(f"Конфигурационный файл не найден: {path}")
    parser = configparser.ConfigParser()
    try:
        parser.read(path, encoding="utf-8")
    except configparser.Error as err:
        raise ConfigError(f"Ошибка синтаксиса INI файла: {err}")
    section = DEFAULT_SECTION
    if not parser.has_section(section):
        if parser.sections():
            section = parser.sections()[0]
        else:
            raise ConfigError(
                f"В INI файле отсутствует секция [{DEFAULT_SECTION}]."
            )
    return parser[section]


def load_config(path: str) -> AppConfig:
    """Считывает и валидирует INI конфигурационный файл.

    Args:
        path: Путь к INI-файлу.

    Returns:
        Объект AppConfig.

    Raises:
        ConfigError: При отсутствии файла или ошибках в параметрах.
    """
    sec = _read_ini_section(path)
    pkg_name = sec.get("package_name", "").strip()
    repo_url = sec.get("repo_url", "").strip()
    test_mode = _parse_bool(sec.get("test_mode", "false").strip())
    version = sec.get("package_version", "").strip()
    output_file = sec.get("output_file", "graph.svg").strip()
    filter_sub = sec.get("filter_substring", "").strip()

    _validate_package_name(pkg_name)
    _validate_output_file(output_file)
    _validate_repo_url(repo_url, test_mode)
    _validate_version(version, test_mode)

    return AppConfig(
        package_name=pkg_name,
        repo_url=repo_url,
        test_mode=test_mode,
        package_version=version,
        output_file=output_file,
        filter_substring=filter_sub,
    )
