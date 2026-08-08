"""Logging helpers (CONVENTION.md § 8).

Every module gets its own logger via `get_logger(__name__)`; no `print()` in
library code. CLI scripts may use `configure_cli_logging()`.
"""

from __future__ import annotations

import logging
from typing import Any

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"


def get_logger(name: str) -> logging.Logger:
    """Return the module logger for `name` with the project format attached."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    return logger


def configure_cli_logging(level: int = logging.INFO, **kwargs: Any) -> None:
    """Configure the root logger for CLI entry points (scripts/)."""
    logging.basicConfig(level=level, format=LOG_FORMAT, **kwargs)
