"""
PostgreSQL database connection and query wrapper.
All DB operations must be wrapped with error handling.
Raises DatabaseError on failure - never crashes the event loop.
"""

import asyncpg
from asyncpg import Pool

from bot.config import DATABASE_URL
from bot.utils.exceptions import DatabaseError
from bot.utils.logger import get_logger

logger = get_logger(__name__)

_pool: Pool | None = None


async def get_pool() -> Pool:
    """Get or create the connection pool."""
    global _pool
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=1,
                max_size=10,
                command_timeout=60,
            )
            logger.info("Database pool created")
        except Exception as e:
            logger.exception("Failed to create database pool")
            raise DatabaseError("Failed to connect to database", original=e) from e
    return _pool


async def close_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed")


async def execute_query(
    query: str,
    *args,
    timeout: float | None = None,
) -> str | None:
    """
    Execute a query that returns nothing (INSERT/UPDATE/DELETE).
    Raises DatabaseError on failure.
    """
    pool = await get_pool()
    try:
        async with pool.acquire() as conn:
            await conn.execute(query, *args, timeout=timeout)
        return None
    except asyncpg.PostgresError as e:
        logger.exception("Database operation failed: %s", query[:100])
        raise DatabaseError("Database operation failed", original=e) from e


async def fetch_one(query: str, *args, timeout: float | None = None):
    """
    Execute a query and return a single row.
    Raises DatabaseError on failure.
    """
    pool = await get_pool()
    try:
        async with pool.acquire() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)
    except asyncpg.PostgresError as e:
        logger.exception("Database fetch failed: %s", query[:100])
        raise DatabaseError("Database fetch failed", original=e) from e


async def fetch_all(query: str, *args, timeout: float | None = None):
    """
    Execute a query and return all rows.
    Raises DatabaseError on failure.
    """
    pool = await get_pool()
    try:
        async with pool.acquire() as conn:
            return await conn.fetch(query, *args, timeout=timeout)
    except asyncpg.PostgresError as e:
        logger.exception("Database fetch failed: %s", query[:100])
        raise DatabaseError("Database fetch failed", original=e) from e


async def init_db() -> None:
    """Create tables if they do not exist."""
    pool = await get_pool()
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    user_id BIGINT PRIMARY KEY,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    joined_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS bot_config (
                    key VARCHAR(100) PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS user_states (
                    user_id BIGINT PRIMARY KEY,
                    state VARCHAR(50),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS admin_states (
                    admin_id BIGINT PRIMARY KEY,
                    state VARCHAR(50),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS broadcast_results (
                    id SERIAL PRIMARY KEY,
                    broadcast_at TIMESTAMPTZ DEFAULT NOW(),
                    total_users INT,
                    delivered INT,
                    failed INT,
                    blocked INT,
                    message_type VARCHAR(50)
                );

                CREATE TABLE IF NOT EXISTS join_logs (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    username VARCHAR(255),
                    dm_sent BOOLEAN,
                    error_message TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
        logger.info("Database tables initialized")
    except asyncpg.PostgresError as e:
        logger.exception("Failed to initialize database")
        raise DatabaseError("Failed to initialize database", original=e) from e
