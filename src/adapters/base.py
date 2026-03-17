"""Base interface for GHOST MARKET data source adapters."""

import json
from datetime import datetime, timedelta, timezone

import aiosqlite


class GhostMarketApiError(Exception):
    """Error from GHOST MARKET API interaction."""

    def __init__(self, message: str, status_code: int | None = None, retryable: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


class GhostMarketAdapter:
    """Base interface for GHOST MARKET data source adapters.

    Provides cache-first pattern with SQLite backing.
    Subclasses implement source-specific fetch logic (thin API clients).
    Signal interpretation is handled by the agent layer.
    """

    def __init__(self, db_path: str):
        """Initialize with path to SQLite database."""
        self.db_path = db_path
        self._conn = None

    async def _get_connection(self) -> aiosqlite.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = await aiosqlite.connect(self.db_path)
            await self._ensure_cache_table()
        return self._conn

    async def _ensure_cache_table(self) -> None:
        """Create cache table if not exists. Override to customize schema."""
        conn = await self._get_connection()
        table_name = f"{self.source_name}_cache"
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)
        await conn.commit()

    async def _cache_lookup(self, key: str) -> dict | None:
        """Check cache for key. Return data if fresh, None if expired/missing."""
        conn = await self._get_connection()
        table_name = f"{self.source_name}_cache"

        cursor = await conn.execute(
            f"""
            SELECT data, expires_at
            FROM {table_name}
            WHERE key = ?
            """,
            (key,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        data_json, expires_at_str = row
        expires_at = datetime.fromisoformat(expires_at_str)

        # Check if expired
        if datetime.now(timezone.utc) > expires_at:
            return None

        return json.loads(data_json)

    async def _cache_store(self, key: str, data: dict) -> None:
        """Store data in cache with TTL expiry."""
        conn = await self._get_connection()
        table_name = f"{self.source_name}_cache"

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self.ttl_seconds)

        await conn.execute(
            f"""
            INSERT OR REPLACE INTO {table_name}
            (key, data, fetched_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (key, json.dumps(data), now.isoformat(), expires_at.isoformat()),
        )
        await conn.commit()

    async def close(self) -> None:
        """Close database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None

    def _validate_response(self, data: dict, required_keys: list[str]) -> None:
        """Raise if required keys missing from response."""
        missing = [k for k in required_keys if k not in data or data[k] is None]
        if missing:
            raise GhostMarketApiError(
                f"{self.source_name}: missing required fields: {missing}"
            )

    # -------------------------------------------------------------------------
    # Subclass interface - override these
    # -------------------------------------------------------------------------

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL in seconds. Override in subclass."""
        raise NotImplementedError

    @property
    def source_name(self) -> str:
        """Human-readable source name. Override in subclass."""
        raise NotImplementedError

    async def fetch(self, query: dict) -> dict:  # noqa: ARG002
        """Cache-first fetch. Override in subclass.

        Args:
            query: Adapter-specific query params (interface contract).

        Workflow:
            1. Check cache (call _cache_lookup)
            2. On miss: call API/scrape
            3. Store in cache (call _cache_store)
            4. Return structured data
        """
        raise NotImplementedError

    async def execute_query(self, query: dict) -> list[dict]:
        """OSINT-compatible query interface.

        Bridges Ghost Market's fetch() to the OSINT execute_query() contract.
        Accepts either OSINT format {"type": str, "params": dict} or raw params.

        Args:
            query: dict with either:
                - OSINT format: {"type": str, "params": dict}
                - Raw format: adapter-specific params directly

        Returns:
            List of result dicts (wraps fetch() output in a list).
        """
        # Extract params from OSINT query format, or use query as-is
        params = query.get("params", query) if "params" in query else query
        result = await self.fetch(params)
        # Normalize to list[dict]
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return [result]
        return []
