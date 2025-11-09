"""Compute indicator series from ClickHouse bars and upsert into ctp.ctp_indicator_series."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List

import clickhouse_connect  # type: ignore\nfrom urllib.parse import urlparse

UTC = timezone.utc


@dataclass
class PriceBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


def fetch_bars(client, symbol: str, limit: int) -> List[PriceBar]:
    query = f"""
        SELECT ts, open, high, low, close
        FROM ctp.ctp_bars_1m
        WHERE symbol = '{symbol}'
        ORDER BY ts DESC
        LIMIT {limit}
    """
    rows = client.query(query).result_rows  # type: ignore[attr-defined]
    return [
        PriceBar(
            timestamp=row[0].replace(tzinfo=UTC),
            open=float(row[1]),
            high=float(row[2]),
            low=float(row[3]),
            close=float(row[4]),
        )
        for row in rows
    ][::-1]


def sma(points: List[PriceBar], window: int) -> List[tuple[datetime, float]]:
    values: List[tuple[datetime, float]] = []
    buffer: List[float] = []
    running = 0.0
    for bar in points:
        buffer.append(bar.close)
        running += bar.close
        if len(buffer) > window:
            running -= buffer.pop(0)
        if len(buffer) == window:
            values.append((bar.timestamp, running / window))
    return values


def channel(points: List[PriceBar], multiplier: float) -> tuple[List[tuple[datetime, float]], List[tuple[datetime, float]]]:
    upper: List[tuple[datetime, float]] = []
    lower: List[tuple[datetime, float]] = []
    for bar in points:
        rng = max(bar.high - bar.low, 0.01)
        upper.append((bar.timestamp, bar.high + rng * multiplier))
        lower.append((bar.timestamp, bar.low - rng * multiplier))
    return upper, lower


def to_rows(symbol: str, indicator_key: str, line_id: str, label: str, color: str, data: Iterable[tuple[datetime, float]]) -> List[List[object]]:
    now = datetime.now(UTC)
    metadata = json.dumps({"source": "derived"})
    return [
        [symbol, indicator_key, line_id, label, color, metadata, ts, value, now]
        for ts, value in data
    ]


INDICATOR_MAP = {
    "MLMA": {
        "lines": lambda bars: [("mlma", "ML Moving Avg (12)", "#0ea5e9", sma(bars, 12))],
    },
    "LONGTERM": {
        "lines": lambda bars: [("longterm", "Long-term SMA (26)", "#f97316", sma(bars, 26))],
    },
    "BSSIDE": {
        "lines": lambda bars: [
            ("bsside_upper", "Liquidity Upper", "#f97316", channel(bars, 0.35)[0]),
            ("bsside_lower", "Liquidity Lower", "#f97316", channel(bars, 0.35)[1]),
        ],
    },
    "SMC": {
        "lines": lambda bars: [
            ("smc_upper", "SMC Supply", "#22c55e", channel(bars, 0.18)[0]),
            ("smc_lower", "SMC Demand", "#22c55e", channel(bars, 0.18)[1]),
        ],
    },
}


def upsert_series(client, rows: List[List[object]]):
    if not rows:
        return
    client.insert(
        "ctp.ctp_indicator_series",
        rows,
        column_names=[
            "symbol",
            "indicator_key",
            "line_id",
            "label",
            "color",
            "metadata_json",
            "timestamp",
            "value",
            "updated_at",
        ],
    )


def parse_symbols(value: str) -> List[str]:
    return [item.strip().upper() for item in value.split(",") if item.strip()]


def main():
    parser = argparse.ArgumentParser(description="Backfill indicator series into ClickHouse")
    parser.add_argument("--symbols", type=str, required=True, help="Comma separated symbols, e.g. CL2512-NYM,CL2601-NYM")
    parser.add_argument("--bars", type=int, default=1500, help="Number of 1m bars to use per symbol")
    parser.add_argument("--url", type=str, default="http://127.0.0.1:18123")
    parser.add_argument("--user", type=str, default="default")
    parser.add_argument("--password", type=str, default="")
    args = parser.parse_args()

    parsed = urlparse(args.url)\nhost = parsed.hostname or "localhost"\nport = parsed.port or 8123\nclient = clickhouse_connect.get_client(host=host, port=port, username=args.user, password=args.password)  # type: ignore
    symbols = parse_symbols(args.symbols)
    for symbol in symbols:
        bars = fetch_bars(client, symbol, args.bars)
        if not bars:
            print(f"[warn] no bars for {symbol}")
            continue
        all_rows: List[List[object]] = []
        for indicator_key, spec in INDICATOR_MAP.items():
            for line_id, label, color, series in spec["lines"](bars):
                all_rows.extend(to_rows(symbol, indicator_key, line_id, label, color, series))
        upsert_series(client, all_rows)
        print(f"[ok] upserted {len(all_rows)} rows for {symbol}")


if __name__ == "__main__":
    main()
