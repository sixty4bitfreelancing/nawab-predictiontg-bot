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

# Broadcast
BROADCAST_DELAY_SECONDS: float = 0.05  # Delay between sends to avoid rate limit
BROADCAST_RETRY_AFTER_FALLBACK_SECONDS: int = 5  # Default wait if RetryAfter missing
