"""Message handlers - admin config, live chat, admin reply."""

import re
from telegram import Update
from telegram.ext import ContextTypes

from bot.services.config_service import get_config_value, set_config_value
from bot.services.user_service import is_admin, get_user
from bot.services.state_service import get_user_state, set_user_state, get_admin_state, set_admin_state
from bot.services.broadcast_service import broadcast_to_users
from bot.utils.maintenance import check_maintenance
from bot.utils.exceptions import ValidationError
from bot.utils.logger import get_logger

logger = get_logger(__name__)

USER_HEADER_FORMAT = "👤 User: @{username} ({first_name})\n🆔 ID: {user_id}\n💬 Message:\n\n"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route messages: admin config, live chat, admin reply."""
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

    # Live chat (user)
    user_state = await get_user_state(user_id)
    if user_state == "live_chat":
        text = (message.text or "").lower().strip()
        if text in ("/exit", "/stop", "/quit", "exit", "stop", "quit"):
            await set_user_state(user_id, None)
            await message.reply_text("🔙 **Live Chat Ended**\n\nSee you next time! 👋")
            return
        await _forward_to_admin_group(update, context, user_id)
        return

    # Admin reply in admin group
    admin_group = await get_config_value("admin_group_id")
    if admin_group and str(message.chat.id) == admin_group and message.reply_to_message:
        await _handle_admin_reply(update, context)


async def _handle_admin_response(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    state: str,
) -> None:
    """Process admin config wizard response."""
    message = update.message
    user_id = update.effective_user.id

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

    elif state == "waiting_signup_url":
        if message.text and message.text.startswith(("http://", "https://")):
            await set_config_value("signup_url", message.text)
            await message.reply_text("✅ Signup URL updated!")
        else:
            await message.reply_text("❌ Please send a valid URL.")
            return

    elif state == "waiting_join_group_url":
        if message.text and message.text.startswith(("https://t.me/", "https://telegram.me/")):
            await set_config_value("join_group_url", message.text)
            await message.reply_text("✅ Join group URL updated!")
        else:
            await message.reply_text("❌ Please send a valid t.me link.")
            return

    elif state == "waiting_download_apk":
        if message.document:
            await set_config_value("download_apk", message.document.file_id)
            await message.reply_text("✅ Download APK updated!")
        else:
            await message.reply_text("❌ Please send an APK file.")
            return

    elif state == "waiting_daily_bonuses":
        if message.text and message.text.startswith(("http://", "https://")):
            await set_config_value("daily_bonuses_url", message.text)
            await message.reply_text("✅ Daily bonuses URL updated!")
        else:
            await message.reply_text("❌ Please send a valid URL.")
            return

    elif state == "waiting_admin_group":
        try:
            gid = int(message.text.strip())
            await set_config_value("admin_group_id", str(gid))
            await message.reply_text(f"✅ Admin group ID updated to: {gid}")
        except (ValueError, AttributeError):
            await message.reply_text("❌ Please send a valid group ID (numbers only).")
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


async def _forward_to_admin_group(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
) -> None:
    """Forward user message to admin group."""
    admin_group = await get_config_value("admin_group_id")
    if not admin_group:
        await update.message.reply_text("❌ Admin group not configured.")
        return

    user_info = await get_user(user_id) or {}
    username = user_info.get("username") or "No username"
    first_name = user_info.get("first_name") or "Unknown"
    header = USER_HEADER_FORMAT.format(
        username=username,
        first_name=first_name,
        user_id=user_id,
    )

    msg = update.message
    try:
        if msg.text:
            await context.bot.send_message(
                chat_id=int(admin_group),
                text=header + msg.text,
            )
        elif msg.photo:
            await context.bot.send_photo(
                chat_id=int(admin_group),
                photo=msg.photo[-1].file_id,
                caption=header + (msg.caption or "📸 Image"),
            )
        elif msg.video:
            await context.bot.send_video(
                chat_id=int(admin_group),
                video=msg.video.file_id,
                caption=header + (msg.caption or "🎥 Video"),
            )
        elif msg.voice:
            await context.bot.send_voice(
                chat_id=int(admin_group),
                voice=msg.voice.file_id,
                caption=header + "🎙️ Voice",
            )
        elif msg.audio:
            await context.bot.send_audio(
                chat_id=int(admin_group),
                audio=msg.audio.file_id,
                caption=header + (msg.caption or "🎵 Audio"),
            )
        elif msg.document:
            await context.bot.send_document(
                chat_id=int(admin_group),
                document=msg.document.file_id,
                caption=header + (msg.caption or "📄 Document"),
            )
        elif msg.sticker:
            await context.bot.send_sticker(
                chat_id=int(admin_group),
                sticker=msg.sticker.file_id,
            )
            await context.bot.send_message(chat_id=int(admin_group), text=header + "🎭 Sticker")
        elif msg.animation:
            await context.bot.send_animation(
                chat_id=int(admin_group),
                animation=msg.animation.file_id,
                caption=header + (msg.caption or "🎬 GIF"),
            )
        await msg.reply_text("✅ Message sent to admin. You'll receive a reply soon!")
    except Exception as e:
        logger.exception("Failed to forward to admin group: %s", e)
        await msg.reply_text("❌ Failed to send. Please try again later.")


async def _handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forward admin reply from admin group to user."""
    message = update.message
    reply = message.reply_to_message
    if not reply:
        return

    text = reply.text or reply.caption or ""
    match = re.search(r"🆔 ID: (\d+)", text)
    if not match:
        return

    user_id = int(match.group(1))
    state = await get_user_state(user_id)
    if state != "live_chat":
        await message.reply_text("❌ User is no longer in live chat mode.")
        return

    prefix = "💬 Admin Reply:\n\n"
    try:
        if message.text:
            await context.bot.send_message(chat_id=user_id, text=prefix + message.text)
        elif message.photo:
            await context.bot.send_photo(
                chat_id=user_id,
                photo=message.photo[-1].file_id,
                caption=prefix + (message.caption or "📸 Image from admin"),
            )
        elif message.video:
            await context.bot.send_video(
                chat_id=user_id,
                video=message.video.file_id,
                caption=prefix + (message.caption or "🎥 Video from admin"),
            )
        elif message.voice:
            await context.bot.send_voice(
                chat_id=user_id,
                voice=message.voice.file_id,
                caption=prefix + "🎙️ Voice from admin",
            )
        elif message.audio:
            await context.bot.send_audio(
                chat_id=user_id,
                audio=message.audio.file_id,
                caption=prefix + (message.caption or "🎵 Audio from admin"),
            )
        elif message.document:
            await context.bot.send_document(
                chat_id=user_id,
                document=message.document.file_id,
                caption=prefix + (message.caption or "📄 Document from admin"),
            )
        elif message.sticker:
            await context.bot.send_sticker(chat_id=user_id, sticker=message.sticker.file_id)
            await context.bot.send_message(chat_id=user_id, text=prefix + "🎭 Sticker from admin")
        elif message.animation:
            await context.bot.send_animation(
                chat_id=user_id,
                animation=message.animation.file_id,
                caption=prefix + (message.caption or "🎬 GIF from admin"),
            )
        await message.reply_text("✅ Reply sent to user!")
    except Exception as e:
        logger.exception("Failed to send admin reply to user %s: %s", user_id, e)
        await message.reply_text(f"❌ Failed to send reply: {e}")
