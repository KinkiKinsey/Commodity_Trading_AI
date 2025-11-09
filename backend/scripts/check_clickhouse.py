"""Quick connectivity check for ClickHouse using backend settings."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.src.core.clickhouse import ClickHouseError, get_clickhouse_config, run_clickhouse_query  # type: ignore


def format_row(row: dict[str, Any]) -> str:
    symbol = row.get("symbol")
    ts = row.get("local_ts") or row.get("ts")
    price = row.get("last_price") or row.get("close")
    return f"{symbol}\t{ts}\t{price}"


async def main() -> None:
    cfg = get_clickhouse_config()
    print(f"ClickHouse URL : {cfg.url}")
    print(f"Database       : {cfg.database}")
    print(f"Username       : {cfg.username or '(default)'}")

    try:
        rows = await run_clickhouse_query(
            """
            SELECT symbol, local_ts, last_price
            FROM ctp.ctp_ticks
            ORDER BY local_ts DESC
            LIMIT 5
            """
        )
    except ClickHouseError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1) from exc

    if not rows:
        print("Warning: no rows returned from ctp.ctp_ticks")
        return

    print("\nLatest ticks:")
    for row in rows:
        print("  ", format_row(row))


if __name__ == "__main__":
    asyncio.run(main())
