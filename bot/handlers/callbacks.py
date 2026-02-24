"""Callback query handlers for inline buttons."""

import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.config import SUPERADMIN_ID
from bot.keyboards.admin import admin_panel_keyboard, back_to_admin_keyboard
from bot.services.config_service import get_config_value, get_all_config, set_config_value
from bot.services.user_service import (
    is_admin,
    get_all_admin_ids,
    get_user_count,
    get_recent_users,
    get_admins_with_info,
    add_admin as add_admin_user,
    remove_admin as remove_admin_user,
)
from bot.services.state_service import get_admin_state, set_admin_state
from bot.services.log_service import get_recent_logs
from bot.services.broadcast_service import broadcast_to_users, BroadcastResult
from bot.services.welcome_service import send_welcome, _parse_welcome_buttons
from bot.utils.maintenance import check_maintenance
from bot.utils.exceptions import WelcomeBuilderError
from bot.utils.logger import get_logger

logger = get_logger(__name__)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries from inline buttons."""
    query = update.callback_query
    if not query:
        return
    data = query.data
    user_id = query.from_user.id if query.from_user else 0

    # Maintenance: block non-admins before answering callback (user-facing buttons only)
    is_admin_user = await is_admin(user_id)
    if not is_admin_user and await check_maintenance(update, context):
        return
    await query.answer()

    # Admin-only
    if not await is_admin(user_id):
        await query.edit_message_text("❌ Access denied. You are not authorized as an admin.")
        return

    if data == "noop_superadmin":
        await query.answer("Superadmin cannot be removed.", show_alert=True)
        return
    if data == "set_welcome_text":
        await set_admin_state(user_id, "waiting_welcome_text")
        await query.edit_message_text(
            "📝 **Set Welcome Text**\n\nSend the new welcome message text."
        )
    elif data == "set_welcome_image":
        await set_admin_state(user_id, "waiting_welcome_image")
        await query.edit_message_text("🖼️ **Set Welcome Image**\n\nSend the image.")
    elif data == "preview_welcome":
        await _preview_welcome(query, context)
    elif data == "custom_welcome_buttons":
        await _show_custom_welcome_buttons(query, context)
    elif data.startswith("remove_custom_btn_"):
        await _handle_remove_custom_button(query, context, data)
    elif data == "add_custom_btn":
        await set_admin_state(user_id, "waiting_custom_btn_label")
        await query.edit_message_text(
            "🔘 **Add Button**\n\nSend the **button label** (text shown on the button).",
            reply_markup=back_to_admin_keyboard(),
        )
    elif data == "bot_config":
        await _show_bot_config(query)
    elif data == "toggle_auto_accept":
        await _toggle_auto_accept(query)
    elif data == "send_broadcast":
        await set_admin_state(user_id, "waiting_broadcast")
        await query.edit_message_text(
            "📡 **Send Message to All Users**\n\n"
            "Send the message (text, photo, video, etc.) to broadcast."
        )
    elif data == "view_users":
        await _show_user_stats(query)
    elif data == "manage_admins":
        await _show_manage_admins(query, context)
    elif data == "add_admin_prompt":
        await set_admin_state(user_id, "waiting_add_admin_id")
        await query.edit_message_text(
            "👑 **Add Admin**\n\n"
            "Send the Telegram **User ID** (numbers only), or **forward a message** from the user you want to add.\n\n"
            "To get a user's ID: they can send /start to the bot, or use @userinfobot.",
            reply_markup=back_to_admin_keyboard(),
        )
    elif data.startswith("remove_admin_"):
        await _handle_remove_admin(query, context, data)
    elif data == "view_logs":
        await _show_logs(query)
    elif data == "stop_bot":
        await query.edit_message_text(
            "🛑 **Stop Bot**\n\nRestart the process to stop.",
            reply_markup=back_to_admin_keyboard(),
        )
    elif data == "back_to_admin":
        await set_admin_state(user_id, None)
        await show_admin_panel_from_query(query, context)


async def _preview_welcome(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the current welcome message to the admin as a preview."""
    admin_id = query.from_user.id if query.from_user else 0
    try:
        await send_welcome(context.bot, admin_id)
        await query.edit_message_text(
            "✅ **Preview sent!**\n\nThe welcome message (text, image, and buttons) was sent above. "
            "That’s exactly what new users will see.",
            reply_markup=back_to_admin_keyboard(),
        )
    except WelcomeBuilderError as e:
        await query.edit_message_text(
            f"❌ **Preview failed**\n\n{str(e)}\n\nCheck welcome text/image and try again.",
            reply_markup=back_to_admin_keyboard(),
        )
    except Exception as e:
        logger.exception("Preview welcome failed: %s", e)
        await query.edit_message_text(
            f"❌ **Preview failed**\n\nSomething went wrong. Try again later.",
            reply_markup=back_to_admin_keyboard(),
        )


