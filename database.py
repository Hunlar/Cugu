"""GROUP CINEMA PostgreSQL layer.

Creates the tables used for menus, content metadata, search selection and
per-group playback state. This module stores metadata only; it does not fetch,
copy, or redistribute media.
"""

import json
import logging
from typing import Any, Optional

import asyncpg

from config import settings

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


SCHEMA = """
CREATE TABLE IF NOT EXISTS menu_messages (
    chat_id BIGINT PRIMARY KEY,
    message_id BIGINT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS search_sessions (
    chat_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    source TEXT NOT NULL,
    query TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS contents (
    content_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    content_type TEXT,
    description TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS playback_sessions (
    chat_id BIGINT PRIMARY KEY,
    content_id TEXT REFERENCES contents(content_id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'idle',
    position_seconds DOUBLE PRECISION NOT NULL DEFAULT 0,
    source TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_contents_source_title
    ON contents (source, title);

CREATE INDEX IF NOT EXISTS idx_playback_status
    ON playback_sessions (status);
"""


async def initialize() -> None:
    """Create the connection pool and ensure the schema exists."""
    global _pool

    if _pool is not None:
        return
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is required for the database module")

    dsn = settings.database_url
    # Heroku Postgres may provide postgres://; asyncpg expects postgresql://.
    if dsn.startswith("postgres://"):
        dsn = "postgresql://" + dsn[len("postgres://"):]

    _pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=1,
        max_size=5,
        command_timeout=30,
        ssl="require" if "amazonaws.com" in dsn or "heroku" in dsn else None,
    )
    async with _pool.acquire() as conn:
        await conn.execute(SCHEMA)
    logger.info("Database pool initialized")


async def close() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def _db() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database is not initialized; call database.initialize()")
    return _pool


async def save_menu_message(chat_id: int, message_id: int) -> None:
    async with _db().acquire() as conn:
        await conn.execute(
            """
            INSERT INTO menu_messages(chat_id, message_id)
            VALUES($1, $2)
            ON CONFLICT(chat_id) DO UPDATE
            SET message_id = EXCLUDED.message_id, updated_at = NOW()
            """,
            chat_id,
            message_id,
        )


async def get_menu_message(chat_id: int) -> Optional[int]:
    async with _db().acquire() as conn:
        return await conn.fetchval(
            "SELECT message_id FROM menu_messages WHERE chat_id = $1",
            chat_id,
        )


async def set_search_source(chat_id: int, user_id: int, source: str) -> None:
    async with _db().acquire() as conn:
        await conn.execute(
            """
            INSERT INTO search_sessions(chat_id, user_id, source)
            VALUES($1, $2, $3)
            ON CONFLICT(chat_id) DO UPDATE
            SET user_id = EXCLUDED.user_id,
                source = EXCLUDED.source,
                query = NULL,
                updated_at = NOW()
            """,
            chat_id,
            user_id,
            source,
        )


async def set_search_query(chat_id: int, query: str) -> None:
    async with _db().acquire() as conn:
        await conn.execute(
            """
            UPDATE search_sessions
            SET query = $2, updated_at = NOW()
            WHERE chat_id = $1
            """,
            chat_id,
            query,
        )


async def get_search_source(chat_id: int) -> Optional[str]:
    async with _db().acquire() as conn:
        return await conn.fetchval(
            "SELECT source FROM search_sessions WHERE chat_id = $1",
            chat_id,
        )


async def save_content(
    content_id: str,
    source: str,
    title: str,
    content_type: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    metadata_json = json.dumps(metadata or {}, ensure_ascii=False)
    async with _db().acquire() as conn:
        await conn.execute(
            """
            INSERT INTO contents(
                content_id, source, title, content_type, description, metadata
            )
            VALUES($1, $2, $3, $4, $5, $6::jsonb)
            ON CONFLICT(content_id) DO UPDATE SET
                source = EXCLUDED.source,
                title = EXCLUDED.title,
                content_type = EXCLUDED.content_type,
                description = EXCLUDED.description,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
            """,
            content_id,
            source,
            title,
            content_type,
            description,
            metadata_json,
        )


async def get_content(content_id: str) -> Optional[dict[str, Any]]:
    async with _db().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM contents WHERE content_id = $1", content_id
        )
    return dict(row) if row else None


async def save_playback(
    chat_id: int,
    content_id: Optional[str],
    status: str = "idle",
    position_seconds: float = 0,
    source: Optional[str] = None,
) -> None:
    async with _db().acquire() as conn:
        await conn.execute(
            """
            INSERT INTO playback_sessions(
                chat_id, content_id, status, position_seconds, source
            )
            VALUES($1, $2, $3, $4, $5)
            ON CONFLICT(chat_id) DO UPDATE SET
                content_id = EXCLUDED.content_id,
                status = EXCLUDED.status,
                position_seconds = EXCLUDED.position_seconds,
                source = EXCLUDED.source,
                updated_at = NOW()
            """,
            chat_id,
            content_id,
            status,
            max(0.0, float(position_seconds)),
            source,
        )


async def get_playback(chat_id: int) -> Optional[dict[str, Any]]:
    async with _db().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM playback_sessions WHERE chat_id = $1", chat_id
        )
    return dict(row) if row else None
