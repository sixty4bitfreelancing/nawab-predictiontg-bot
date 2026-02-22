"""Exit live chat command handler."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.state_service import get_user_state, set_user_state


async def exit_live_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /exit command to exit live chat mode."""
    user_id = update.effective_user.id if update.effective_user else 0

    state = await get_user_state(user_id)
    if state == "live_chat":
        await set_user_state(user_id, None)
        await update.message.reply_text(
            "🔙 **Live Chat Ended**\n\nSee you next time! 👋"
        )
    else:
        await update.message.reply_text(
            "ℹ️ **Not in Live Chat**\n\nUse /start to begin."
        )
