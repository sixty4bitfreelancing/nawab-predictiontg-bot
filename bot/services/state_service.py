"""
User and admin state service - live chat and config wizard states.
"""

from bot.database import fetch_one, execute_query
from bot.utils.exceptions import DatabaseError
from bot.utils.logger import get_logger

logger = get_logger(__name__)


async def get_user_state(user_id: int) -> str | None:
    """Get user state (e.g. live_chat)."""
    try:
        row = await fetch_one("SELECT state FROM user_states WHERE user_id = $1", user_id)
        return row["state"] if row and row["state"] else None
    except DatabaseError:
        raise
    except Exception as e:
        logger.exception("Failed to get user state %s", user_id)
        raise DatabaseError("Failed to get state", original=e) from e


async def set_user_state(user_id: int, state: str | None) -> None:
    """Set user state. Pass None to clear."""
    try:
        if state is None:
            await execute_query("DELETE FROM user_states WHERE user_id = $1", user_id)
        else:
            await execute_query(
                """
                INSERT INTO user_states (user_id, state, updated_at)
                VALUES ($1, $2, NOW())
                ON CONFLICT (user_id) DO UPDATE SET state = $2, updated_at = NOW()
                """,
                user_id,
                state,
            )
    except DatabaseError:
        raise
    except Exception as e:
        logger.exception("Failed to set user state %s", user_id)
        raise DatabaseError("Failed to set state", original=e) from e


async def get_admin_state(admin_id: int) -> str | None:
    """Get admin state (e.g. waiting_welcome_text)."""
    try:
        row = await fetch_one("SELECT state FROM admin_states WHERE admin_id = $1", admin_id)
        return row["state"] if row and row["state"] else None
    except DatabaseError:
        raise
    except Exception as e:
        logger.exception("Failed to get admin state %s", admin_id)
        raise DatabaseError("Failed to get state", original=e) from e


async def set_admin_state(admin_id: int, state: str | None) -> None:
    """Set admin state. Pass None to clear."""
    try:
        if state is None:
            await execute_query("DELETE FROM admin_states WHERE admin_id = $1", admin_id)
        else:
            await execute_query(
                """
                INSERT INTO admin_states (admin_id, state, updated_at)
                VALUES ($1, $2, NOW())
                ON CONFLICT (admin_id) DO UPDATE SET state = $2, updated_at = NOW()
                """,
                admin_id,
                state,
            )
    except DatabaseError:
        raise
    except Exception as e:
        logger.exception("Failed to set admin state %s", admin_id)
        raise DatabaseError("Failed to set state", original=e) from e
