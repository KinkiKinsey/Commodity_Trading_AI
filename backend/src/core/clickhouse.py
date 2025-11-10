from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List

import httpx


class ClickHouseError(RuntimeError):
    """Raised when the ClickHouse HTTP API cannot be reached or returns an error."""


@dataclass(frozen=True)
class ClickHouseConfig:
    url: str
    database: str
    username: str | None
    password: str | None
    timeout: float


# Global httpx client to reuse connections
_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    """Get or create a singleton httpx client for ClickHouse queries."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        cfg = get_clickhouse_config()
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(cfg.timeout, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )
    return _http_client


@lru_cache(maxsize=1)
def get_clickhouse_config() -> ClickHouseConfig:
    url = os.getenv("CLICKHOUSE_HTTP_URL", "http://localhost:18123").strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"http://{url}"
    database = os.getenv("CLICKHOUSE_DATABASE", "ctp").strip() or "ctp"
    username = os.getenv("CLICKHOUSE_USER") or None
    password = os.getenv("CLICKHOUSE_PASSWORD")
    if password is None:
        password = ""
    timeout = float(os.getenv("CLICKHOUSE_TIMEOUT_SECONDS", "5.0"))
    return ClickHouseConfig(url=url, database=database, username=username, password=password, timeout=timeout)


async def run_clickhouse_query(sql: str) -> List[Dict[str, Any]]:
    """
    Execute a SQL statement via the ClickHouse HTTP interface and return rows as dictionaries.
    """
    import logging
    logger = logging.getLogger(__name__)

    cfg = get_clickhouse_config()

    query = sql.strip()
    if not query.lower().endswith("format json"):
        query = f"{query}\nFORMAT JSON"

    params = {"database": cfg.database}
    auth = (cfg.username, cfg.password) if cfg.username or cfg.password else None

    client = _get_http_client()

    try:
        response = await client.post(cfg.url, params=params, content=query, auth=auth)
    except httpx.HTTPError as exc:  # pragma: no cover - network failure
        logger.error(f"ClickHouse HTTP error: {exc}")
        raise ClickHouseError(f"ClickHouse request failed: {exc}") from exc

    if response.status_code >= 400:
        raise ClickHouseError(f"ClickHouse responded with {response.status_code}: {response.text[:200]}")

    try:
        payload = response.json()
    except ValueError as exc:
        logger.error(f"ClickHouse response text (first 500 chars): {response.text[:500]}")
        raise ClickHouseError(f"Failed to decode ClickHouse response as JSON: {exc}. Response: {response.text[:200]}") from exc

    data = payload.get("data")
    if data is None:
        raise ClickHouseError("ClickHouse response missing 'data' key")
    return data
