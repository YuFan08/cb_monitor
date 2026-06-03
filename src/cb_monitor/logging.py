"""Loguru configuration."""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger


def configure_logging(level: str, log_file: Path | None = None) -> None:
    """Configure concise terminal logging and optional file logs."""
    logger.remove()
    logger.add(
        sys.stderr,
        colorize=True,
        level=level.upper(),
        format=(
            "<green>{time:HH:mm:ss}</green> | <level>{level: ^7}</level> | {message}"
        ),
    )
    if log_file is not None:
        logger.add(
            log_file,
            encoding="utf-8",
            level="DEBUG",
            rotation="5 MB",
            retention=5,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | "
                "{name}:{function}:{line} | {message}"
            ),
        )
