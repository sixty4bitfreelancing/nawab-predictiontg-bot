"""
Log service - join logs and activity logs in PostgreSQL.
"""

from bot.database import execute_query, fetch_all
from bot.utils.exceptions import DatabaseError
from bot.utils.logger import get_logger

logger = get_logger(__name__)


async def log_join(
    user_id: int,
    username: str | None,
    dm_sent: bool,
    error_message: str | None = None,
) -> None:
    """Log a join request."""
    try:
        await execute_query(
            """
            INSERT INTO join_logs (user_id, username, dm_sent, error_message)
            VALUES ($1, $2, $3, $4)
            """,
            user_id,
            username or "",
            dm_sent,
            error_message,
        )
    except DatabaseError:
        raise
    except Exception as e:
        logger.exception("Failed to log join for user %s", user_id)
        raise DatabaseError("Failed to log join", original=e) from e


async def get_recent_logs(limit: int = 10) -> list[dict]:
    """Get recent join logs for admin panel."""
    try:
        rows = await fetch_all(
            """
            SELECT user_id, username, dm_sent, error_message, created_at
            FROM join_logs ORDER BY created_at DESC LIMIT $1
            """,
            limit,
        )
        return [dict(r) for r in rows]
    except DatabaseError:
        raise
    except Exception as e:
        logger.exception("Failed to get recent logs")
        raise DatabaseError("Failed to get logs", original=e) from e
