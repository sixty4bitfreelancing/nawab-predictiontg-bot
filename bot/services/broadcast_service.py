"""
Broadcast service - scalable message broadcasting with structured error handling.
Handles RetryAfter, Forbidden (blocked), NetworkError.
One user's failure must NOT crash the broadcast loop.
"""

import asyncio
from dataclasses import dataclass
from typing import Any

from telegram import Bot
from telegram.error import RetryAfter, Forbidden, NetworkError, TelegramError

from bot.config import BROADCAST_DELAY_SECONDS, BROADCAST_RETRY_AFTER_FALLBACK_SECONDS
from bot.database import execute_query, fetch_all
from bot.utils.exceptions import BroadcastError
from bot.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BroadcastResult:
    """Result of a broadcast run."""

    total: int
    delivered: int
    failed: int
    blocked: int
    message_type: str


def _extract_message_data(message: Any) -> dict | None:
    """Extract broadcast payload from Telegram message."""
    if message.text is not None:
        return {"type": "text", "content": message.text}
    if message.photo:
        return {
            "type": "photo",
            "file_id": message.photo[-1].file_id,
            "caption": message.caption,
        }
    if message.video:
        return {
            "type": "video",
            "file_id": message.video.file_id,
            "caption": message.caption,
        }
    if message.voice:
        return {"type": "voice", "file_id": message.voice.file_id, "caption": message.caption}
    if message.audio:
        return {"type": "audio", "file_id": message.audio.file_id, "caption": message.caption}
    if message.document:
        return {
            "type": "document",
            "file_id": message.document.file_id,
            "caption": message.caption,
        }
    if message.video_note:
        return {"type": "video_note", "file_id": message.video_note.file_id}
    if message.sticker:
        return {"type": "sticker", "file_id": message.sticker.file_id}
    if message.animation:
        return {
            "type": "animation",
            "file_id": message.animation.file_id,
            "caption": message.caption,
        }
    return None


async def _send_to_user(bot: Bot, user_id: int, data: dict) -> None:
    """Send a single message to a user. Raises on failure."""
    msg_type = data["type"]
    if msg_type == "text":
        await bot.send_message(chat_id=user_id, text=data["content"])
    elif msg_type == "photo":
        await bot.send_photo(
            chat_id=user_id,
            photo=data["file_id"],
            caption=data.get("caption"),
        )
    elif msg_type == "video":
        await bot.send_video(
            chat_id=user_id,
            video=data["file_id"],
            caption=data.get("caption"),
        )
    elif msg_type == "voice":
        await bot.send_voice(
            chat_id=user_id,
            voice=data["file_id"],
            caption=data.get("caption"),
        )
    elif msg_type == "audio":
        await bot.send_audio(
            chat_id=user_id,
            audio=data["file_id"],
            caption=data.get("caption"),
        )
    elif msg_type == "document":
        await bot.send_document(
            chat_id=user_id,
            document=data["file_id"],
            caption=data.get("caption"),
        )
    elif msg_type == "video_note":
        await bot.send_video_note(chat_id=user_id, video_note=data["file_id"])
    elif msg_type == "sticker":
        await bot.send_sticker(chat_id=user_id, sticker=data["file_id"])
    elif msg_type == "animation":
        await bot.send_animation(
            chat_id=user_id,
            animation=data["file_id"],
            caption=data.get("caption"),
        )
    else:
        raise BroadcastError(f"Unsupported message type: {msg_type}")


async def broadcast_to_users(
    bot: Bot,
    user_ids: list[int],
    message: Any,
) -> BroadcastResult:
    """
    Broadcast a message to a list of users.
    - Catches RetryAfter: waits and retries once for that user
    - Catches Forbidden: counts as blocked (user blocked bot)
    - Catches NetworkError: counts as failed
    - Other errors: counts as failed, logged, loop continues
    """
    data = _extract_message_data(message)
    if not data:
        raise BroadcastError("Unsupported message type for broadcast")

    delivered = 0
    failed = 0
    blocked = 0
    total = len(user_ids)

    for user_id in user_ids:
        try:
            await _send_to_user(bot, user_id, data)
            delivered += 1
        except RetryAfter as e:
            wait_sec = getattr(e, "retry_after", None)
            if wait_sec is None:
                wait_sec = BROADCAST_RETRY_AFTER_FALLBACK_SECONDS
            if isinstance(wait_sec, (int, float)):
                wait_sec = int(wait_sec)
            else:
                wait_sec = BROADCAST_RETRY_AFTER_FALLBACK_SECONDS
            logger.warning(
                "Broadcast RetryAfter for user %s | waiting %s seconds",
                user_id,
                wait_sec,
            )
            await asyncio.sleep(wait_sec)
            try:
                await _send_to_user(bot, user_id, data)
                delivered += 1
            except (Forbidden, NetworkError, TelegramError) as retry_err:
                if isinstance(retry_err, Forbidden):
                    blocked += 1
                    logger.warning("Broadcast blocked for user %s | %s", user_id, retry_err)
                else:
                    failed += 1
                    logger.exception(
                        "Broadcast failed for user %s | %s: %s",
                        user_id,
                        type(retry_err).__name__,
                        retry_err,
                    )
        except Forbidden:
            blocked += 1
            logger.warning("Broadcast blocked for user %s | user blocked bot", user_id)
        except NetworkError as e:
            failed += 1
            logger.exception("Broadcast network error for user %s | %s", user_id, e)
        except TelegramError as e:
            failed += 1
            logger.exception(
                "Broadcast failed for user %s | %s: %s",
                user_id,
                type(e).__name__,
                e,
            )
        except Exception as e:
            failed += 1
            logger.exception("Broadcast unexpected error for user %s | %s", user_id, e)

        await asyncio.sleep(BROADCAST_DELAY_SECONDS)

    result = BroadcastResult(
        total=total,
        delivered=delivered,
        failed=failed,
        blocked=blocked,
        message_type=data["type"],
    )

    # Persist broadcast result
    try:
        await execute_query(
            """
            INSERT INTO broadcast_results (total_users, delivered, failed, blocked, message_type)
            VALUES ($1, $2, $3, $4, $5)
            """,
            total,
            delivered,
            failed,
            blocked,
            data["type"],
        )
    except Exception as e:
        logger.exception("Failed to save broadcast result: %s", e)

    logger.info(
        "Broadcast complete | total=%s delivered=%s failed=%s blocked=%s",
        total,
        delivered,
        failed,
        blocked,
    )

    return result
