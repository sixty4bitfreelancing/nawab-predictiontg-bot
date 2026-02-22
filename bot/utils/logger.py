"""
Structured logging for the bot.
Uses Python logging module with configurable format and levels.
All exceptions must use logger.exception() for full traceback capture.
"""

import logging
import sys
from pathlib import Path

from bot.config import LOG_LEVEL, LOG_FILE, DEBUG

# Ensure logs directory exists
Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

# Log format: timestamp | level | module | message
LOG_FORMAT = (
    "[%(asctime)s] %(levelname)s | %(name)s | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Create formatter
_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

# File handler
_file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
_file_handler.setFormatter(_formatter)

# Console handler
_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setFormatter(_formatter)

# Root logger
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[_file_handler, _console_handler],
    force=True,
)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a module."""
    logger = logging.getLogger(name)
    return logger
