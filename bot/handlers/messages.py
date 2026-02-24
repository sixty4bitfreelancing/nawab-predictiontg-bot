"""Message handlers - admin config wizard."""

import json
from telegram import Update
from telegram.ext import ContextTypes

from bot.services.config_service import get_config_value, set_config_value
from bot.services.state_service import get_admin_state, set_admin_state
from bot.services.user_service import add_admin as add_admin_user, upsert_user
from bot.services.broadcast_service import broadcast_to_users
from bot.services.welcome_service import _parse_welcome_buttons
from bot.utils.maintenance import check_maintenance
from bot.utils.exceptions import ValidationError
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

    # No other message routing (live chat removed)


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

    elif state == "waiting_admin_group":
        try:
            gid = int(message.text.strip())
            await set_config_value("admin_group_id", str(gid))
            await message.reply_text(f"✅ Admin group ID updated to: {gid}")
        except (ValueError, AttributeError):
            await message.reply_text("❌ Please send a valid group ID (numbers only).")
            return

    elif state == "waiting_add_admin_id":
        target_id = None
        if message.forward_from:
            target_id = message.forward_from.id
            await upsert_user(
                target_id,
                username=message.forward_from.username,
                first_name=message.forward_from.first_name,
                last_name=message.forward_from.last_name,
            )
        elif message.text and message.text.strip().isdigit():
            target_id = int(message.text.strip())
        if target_id is None:
            await message.reply_text(
                "❌ Send a numeric User ID, or forward a message from the user you want to add as admin."
            )
            return
        try:
            await add_admin_user(target_id)
            await message.reply_text(f"✅ User ID {target_id} added as admin.")
        except Exception as e:
            await message.reply_text(f"❌ Failed to add admin: {e}")
        await set_admin_state(user_id, None)
        return

    elif state == "waiting_broadcast":
        await _run_broadcast(update, context)
        await set_admin_state(user_id, None)
        return

    await set_admin_state(user_id, None)


async def _run_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run broadcast to all users."""
    message = update.message
    from bot.services.user_service import get_all_user_ids, get_all_admin_ids
    admin_ids = await get_all_admin_ids()
    user_ids = await get_all_user_ids(exclude_admin_ids=admin_ids)

    if not user_ids:
        await message.reply_text("❌ No users to broadcast to.")
        return

    await message.reply_text(f"📡 Broadcasting to {len(user_ids)} users...")
    result = await broadcast_to_users(context.bot, user_ids, message)
    await message.reply_text(
        f"📡 **Broadcast Complete**\n\n"
        f"✅ Delivered: {result.delivered}\n"
        f"❌ Failed: {result.failed}\n"
        f"🚫 Blocked: {result.blocked}\n"
        f"📊 Total: {result.total}"
    )