async def show_admin_panel_from_query(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin panel (used from callback or admin command)."""
    await query.edit_message_text(
        "🔧 **Advanced Admin Panel**\n\nUse the buttons below to configure the bot:",
        reply_markup=admin_panel_keyboard(),
    )


async def _show_custom_welcome_buttons(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show custom welcome buttons management (max 10)."""
    config = await get_all_config()
    buttons = _parse_welcome_buttons(config.get("welcome_buttons") or "[]")
    MAX_BTNS = 10
    lines = [f"{i+1}. {b['label']} → {b['url'][:40]}..." if len(b['url']) > 40 else f"{i+1}. {b['label']} → {b['url']}" for i, b in enumerate(buttons)]
    keyboard = []
    for i, btn in enumerate(buttons):
        keyboard.append([InlineKeyboardButton(f"❌ Remove {i+1}. {btn['label'][:20]}", callback_data=f"remove_custom_btn_{i}")])
    if len(buttons) < MAX_BTNS:
        keyboard.append([InlineKeyboardButton("➕ Add Button", callback_data="add_custom_btn")])
    keyboard.append([InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="back_to_admin")])
    text = (
        f"🔘 **Custom Welcome Buttons** (max {MAX_BTNS})\n\n"
        "**Current buttons:**\n" + ("\n".join(lines) if lines else "None. Add buttons below.\n") + "\n\n"
        "• **Add:** label + URL (one row per button under the welcome message).\n"
        "• **Remove:** use the ❌ button."
    )
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def _handle_remove_custom_button(query, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    """Remove a custom welcome button by index."""
    try:
        idx = int(data.replace("remove_custom_btn_", ""))
    except ValueError:
        await query.answer("Invalid data.", show_alert=True)
        return
    config = await get_all_config()
    buttons = _parse_welcome_buttons(config.get("welcome_buttons") or "[]")
    if idx < 0 or idx >= len(buttons):
        await query.answer("Button not found.", show_alert=True)
        return
    buttons.pop(idx)
    await set_config_value("welcome_buttons", json.dumps(buttons))
    await query.answer("✅ Button removed.")
    await _show_custom_welcome_buttons(query, context)


async def _show_bot_config(query) -> None:
    config = await get_all_config()
    text = config.get("welcome_text", "")[:50]
    txt = f"{text}..." if len(config.get("welcome_text", "")) > 50 else text
    auto_accept = config.get("auto_accept_enabled", "true").lower() in ("true", "1", "yes")
    cfg_text = (
        f"🔧 **Bot Configuration**\n\n"
        f"📝 **Welcome Text:** {txt}\n"
        f"🖼️ **Welcome Image:** {'✅ Set' if config.get('welcome_image') else '❌ Not Set'}\n"
        f"🔘 **Welcome Buttons:** {len(_parse_welcome_buttons(config.get('welcome_buttons') or '[]'))}/10\n"
        f"🔄 **Auto-Accept Join:** {'✅ ON' if auto_accept else '❌ OFF'}"
    )
    await query.edit_message_text(cfg_text, reply_markup=back_to_admin_keyboard())


async def _toggle_auto_accept(query) -> None:
    """Toggle auto-accept join requests on/off. Other services (welcome, broadcast, etc.) stay on."""
    current = await get_config_value("auto_accept_enabled")
    new_value = "false" if current.lower() in ("true", "1", "yes") else "true"
    await set_config_value("auto_accept_enabled", new_value)
    status = "ON" if new_value == "true" else "OFF"
    await query.edit_message_text(
        f"🔄 **Auto-Accept Join** is now **{status}**\n\n"
        f"When OFF, the bot will not approve channel/group join requests. "
        f"All other services (/start welcome, broadcast) keep running.",
        reply_markup=back_to_admin_keyboard(),
    )


async def _show_manage_admins(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show list of admins with Add / Remove options."""
    admins = await get_admins_with_info()
    lines = []
    keyboard = []
    for a in admins:
        uid = a["user_id"]
        label = a.get("username") or a.get("first_name") or str(uid)
        display = f"@{label}" if a.get("username") else f"{label} (ID: {uid})"
        lines.append(f"• {display} — `{uid}`" + (" 👑" if SUPERADMIN_ID and uid == SUPERADMIN_ID else ""))
        if SUPERADMIN_ID and uid == SUPERADMIN_ID:
            keyboard.append([InlineKeyboardButton(f"🔒 {display} (Superadmin)", callback_data="noop_superadmin")])
        else:
            keyboard.append([InlineKeyboardButton(f"❌ Remove {display}", callback_data=f"remove_admin_{uid}")])
    keyboard.append([InlineKeyboardButton("➕ Add Admin", callback_data="add_admin_prompt")])
    keyboard.append([InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="back_to_admin")])
    text = (
        "👑 **Manage Admins**\n\n"
        "**Current admins:**\n" + ("\n".join(lines) if lines else "None yet.") + "\n\n"
        "• **Add:** use the button below, then send a User ID or forward a message from that user.\n"
        "• **Remove:** use the ❌ button (Superadmin cannot be removed)."
    )
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def _handle_remove_admin(query, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    """Remove an admin (unless they are superadmin)."""
    try:
        uid = int(data.replace("remove_admin_", ""))
    except ValueError:
        await query.answer("Invalid data.", show_alert=True)
        return
    if SUPERADMIN_ID and uid == SUPERADMIN_ID:
        await query.answer("Cannot remove Superadmin.", show_alert=True)
        return
    try:
        await remove_admin_user(uid)
        await query.answer("✅ Admin removed.")
        await _show_manage_admins(query, context)
    except Exception as e:
        logger.exception("Remove admin failed: %s", e)
        await query.answer("Failed to remove admin.", show_alert=True)


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
