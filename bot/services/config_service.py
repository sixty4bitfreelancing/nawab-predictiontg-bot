"""
Bot configuration service - reads/writes config from PostgreSQL.
"""

from bot.database import fetch_one, fetch_all, execute_query
from bot.utils.exceptions import DatabaseError
from bot.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_CONFIG = {
    "welcome_text": "Welcome to our channel! 🎉",
    "welcome_image": "",
    "signup_url": "",
    "join_group_url": "",
    "download_apk": "",
    "daily_bonuses_url": "",
    "admin_group_id": "",
    "live_chat_enabled": "true",
    "auto_accept_enabled": "true",  # When false, join requests are not auto-approved (other services stay on)
}


async def get_config_value(key: str) -> str:
    """Get a config value by key."""
    try:
        row = await fetch_one(
            "SELECT value FROM bot_config WHERE key = $1",
            key,
        )
        if row and row["value"] is not None:
            return row["value"]
        return DEFAULT_CONFIG.get(key, "")
    except DatabaseError:
        raise
    except Exception as e:
        logger.exception("Failed to get config value %s", key)
        raise DatabaseError("Failed to get config", original=e) from e


async def set_config_value(key: str, value: str) -> None:
    """Set a config value."""
    try:
        await execute_query(
            """
            INSERT INTO bot_config (key, value, updated_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (key) DO UPDATE SET value = $2, updated_at = NOW()
            """,
            key,
            value,
        )
    except DatabaseError:
        raise
    except Exception as e:
        logger.exception("Failed to set config value %s", key)
        raise DatabaseError("Failed to set config", original=e) from e


async def get_all_config() -> dict:
    """Get all config as dict."""
    try:
        rows = await fetch_all("SELECT key, value FROM bot_config")
        result = dict(DEFAULT_CONFIG)
        for row in rows:
            result[row["key"]] = row["value"] or ""
        return result
    except DatabaseError:
        raise
    except Exception as e:
        logger.exception("Failed to get all config")
        raise DatabaseError("Failed to get config", original=e) from e
