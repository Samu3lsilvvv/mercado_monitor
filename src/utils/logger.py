"""
Logger estruturado com suporte a Rich (terminal colorido) e arquivo de log.
"""

import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

from rich.console import Console
from rich.logging import RichHandler

from src.utils.config import LOG_PATH, LOGS_DIR

# Garante que o console usa UTF-8 no Windows (evita UnicodeEncodeError com emojis)
_console = Console(stderr=False, force_terminal=True, highlight=False)


def get_logger(name: str = "mercado_monitor") -> logging.Logger:
    """
    Retorna um logger configurado com:
      - RichHandler: saída colorida e formatada no terminal
      - FileHandler: arquivo de log com rotação diária em logs/app.log
    """
    os.makedirs(LOGS_DIR, exist_ok=True)

    logger = logging.getLogger(name)

    # Evita adicionar handlers duplicados em chamadas repetidas
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # ── Terminal (Rich) ──────────────────────────────────────
    rich_handler = RichHandler(
        console=_console,
        rich_tracebacks=True,
        markup=True,
        show_time=True,
        show_path=False,
    )
    rich_handler.setLevel(logging.INFO)
    rich_format = logging.Formatter("%(message)s")
    rich_handler.setFormatter(rich_format)

    # ── Arquivo (rotação diária, mantém 30 dias) ─────────────
    file_handler = TimedRotatingFileHandler(
        LOG_PATH,
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_format)

    logger.addHandler(rich_handler)
    logger.addHandler(file_handler)

    return logger
