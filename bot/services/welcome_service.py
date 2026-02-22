"""
Welcome message service - builds and sends welcome messages.
"""

from telegram import Bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.services.config_service import get_config_value, get_all_config
from bot.utils.exceptions import WelcomeBuilderError
from bot.utils.logger import get_logger

logger = get_logger(__name__)


async def build_welcome_keyboard() -> InlineKeyboardMarkup | None:
    """Build welcome keyboard from config."""
    try:
        config = await get_all_config()
        keyboard = []

        if config.get("signup_url"):
            keyboard.append([InlineKeyboardButton("🔑 Signup", url=config["signup_url"])])
        if config.get("join_group_url"):
            keyboard.append([InlineKeyboardButton("📢 Join Group", url=config["join_group_url"])])
        keyboard.append([InlineKeyboardButton("💬 Live Chat", callback_data="live_chat")])
        if config.get("download_apk"):
            keyboard.append([InlineKeyboardButton("📥 Download Hack", callback_data="download_hack")])
        if config.get("daily_bonuses_url"):
            keyboard.append(
                [InlineKeyboardButton("🎁 Daily Bonuses", url=config["daily_bonuses_url"])]
            )

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
