#!/usr/bin/env bash
set -e

# Определение директории проекта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MODE="${1:-all}"

case "$MODE" in
  test)
    echo "=== Запуск модульных тестов ==="
    python3 -m unittest discover tests -v
    ;;
  demo)
    echo "=== Демонстрация работы визуализатора (3 реальных пакета + тесты) ==="
    echo ""
    echo ">>> 1. Линейный тестовый граф (A -> B -> C -> D):"
    python3 main.py --config configs/test_linear.ini
    echo ""
    echo ">>> 2. Тестовый граф с циклом (C -> A):"
    python3 main.py --config configs/test_cycle.ini
    echo ""
    echo ">>> 3. Пакет rand (0.8.5):"
    python3 main.py --config configs/sample_rand.ini
    echo ""
    echo ">>> 4. Пакет regex (1.10.2):"
    python3 main.py --config configs/sample_regex.ini
    echo ""
    echo ">>> 5. Пакет log (0.4.20):"
    python3 main.py --config configs/sample_log.ini
    ;;
  all)
    echo "=== 1. Модульное тестирование ==="
    python3 -m unittest discover tests -v
    echo ""
    echo "=== 2. Демонстрация всех этапов ==="
    python3 main.py --config configs/sample_rand.ini
    ;;
  stage1|1)
    python3 main.py --config config.ini --stage 1
    ;;
  stage2|2)
    python3 main.py --config config.ini --stage 2
    ;;
  stage3|3)
    python3 main.py --config config.ini --stage 3
    ;;
  stage4|4)
    python3 main.py --config config.ini --stage 4
    ;;
  stage5|5)
    python3 main.py --config config.ini --stage 5
    ;;
  *)
    echo "Использование: $0 [test|demo|all|1|2|3|4|5]"
    exit 1
    ;;
esac
