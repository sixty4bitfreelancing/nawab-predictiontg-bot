"""
Welcome message service - builds and sends welcome messages.
"""

import json
from telegram import Bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.services.config_service import get_all_config
from bot.utils.exceptions import WelcomeBuilderError
from bot.utils.logger import get_logger

logger = get_logger(__name__)


MAX_WELCOME_BUTTONS = 10


def _parse_welcome_buttons(value: str) -> list[dict]:
    """Parse welcome_buttons JSON. Returns list of {label, url} (max MAX_WELCOME_BUTTONS)."""
    if not value or not value.strip():
        return []
    try:
        data = json.loads(value)
        if not isinstance(data, list):
            return []
        out = []
        for item in data[:MAX_WELCOME_BUTTONS]:
            if isinstance(item, dict) and item.get("label") and item.get("url"):
                out.append({"label": str(item["label"]), "url": str(item["url"])})
        return out
    except (json.JSONDecodeError, TypeError):
        return []


async def build_welcome_keyboard() -> InlineKeyboardMarkup | None:
    """Build welcome keyboard from config (custom buttons only, max 10)."""
    try:
        config = await get_all_config()
        custom = _parse_welcome_buttons(config.get("welcome_buttons") or "[]")
        keyboard = []
        for btn in custom:
            if btn.get("url", "").startswith(("http://", "https://")):
                keyboard.append([InlineKeyboardButton(btn["label"], url=btn["url"])])
        if not keyboard:
            return None
        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        logger.exception("Failed to build welcome keyboard")
        raise WelcomeBuilderError("Failed to build welcome keyboard", original=e) from e


async def send_welcome(bot: Bot, user_id: int) -> None:
    """
    Send welcome message to user.
    Uses welcome_image if set, else text only.
    """
    try:
        config = await get_all_config()
        welcome_text = config.get("welcome_text") or "Welcome! 🎉"
        welcome_image = config.get("welcome_image")
        reply_markup = await build_welcome_keyboard()

        if welcome_image:
            await bot.send_photo(
                chat_id=user_id,
                photo=welcome_image,
                caption=welcome_text,
                reply_markup=reply_markup,
            )
        else:
            await bot.send_message(
                chat_id=user_id,
                text=welcome_text,
                reply_markup=reply_markup,
            )
    except WelcomeBuilderError:
        raise
    except Exception as e:
        logger.exception("Failed to send welcome message to %s", user_id)
        raise WelcomeBuilderError("Failed to send welcome", original=e) from e
