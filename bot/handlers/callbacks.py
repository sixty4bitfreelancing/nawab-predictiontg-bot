"""Callback query handlers for inline buttons."""

import re
from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboards.admin import admin_panel_keyboard, back_to_admin_keyboard
from bot.keyboards.user import live_chat_exit_keyboard, live_chat_start_keyboard
from bot.services.config_service import get_config_value, get_all_config, set_config_value
from bot.services.user_service import is_admin, get_all_admin_ids, get_user_count, get_recent_users
from bot.services.state_service import get_user_state, set_user_state, get_admin_state, set_admin_state
from bot.services.log_service import get_recent_logs
from bot.services.broadcast_service import broadcast_to_users, BroadcastResult
from bot.services.welcome_service import send_welcome
from bot.utils.logger import get_logger

logger = get_logger(__name__)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries from inline buttons."""
    query = update.callback_query
    if not query:
        return
    await query.answer()

    data = query.data
    user_id = query.from_user.id if query.from_user else 0

    # User buttons (work for everyone)
    if data == "signup":
        await _handle_signup(query)
        return
    if data == "join_group":
        await _handle_join_group(query)
        return
    if data == "live_chat":
        await _start_live_chat(query, context)
        return
    if data == "download_hack":
        await _handle_download_hack(query, context)
        return
    if data == "daily_bonuses":
        await _handle_daily_bonuses(query)
        return
    if data == "exit_live_chat":
        await _exit_live_chat_button(query, context)
        return

    # Admin-only
    if not await is_admin(user_id):
        await query.edit_message_text("❌ Access denied. You are not authorized as an admin.")
        return

    if data == "set_welcome_text":
        await set_admin_state(user_id, "waiting_welcome_text")
        await query.edit_message_text(
            "📝 **Set Welcome Text**\n\nSend the new welcome message text."
        )
    elif data == "set_welcome_image":
        await set_admin_state(user_id, "waiting_welcome_image")
        await query.edit_message_text("🖼️ **Set Welcome Image**\n\nSend the image.")
    elif data == "set_signup_url":
        await set_admin_state(user_id, "waiting_signup_url")
        await query.edit_message_text("🔗 **Set Signup URL**\n\nSend the URL (https://...).")
    elif data == "set_join_group_url":
        await set_admin_state(user_id, "waiting_join_group_url")
        await query.edit_message_text(
            "👥 **Set Join Group URL**\n\nSend the t.me group/channel link."
        )
    elif data == "set_download_apk":
        await set_admin_state(user_id, "waiting_download_apk")
        await query.edit_message_text("📱 **Set Download APK**\n\nSend the APK file.")
    elif data == "set_daily_bonuses":
        await set_admin_state(user_id, "waiting_daily_bonuses")
        await query.edit_message_text("🎁 **Set Daily Bonuses URL**\n\nSend the URL.")
    elif data == "set_admin_group":
        await set_admin_state(user_id, "waiting_admin_group")
        await query.edit_message_text(
            "📱 **Set Admin Group**\n\nSend the group ID. Use /id in the group to get it."
        )
    elif data == "bot_config":
        await _show_bot_config(query)
    elif data == "send_broadcast":
        await set_admin_state(user_id, "waiting_broadcast")
        await query.edit_message_text(
            "📡 **Send Message to All Users**\n\n"
            "Send the message (text, photo, video, etc.) to broadcast."
        )
    elif data == "view_users":
        await _show_user_stats(query)
    elif data == "view_logs":
        await _show_logs(query)
    elif data == "stop_bot":
        await query.edit_message_text(
            "🛑 **Stop Bot**\n\nRestart the process to stop.",
            reply_markup=back_to_admin_keyboard(),
        )
    elif data == "back_to_admin":
        await show_admin_panel_from_query(query, context)


async def show_admin_panel_from_query(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin panel (used from callback or admin command)."""
    await query.edit_message_text(
        "🔧 **Advanced Admin Panel**\n\nUse the buttons below to configure the bot:",
        reply_markup=admin_panel_keyboard(),
    )


async def _handle_signup(query) -> None:
    url = await get_config_value("signup_url")
    if url:
        await query.answer("🔑 Time to level up! 🚀")
    else:
        await query.answer("❌ Signup URL not configured yet!", show_alert=True)


