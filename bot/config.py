"""
Bot configuration - centralized settings.
All config loaded from environment variables.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

# Debug mode - when True: full traceback; when False: summary only
DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

# Telegram
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
SUPERADMIN_ID: int | None = None
_SA = os.getenv("SUPERADMIN_ID")
if _SA:
    try:
        SUPERADMIN_ID = int(_SA)
    except ValueError:
        pass

# Database (PostgreSQL)
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/telegram_bot"
)

# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE: str = str(ROOT_DIR / "logs" / "bot.log")

# Broadcast (tune via .env if you hit Telegram rate limits)
def _float_env(name: str, default: float) -> float:
    v = os.getenv(name)
    if v is None:
        return default
    try:
        return float(v)
    except ValueError:
        return default


def _int_env(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None:
        return default
    try:
        return int(v)
    except ValueError:
        return default


# 0.04 s = 25 messages per second (under Telegram’s ~30 msg/s limit)
BROADCAST_DELAY_SECONDS: float = _float_env("BROADCAST_DELAY_SECONDS", 0.04)
BROADCAST_RETRY_AFTER_FALLBACK_SECONDS: int = _int_env("BROADCAST_RETRY_AFTER_FALLBACK_SECONDS", 5)

# Maintenance mode - server only (set in .env or environment). When True, non-admin users see maintenance message.
MAINTENANCE: bool = os.getenv("MAINTENANCE", "false").lower() in ("true", "1", "yes")
