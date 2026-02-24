"""
Maintenance mode - server-only (env MAINTENANCE=true).
When enabled, non-admin users see a maintenance message; admins can use the bot normally.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import MAINTENANCE
from bot.services.user_service import is_admin

MAINTENANCE_MESSAGE = (
    "🔧 **Bot is under maintenance**\n\n"
    "Please try again later. We'll be back soon!"
)


async def check_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    If maintenance mode is on and user is not admin, send maintenance message and return True.
    Caller should return immediately when True.
    Returns False if bot should process normally.
    """
    if not MAINTENANCE:
        return False
    user = update.effective_user
    if not user:
        return False
    if await is_admin(user.id):
        return False
    # Non-admin during maintenance
    try:
        if update.callback_query:
            await update.callback_query.answer(MAINTENANCE_MESSAGE.strip(), show_alert=True)
        elif update.message:
            await update.message.reply_text(MAINTENANCE_MESSAGE)
    except Exception:
        pass
    return True
