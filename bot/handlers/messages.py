"""Message handlers - admin config wizard."""

import json
from telegram import Update
from telegram.ext import ContextTypes

from bot.services.config_service import get_config_value, set_config_value
from bot.services.state_service import get_admin_state, set_admin_state
from bot.services.user_service import is_admin, get_all_user_ids, get_all_admin_ids
from bot.services.broadcast_service import broadcast_payload_type
from bot.keyboards.admin import confirm_broadcast_keyboard
from bot.services.welcome_service import send_welcome, _parse_welcome_buttons
from bot.utils.maintenance import check_maintenance
from bot.utils.logger import get_logger

logger = get_logger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route messages: admin config wizard only."""
    if await check_maintenance(update, context):
        return
    user_id = update.effective_user.id if update.effective_user else 0
    message = update.message
    if not message:
        return

    # Admin config wizard
    admin_state = await get_admin_state(user_id)
    if admin_state:
        await _handle_admin_response(update, context, admin_state)
        return

    # Any other message from a non-admin: reply with welcome (text + image + buttons)
    if not await is_admin(user_id):
        try:
            await send_welcome(context.bot, user_id)
        except Exception as e:
            logger.exception("Failed to send welcome on message to %s: %s", user_id, e)


async def _handle_admin_response(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    state: str,
) -> None:
    """Process admin config wizard response."""
    message = update.message
    user_id = update.effective_user.id

    if state == "waiting_custom_btn_label":
        if message.text and message.text.strip():
            context.user_data["custom_btn_label"] = message.text.strip()
            await set_admin_state(user_id, "waiting_custom_btn_url")
            await message.reply_text("✅ Now send the **URL** for this button (https://...).")
        else:
            await message.reply_text("❌ Please send the button label (text only).")
        return

    if state == "waiting_custom_btn_url":
        label = context.user_data.pop("custom_btn_label", None)
        if not label:
            await set_admin_state(user_id, None)
            await message.reply_text("❌ Session expired. Use Admin Panel → Custom Welcome Buttons → Add again.")
            return
        if not message.text or not message.text.strip().startswith(("http://", "https://")):
            await message.reply_text("❌ Please send a valid URL (https://...).")
            return
        url = message.text.strip()
        current = await get_config_value("welcome_buttons")
        buttons = _parse_welcome_buttons(current or "[]")
        buttons.append({"label": label, "url": url})
        buttons = buttons[:10]
        await set_config_value("welcome_buttons", json.dumps(buttons))
        await set_admin_state(user_id, None)
        await message.reply_text(f"✅ Button added. You have **{len(buttons)}/10** welcome buttons.")
        return

    if state == "waiting_welcome_text":
        if message.text:
            await set_config_value("welcome_text", message.text)
            await message.reply_text("✅ Welcome text updated!")
        else:
            await message.reply_text("❌ Please send text.")
            return

    elif state == "waiting_welcome_image":
        if message.photo:
            fid = message.photo[-1].file_id
            await set_config_value("welcome_image", fid)
            await message.reply_text("✅ Welcome image updated!")
        else:
            await message.reply_text("❌ Please send an image.")
            return

    elif state == "waiting_broadcast":
        msg_type = broadcast_payload_type(message)
        if not msg_type:
            await message.reply_text(
                "❌ Unsupported message type. Send text, photo, video, document, "
                "voice, audio, sticker, animation, or video note."
            )
            return
        admin_ids = await get_all_admin_ids()
        user_ids = await get_all_user_ids(exclude_admin_ids=admin_ids)
        if not user_ids:
            await message.reply_text("❌ No users to broadcast to.")
            await set_admin_state(user_id, None)
            return
        context.user_data["broadcast_pending"] = {
            "from_chat_id": message.chat_id,
            "message_id": message.message_id,
            "message_type": msg_type,
        }
        await set_admin_state(user_id, "waiting_broadcast_confirm")
        await message.reply_text(
            f"📢 Ready to broadcast\n\n"
            f"This message will be forwarded to {len(user_ids)} users "
            f"(admins excluded).\n"
            f"Type: {msg_type}\n\n"
            "Tap ✅ Send to start or ❌ Cancel.",
            reply_markup=confirm_broadcast_keyboard(),
        )
        return

    elif state == "waiting_broadcast_confirm":
        await message.reply_text(
            "⚠️ A broadcast is waiting for confirmation. "
            "Use ✅ Send or ❌ Cancel on the message above."
        )
        return

    await set_admin_state(user_id, None)
