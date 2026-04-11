"""
Broadcast service - scalable message broadcasting with structured error handling.
Handles RetryAfter, Forbidden (blocked), NetworkError.
One user's failure must NOT crash the broadcast loop.

Supports:
- **copyMessage** broadcast: same content as your draft, no “Forwarded from” header (recommended).
- Resend via send_* + file_id (broadcast_to_users) for identical behaviour without copyMessage.
"""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from telegram import Bot
from telegram.error import RetryAfter, Forbidden, NetworkError, TelegramError

from bot.config import (
    BROADCAST_DELAY_SECONDS,
    BROADCAST_RETRY_AFTER_FALLBACK_SECONDS,
    BROADCAST_PROGRESS_EVERY,
)
from bot.database import execute_query, fetch_one
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


def broadcast_payload_type(message: Any) -> str | None:
    """Return content type if the message can be broadcast, else None."""
    data = _extract_message_data(message)
    return data["type"] if data else None


async def _copy_message_to_user(
    bot: Bot, user_id: int, from_chat_id: int, message_id: int
) -> None:
    """Send a copy of the message (no forward header). Raises on failure."""
    await bot.copy_message(
        chat_id=user_id,
        from_chat_id=from_chat_id,
        message_id=message_id,
    )


async def broadcast_copy_to_users(
    bot: Bot,
    user_ids: list[int],
    from_chat_id: int,
    message_id: int,
    message_type: str,
    *,
    on_progress: Callable[[int, int, int, int, int], Awaitable[None]] | None = None,
    progress_every: int | None = None,
) -> BroadcastResult:
    """
    Copy the same source message to many users (Telegram copyMessage — no forward label).
    Same resilience as broadcast_to_users: per-user errors never stop the loop.
    Optional on_progress(done, total, delivered, failed, blocked) for live status.
    """
    delivered = 0
    failed = 0
    blocked = 0
    total = len(user_ids)
    pe = BROADCAST_PROGRESS_EVERY if progress_every is None else progress_every

    for idx, user_id in enumerate(user_ids, start=1):
        try:
            await _copy_message_to_user(bot, user_id, from_chat_id, message_id)
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
                "Broadcast copy RetryAfter for user %s | waiting %s seconds",
                user_id,
                wait_sec,
            )
            await asyncio.sleep(wait_sec)
            try:
                await _copy_message_to_user(bot, user_id, from_chat_id, message_id)
                delivered += 1
            except (Forbidden, NetworkError, TelegramError) as retry_err:
                if isinstance(retry_err, Forbidden):
                    blocked += 1
                    logger.warning(
                        "Broadcast copy blocked for user %s | %s", user_id, retry_err
                    )
                else:
                    failed += 1
                    logger.exception(
                        "Broadcast copy failed for user %s | %s: %s",
                        user_id,
                        type(retry_err).__name__,
                        retry_err,
                    )
        except Forbidden:
            blocked += 1
            logger.warning(
                "Broadcast copy blocked for user %s | user blocked bot", user_id
            )
        except NetworkError as e:
            failed += 1
            logger.exception("Broadcast copy network error for user %s | %s", user_id, e)
        except TelegramError as e:
            failed += 1
            logger.exception(
                "Broadcast copy failed for user %s | %s: %s",
                user_id,
                type(e).__name__,
                e,
            )
        except Exception as e:
            failed += 1
            logger.exception(
                "Broadcast copy unexpected error for user %s | %s", user_id, e
            )

        await asyncio.sleep(BROADCAST_DELAY_SECONDS)

        if on_progress and pe > 0 and (idx % pe == 0 or idx == total):
            try:
                await on_progress(idx, total, delivered, failed, blocked)
            except Exception:
                logger.debug("broadcast progress callback failed", exc_info=True)

    result = BroadcastResult(
        total=total,
        delivered=delivered,
        failed=failed,
        blocked=blocked,
        message_type=message_type,
    )

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
            f"copy:{message_type}",
        )
    except Exception as e:
        logger.exception("Failed to save broadcast result: %s", e)

    logger.info(
        "Broadcast copy complete | total=%s delivered=%s failed=%s blocked=%s",
        total,
        delivered,
        failed,
        blocked,
    )

    return result


async def get_last_broadcast_row() -> dict | None:
    """Latest row from broadcast_results (for Broadcast Status)."""
    try:
        row = await fetch_one(
            """
            SELECT broadcast_at, total_users, delivered, failed, blocked, message_type
            FROM broadcast_results
            ORDER BY id DESC
            LIMIT 1
            """
        )
        return dict(row) if row else None
    except Exception as e:
        logger.exception("Failed to read last broadcast: %s", e)
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
