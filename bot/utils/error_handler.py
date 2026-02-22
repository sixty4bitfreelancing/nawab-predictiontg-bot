"""
Global Telegram error handler.
Registers with application.add_error_handler() to capture all unhandled exceptions.
Never exposes raw tracebacks to users.
"""

import traceback
from typing import TYPE_CHECKING

from telegram import Update

from bot.config import DEBUG, SUPERADMIN_ID
from bot.utils.exceptions import BotBaseError
from bot.utils.logger import get_logger

if TYPE_CHECKING:
    from telegram.ext import ContextTypes

logger = get_logger(__name__)

# User-facing message - generic, no technical details
USER_ERROR_MESSAGE = (
    "❌ An unexpected error occurred. Please try again later or contact support."
)


def _sanitize_update(update: object) -> dict:
    """Extract safe info from Update for logging. Do not log sensitive data."""
    if not isinstance(update, Update):
        return {"type": type(update).__name__, "raw": str(update)[:200]}
    data = {
        "update_id": update.update_id,
        "user_id": None,
        "chat_id": None,
        "user_username": None,
    }
    if update.effective_user:
        data["user_id"] = update.effective_user.id
        data["user_username"] = (update.effective_user.username or "")[:50]
    if update.effective_chat:
        data["chat_id"] = update.effective_chat.id
    return data


def _get_handler_name(context: "ContextTypes.DEFAULT_TYPE") -> str | None:
    """Get the name of the handler that raised the error if possible."""
    if not context or not hasattr(context, "handler"):
        return None
    handler = getattr(context, "handler", None)
    if handler:
        return getattr(handler, "callback", handler).__qualname__
    return None


async def global_error_handler(
    update: object,
    context: "ContextTypes.DEFAULT_TYPE",
) -> None:
    """
    Global error handler for the Telegram application.
    - Logs all errors with structured info
    - Does NOT expose tracebacks to users
    - Optionally notifies superadmin on CRITICAL
    """
    exc = context.error
    if exc is None:
        return

    exc_type = type(exc).__name__
    exc_msg = str(exc) or "(no message)"
    user_id = None
    chat_id = None
    handler_name = _get_handler_name(context)

    if isinstance(update, Update):
        if update.effective_user:
            user_id = update.effective_user.id
        if update.effective_chat:
            chat_id = update.effective_chat.id

    sanitized = _sanitize_update(update)

    # Determine severity
    if isinstance(exc, BotBaseError):
        log_level = "ERROR"
    else:
        log_level = "CRITICAL"

    # Build log message
    log_parts = [
        f"{exc_type} | {exc_msg}",
        f"user_id={user_id}",
        f"chat_id={chat_id}",
        f"handler={handler_name}",
        f"update={sanitized}",
    ]
    log_msg = " | ".join(str(p) for p in log_parts)

    if DEBUG:
        # Full traceback in debug
        logger.exception(log_msg)
    else:
        if log_level == "CRITICAL":
            logger.critical(log_msg)
            logger.debug("Traceback:\n%s", traceback.format_exc())
        else:
            logger.error(log_msg)
            logger.debug("Traceback:\n%s", traceback.format_exc())

    # User-facing reply - never expose traceback
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(USER_ERROR_MESSAGE)
    except Exception as send_err:
        logger.exception("Failed to send error message to user: %s", send_err)

    # Admin alert for CRITICAL (no traceback via Telegram)
    if log_level == "CRITICAL" and SUPERADMIN_ID:
        try:
            bot = context.bot if context else None
            if bot:
                summary = (
                    f"🚨 CRITICAL Error\n\n"
                    f"Type: {exc_type}\n"
                    f"Message: {exc_msg[:200]}\n"
                    f"User ID: {user_id}\n"
                    f"Chat ID: {chat_id}\n"
                    f"Handler: {handler_name}"
                )
                await bot.send_message(
                    chat_id=SUPERADMIN_ID,
                    text=summary[:4000],
                )
        except Exception as alert_err:
            logger.exception("Failed to send CRITICAL alert to superadmin: %s", alert_err)
