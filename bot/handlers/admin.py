"""Admin command and panel handlers."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.callbacks import show_admin_panel_from_query
from bot.keyboards.admin import admin_panel_keyboard
from bot.services.user_service import is_admin
from bot.utils.logger import get_logger

logger = get_logger(__name__)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /admin command."""
    user = update.effective_user
    if not user:
        return

    if not await is_admin(user.id):
        await update.message.reply_text("❌ Access denied. You are not authorized as an admin.")
        return

    await update.message.reply_text(
        "🔧 **Advanced Admin Panel**\n\n"
        "Welcome to the admin panel. Use the buttons below to configure the bot:",
        reply_markup=admin_panel_keyboard(),
    )


async def show_chat_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /id command - show chat ID for channels/groups."""
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return

    if chat.type not in ("channel", "supergroup", "group"):
        await update.message.reply_text(
            "❌ **Error**\n\n"
            "This command only works in channels and groups."
        )
        return

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status not in ("creator", "administrator"):
            await update.message.reply_text("❌ You need to be an admin in this chat.")
            return
    except Exception as e:
        logger.exception("Failed to verify admin status: %s", e)
        await update.message.reply_text("❌ Could not verify your admin status.")
        return

    chat_type = "Channel" if chat.type == "channel" else "Supergroup" if chat.type == "supergroup" else "Group"
    username_info = f"\n**Username:** @{chat.username}" if chat.username else "\n**Username:** None (Private)"

    await update.message.reply_text(
        f"📋 **Chat Information**\n\n"
        f"**Type:** {chat_type}\n**Title:** {chat.title}\n**ID:** `{chat.id}`\n"
        f"{username_info}",
        parse_mode="Markdown",
    )
