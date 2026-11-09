"""Модуль извлечения прямых зависимостей для пакетов Rust (Cargo)."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Dict, List, Optional

DEFAULT_TIMEOUT = 10
HTTP_OK = 200
HTTP_NOT_FOUND = 404
USER_AGENT = "DependencyVisualizer/1.0 (student@mirea.ru)"
CRATES_IO_DEFAULT = "https://crates.io/api/v1/crates"
KIND_NORMAL = "normal"
EMPTY_LENGTH = 0


class CollectorError(Exception):
    """Исключение при ошибках получения данных о зависимостях."""


class DependencyInfo:
    """Информация об отдельной зависимости пакета."""

    def __init__(
        self,
        name: str,
        req: str = "*",
        optional: bool = False,
        kind: str = KIND_NORMAL,
    ) -> None:
        """Инициализирует описание зависимости.

        Args:
            name: Имя зависимого пакета.
            req: Версионное требование (например, ^1.0).
            optional: Является ли зависимость опциональной.
            kind: Тип зависимости (normal, dev, build).
        """
        self.name = name
        self.req = req
        self.optional = optional
        self.kind = kind

    def __eq__(self, other: object) -> bool:
        """Сравнивает две зависимости на равенство."""
        if not isinstance(other, DependencyInfo):
            return False
        return (
            self.name == other.name
            and self.req == other.req
            and self.optional == other.optional
            and self.kind == other.kind
        )

    def __repr__(self) -> str:
        """Возвращает строковое представление зависимости."""
        return f"DependencyInfo(name='{self.name}', req='{self.req}')"


def _read_local_test_repo(path: str) -> Dict[str, List[str]]:
    """Считывает граф зависимостей из локального тестового файла.

    Args:
        path: Путь к файлу тестового репозитория.

    Returns:
        Словарь смежности {пакет: [зависимости]}.

    Raises:
        CollectorError: Если файл поврежден или не найден.
    """
    if not os.path.exists(path):
        raise CollectorError(
            f"Файл тестового репозитория не найден: {path}"
        )
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
            if not isinstance(data, dict):
                raise CollectorError(
                    "Тестовый репозиторий должен содержать JSON-объект."
                )
            result: Dict[str, List[str]] = {}
            for k, val in data.items():
                if isinstance(val, list):
                    result[str(k)] = [str(x) for x in val]
                else:
                    result[str(k)] = []
            return result
    except (json.JSONDecodeError, OSError) as err:
        raise CollectorError(
            f"Не удалось прочитать тестовый репозиторий: {err}"
        )


def _handle_http_error(
    err: urllib.error.HTTPError, pkg: str, ver: str
) -> None:
    """Обрабатывает ошибки протокола HTTP при запросе к Crates.io.

    Args:
        err: Исключение HTTPError.
        pkg: Имя пакета.
        ver: Версия пакета.
    """
    if err.code == HTTP_NOT_FOUND:
        raise CollectorError(
            f"Пакет '{pkg}' версии '{ver}' не найден в репозитории."
        )
    raise CollectorError(
        f"Ошибка HTTP при обращении к Crates.io: {err.code} {err.reason}"
    )


def _fetch_crates_io_json(
    base_url: str,
    package: str,
    version: str,
) -> Dict[str, object]:
    """Запрашивает зависимости пакета с сервера Crates.io.

    Args:
        base_url: Базовый URL API Crates.io.
        package: Имя пакета.
        version: Версия пакета.

    Returns:
        Словарь с ответом сервера.

    Raises:
        CollectorError: При сетевых ошибках или отсутствии пакета.
    """
    clean_url = base_url.rstrip("/")
    target_url = f"{clean_url}/{package}/{version}/dependencies"
    req = urllib.request.Request(
        target_url,
        headers={"User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as response:
            body = response.read().decode("utf-8")
            parsed = json.loads(body)
            if not isinstance(parsed, dict):
                raise CollectorError("Некорректный формат ответа Crates.io.")
            return parsed
    except urllib.error.HTTPError as err:
        _handle_http_error(err, package, version)
        return {}
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as err:
        raise CollectorError(
            f"Не удалось получить данные с {target_url}: {err}"
        )


def _parse_dependencies_payload(
    payload: Dict[str, object],
    include_optional: bool = False,
) -> List[DependencyInfo]:
    """Извлекает список зависимостей из ответа Crates.io.

    Args:
        payload: Распарсенный ответ API Crates.io.
        include_optional: Включать ли опциональные зависимости.

    Returns:
        Список объектов DependencyInfo.
    """
    raw_deps = payload.get("dependencies", [])
    if not isinstance(raw_deps, list):
        return []
    dependencies: List[DependencyInfo] = []
    for item in raw_deps:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind", KIND_NORMAL))
        if kind != KIND_NORMAL:
            continue
        opt = bool(item.get("optional", False))
        if opt and not include_optional:
            continue
        crate_id = str(item.get("crate_id", "")).strip()
        req = str(item.get("req", "*")).strip()
        if len(crate_id) > EMPTY_LENGTH:
            dependencies.append(
                DependencyInfo(
                    name=crate_id,
                    req=req,
                    optional=opt,
                    kind=kind,
                )
            )
    return dependencies


def _get_test_dependencies(
    package_name: str,
    repo_url: str,
) -> List[DependencyInfo]:
    """Извлекает прямые зависимости из файла тестового репозитория.

    Args:
        package_name: Имя пакета.
        repo_url: Путь к файлу репозитория.

    Returns:
        Список объектов DependencyInfo.
    """
    data = _read_local_test_repo(repo_url)
    if package_name not in data:
        raise CollectorError(
            f"Пакет '{package_name}' отсутствует в тестовом репозитории."
        )
    return [DependencyInfo(name=d) for d in sorted(data[package_name])]


def get_direct_dependencies(
    package_name: str,
    repo_url: str,
    test_mode: bool,
    package_version: Optional[str] = None,
) -> List[DependencyInfo]:
    """Получает список прямых зависимостей пакета.

    Args:
        package_name: Имя анализируемого пакета.
        repo_url: URL или локальный путь к репозиторию.
        test_mode: Режим тестового репозитория.
        package_version: Версия пакета (для реального репозитория).

    Returns:
        Список прямых зависимостей.

    Raises:
        CollectorError: При возникновении ошибок сбора данных.
    """
    if test_mode:
        return _get_test_dependencies(package_name, repo_url)

    version = package_version or ""
    if len(version.strip()) == EMPTY_LENGTH:
        raise CollectorError(
            "Не указана версия пакета для реального репозитория."
        )

    if os.path.isfile(repo_url):
        data = _read_local_test_repo(repo_url)
        return [
            DependencyInfo(name=d)
            for d in sorted(data.get(package_name, []))
        ]

    payload = _fetch_crates_io_json(repo_url, package_name, version)
    return _parse_dependencies_payload(payload)


def format_direct_dependencies(
    package_name: str,
    version: str,
    dependencies: List[DependencyInfo],
) -> str:
    """Форматирует список прямых зависимостей для вывода на экран.

    Args:
        package_name: Имя пакета.
        version: Версия пакета.
        dependencies: Список прямых зависимостей.

    Returns:
        Текстовое представление прямых зависимостей.
    """
    title = (
        f"Прямые зависимости пакета '{package_name}' (версия {version}):"
    )
    if not dependencies:
        return f"{title}\n  (зависимостей нет)"
    lines = [title]
    for dep in dependencies:
        lines.append(f"  - {dep.name} ({dep.req})")
    return "\n".join(lines)


def create_dependency_fetcher(
    repo_url: str,
    test_mode: bool,
    root_version: str = "",
) -> Callable[[str], List[str]]:
    """Создает функцию получения зависимостей для алгоритма DFS.

    Args:
        repo_url: URL или путь к репозиторию.
        test_mode: Флаг тестового режима.
        root_version: Версия корневого пакета.

    Returns:
        Функция, принимающая имя пакета и возвращающая имена зависимостей.
    """
    def fetcher(pkg_name: str) -> List[str]:
        """Возвращает список имен прямых зависимостей пакета."""
        try:
            deps = get_direct_dependencies(
                package_name=pkg_name,
                repo_url=repo_url,
                test_mode=test_mode,
                package_version=root_version,
            )
            return [dep.name for dep in deps]
        except CollectorError:
            return []

    return fetcher