async def _handle_join_group(query) -> None:
    url = await get_config_value("join_group_url")
    if url:
        await query.answer("📢 Join the elite squad! 💪")
    else:
        await query.answer("❌ Join group URL not configured yet!", show_alert=True)


async def _start_live_chat(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    admin_group = await get_config_value("admin_group_id")
    if not admin_group:
        await query.answer("❌ Admin group not configured yet!", show_alert=True)
        return
    await set_user_state(query.from_user.id, "live_chat")
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text="💬 **Live Chat Connected**\n\nSend any message. Use /exit or the button to stop.",
        reply_markup=live_chat_exit_keyboard(),
    )
    await query.answer("✅ Live chat connected!")


async def _exit_live_chat_button(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = query.from_user.id
    state = await get_user_state(user_id)
    if state == "live_chat":
        await set_user_state(user_id, None)
        await query.edit_message_text(
            "🔙 **Live Chat Ended**\n\nSee you next time! 👋\n\nWant to chat again?",
            reply_markup=live_chat_start_keyboard(),
        )
        await query.answer("🔙 Live chat exited!")
    else:
        await query.answer("ℹ️ You're not in live chat mode!", show_alert=True)


async def _handle_download_hack(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    apk = await get_config_value("download_apk")
    if apk:
        await context.bot.send_document(
            chat_id=query.from_user.id,
            document=apk,
            caption="🎯 **Here's Your Premium APK!** 🎯",
        )
        await query.answer("🎯 Premium APK delivered! 🚀")
    else:
        await query.answer("❌ Download APK not configured yet!", show_alert=True)


async def _handle_daily_bonuses(query) -> None:
    url = await get_config_value("daily_bonuses_url")
    if url:
        await query.answer("🎁 Claim your rewards! ⭐")
    else:
        await query.answer("❌ Daily bonuses URL not configured yet!", show_alert=True)


async def _show_bot_config(query) -> None:
    config = await get_all_config()
    text = config.get("welcome_text", "")[:50]
    txt = f"{text}..." if len(config.get("welcome_text", "")) > 50 else text
    cfg_text = (
        f"🔧 **Bot Configuration**\n\n"
        f"📝 **Welcome Text:** {txt}\n"
        f"🖼️ **Welcome Image:** {'✅ Set' if config.get('welcome_image') else '❌ Not Set'}\n"
        f"🔗 **Signup URL:** {config.get('signup_url') or '❌ Not Set'}\n"
        f"👥 **Join Group URL:** {config.get('join_group_url') or '❌ Not Set'}\n"
        f"📱 **Download APK:** {'✅ Set' if config.get('download_apk') else '❌ Not Set'}\n"
        f"🎁 **Daily Bonuses URL:** {config.get('daily_bonuses_url') or '❌ Not Set'}\n"
        f"📱 **Admin Group ID:** {config.get('admin_group_id') or '❌ Not Set'}\n"
        f"💬 **Live Chat:** {'✅ Enabled' if config.get('live_chat_enabled', 'true') == 'true' else '❌ Disabled'}"
    )
    await query.edit_message_text(cfg_text, reply_markup=back_to_admin_keyboard())


async def _show_user_stats(query) -> None:
    total = await get_user_count()
    recent = await get_recent_users(5)
    admins = await get_all_admin_ids()
    lines = []
    for u in recent:
        un = f"@{u['username']}" if u.get("username") else "No username"
        lines.append(f"• {un} ({u.get('first_name', '')})")
    text = (
        f"👥 **User Statistics**\n\n"
        f"📊 **Total Users:** {total}\n\n"
        f"**Recent Users:**\n" + ("\n".join(lines) if lines else "No users yet")
    )
    await query.edit_message_text(text, reply_markup=back_to_admin_keyboard())


async def _show_logs(query) -> None:
    logs = await get_recent_logs(10)
    if not logs:
        await query.edit_message_text(
            "📑 **No Logs Available**\n\nNo activity logged yet.",
            reply_markup=back_to_admin_keyboard(),
        )
        return
    lines = []
    for log in logs:
        status = "✅" if log.get("dm_sent") else "❌"
        err = f" ({log.get('error_message', '')})" if not log.get("dm_sent") else ""
        lines.append(
            f"• @{log.get('username', '')} (ID: {log.get('user_id')}) - {status}{err}"
        )
    text = "📑 **Recent Logs**\n\n" + "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n\n... (truncated)"
    await query.edit_message_text(text, reply_markup=back_to_admin_keyboard())
