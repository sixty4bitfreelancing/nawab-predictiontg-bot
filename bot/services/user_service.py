"""
User service - manages users and admins in PostgreSQL.
"""

from bot.database import fetch_one, fetch_all, execute_query
from bot.utils.exceptions import DatabaseError
from bot.utils.logger import get_logger

logger = get_logger(__name__)


async def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    try:
        row = await fetch_one("SELECT 1 FROM admins WHERE user_id = $1", user_id)
        return row is not None
    except DatabaseError:
        raise
    except Exception as e:
        logger.exception("Failed to check admin status for %s", user_id)
        raise DatabaseError("Failed to check admin", original=e) from e


async def get_all_admin_ids() -> list[int]:
    """Get all admin user IDs."""
    try:
        rows = await fetch_all("SELECT user_id FROM admins ORDER BY user_id")
        return [r["user_id"] for r in rows]
    except DatabaseError:
        raise
    except Exception as e:
        logger.exception("Failed to get admins")
        raise DatabaseError("Failed to get admins", original=e) from e


async def add_admin(user_id: int) -> None:
    """Add admin."""
    try:
        await execute_query(
            "INSERT INTO admins (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING",
            user_id,
        )
    except DatabaseError:
        raise
    except Exception as e:
        logger.exception("Failed to add admin %s", user_id)
        raise DatabaseError("Failed to add admin", original=e) from e


async def remove_admin(user_id: int) -> bool:
    """Remove admin. Returns True if removed, False if not found."""
    try:
        result = await execute_query(
            "DELETE FROM admins WHERE user_id = $1",
            user_id,
        )
        return True
    except DatabaseError:
        raise
    except Exception as e:
        logger.exception("Failed to remove admin %s", user_id)
        raise DatabaseError("Failed to remove admin", original=e) from e


async def get_admins_with_info() -> list[dict]:
    """Get all admins with user_id, username, first_name (from users table when available)."""
    try:
        rows = await fetch_all(
            """
            SELECT a.user_id, u.username, u.first_name
            FROM admins a
            LEFT JOIN users u ON u.user_id = a.user_id
            ORDER BY a.user_id
            """
        )
        return [dict(r) for r in rows]
    except DatabaseError:
        raise
    except Exception as e:
        logger.exception("Failed to get admins with info")
        raise DatabaseError("Failed to get admins", original=e) from e


async def upsert_user(
    user_id: int,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> None:
    """Insert or update user."""
    try:
        await execute_query(
            """
            INSERT INTO users (user_id, username, first_name, last_name, updated_at)
            VALUES ($1, $2, $3, $4, NOW())
            ON CONFLICT (user_id) DO UPDATE SET
                username = COALESCE(EXCLUDED.username, users.username),
                first_name = COALESCE(EXCLUDED.first_name, users.first_name),
                last_name = COALESCE(EXCLUDED.last_name, users.last_name),
                updated_at = NOW()
            """,
            user_id,
            username,
            first_name,
            last_name,
        )
    except DatabaseError:
        raise
    except Exception as e:
        logger.exception("Failed to upsert user %s", user_id)
        raise DatabaseError("Failed to save user", original=e) from e


async def get_user(user_id: int) -> dict | None:
    """Get user by ID."""
    try:
        row = await fetch_one(
            "SELECT user_id, username, first_name, last_name, joined_at FROM users WHERE user_id = $1",
            user_id,
        )
        if row:
            return dict(row)
        return None
    except DatabaseError:
        raise
    except Exception as e:
        logger.exception("Failed to get user %s", user_id)
        raise DatabaseError("Failed to get user", original=e) from e


async def get_all_user_ids(exclude_admin_ids: list[int] | None = None) -> list[int]:
    """Get all user IDs for broadcast, optionally excluding admins."""
    try:
        if exclude_admin_ids and len(exclude_admin_ids) > 0:
            rows = await fetch_all(
                "SELECT user_id FROM users WHERE NOT (user_id = ANY($1::bigint[])) ORDER BY user_id",
                exclude_admin_ids,
            )
        else:
            rows = await fetch_all("SELECT user_id FROM users ORDER BY user_id")
        return [r["user_id"] for r in rows]
    except DatabaseError:
        raise
    except Exception as e:
        logger.exception("Failed to get user IDs")
        raise DatabaseError("Failed to get users", original=e) from e


async def get_user_count() -> int:
    """Get total user count."""
    try:
        row = await fetch_one("SELECT COUNT(*) as c FROM users")
        return row["c"] if row else 0
    except DatabaseError:
        raise
    except Exception as e:
        logger.exception("Failed to get user count")
        raise DatabaseError("Failed to get user count", original=e) from e


async def get_recent_users(limit: int = 5) -> list[dict]:
    """Get recent users for stats."""
    try:
        rows = await fetch_all(
            "SELECT user_id, username, first_name, joined_at FROM users ORDER BY joined_at DESC LIMIT $1",
            limit,
        )
        return [dict(r) for r in rows]
    except DatabaseError:
        raise
    except Exception as e:
        logger.exception("Failed to get recent users")
        raise DatabaseError("Failed to get users", original=e) from e
