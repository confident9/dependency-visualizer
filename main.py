"""Главная точка входа для запуска визуализатора зависимостей."""

import sys
from src.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
