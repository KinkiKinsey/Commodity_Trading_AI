from __future__ import annotations

import re
import os
import time
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Dict, List, Optional, TypedDict

from fastapi import APIRouter, HTTPException, Query

from src.core.clickhouse import ClickHouseError, run_clickhouse_query
from src.models.ctp import CtpKlineResponse, CtpRealtimeResponse, SupportedInterval
from src.models.pricing import PriceBar, RangeMetadata, PricingMetadata, QuoteLevel

router = APIRouter()

SYMBOL_PATTERN = re.compile(r"^[A-Z0-9_.-]{2,32}$")
INTERVAL_CONFIG: Dict[SupportedInterval, Dict[str, int]] = {
    "1m": {"minutes": 1, "limit_factor": 1},
    "5m": {"minutes": 5, "limit_factor": 5},
    "15m": {"minutes": 15, "limit_factor": 15},
    "1h": {"minutes": 60, "limit_factor": 75},  # 75 ensures enough 1m bars per hour
}
MAX_BASE_ROWS = 20000
REALTIME_CACHE_SECONDS = max(0.1, float(os.getenv("CTP_REALTIME_CACHE_SECONDS", "1.0")))
REALTIME_MIN_INTERVAL_SECONDS = max(0.0, float(os.getenv("CTP_REALTIME_MIN_INTERVAL_SECONDS", "0.3")))


class TickCacheEntry(TypedDict):
    payload: CtpRealtimeResponse
    expires_at: float
    next_fetch_after: float


_REALTIME_CACHE: Dict[str, TickCacheEntry] = {}


def _normalize_symbol(symbol: str) -> str:
    candidate = symbol.strip().upper()
    if not SYMBOL_PATTERN.fullmatch(candidate):
        raise HTTPException(status_code=400, detail="symbol must match ^[A-Z0-9_.-]{2,32}$")
    return candidate


def _parse_ts(value: str) -> datetime:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if not isinstance(value, str):
        raise ValueError(f"Unexpected timestamp value: {value!r}")
    normalized = value.replace(" ", "T")
    if normalized.endswith("Z"):
        dt = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    else:
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _floor_to_bucket(ts: datetime, minutes: int) -> datetime:
    if minutes <= 1:
        return ts.replace(second=0, microsecond=0)
    seconds = int(ts.timestamp())
    bucket = (seconds // (minutes * 60)) * (minutes * 60)
    return datetime.fromtimestamp(bucket, tz=timezone.utc)


def _aggregate_rows(rows: List[dict], minutes: int, desired_count: int) -> List[PriceBar]:
    if not rows:
        return []

    ordered = list(reversed(rows))  # rows are fetched DESC, we need chronological order
    buckets: "OrderedDict[datetime, dict]" = OrderedDict()

    for row in ordered:
        ts = _parse_ts(row["ts"])
        bucket = _floor_to_bucket(ts, minutes)
        volume = float(row.get("volume") or 0.0)
        open_price = float(row["open"])
        high_price = float(row["high"])
        low_price = float(row["low"])
        close_price = float(row["close"])

        entry = buckets.get(bucket)
        if entry is None:
            entry = {
                "timestamp": bucket,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume,
            }
            buckets[bucket] = entry
        else:
            entry["high"] = max(entry["high"], high_price)
            entry["low"] = min(entry["low"], low_price)
            entry["close"] = close_price
            entry["volume"] += volume

    bars = [
        PriceBar(
            timestamp=data["timestamp"],
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            volume=data["volume"],
        )
        for data in buckets.values()
    ]
    if len(bars) > desired_count:
        bars = bars[-desired_count:]
    return bars


async def _fetch_base_rows(symbol: str, limit: int) -> List[dict]:
    sql = f"""
        SELECT
            symbol,
            ts,
            open,
            high,
            low,
            close,
            volume
        FROM ctp.ctp_bars_1m
        WHERE symbol = '{symbol}'
        ORDER BY ts DESC
        LIMIT {limit}
    """
    return await run_clickhouse_query(sql)


async def _fetch_latest_tick(symbol: str) -> Optional[dict]:
    sql = f"""
        SELECT
            symbol,
            local_ts,
            exchange_ts,
            update_time,
            update_millisec,
            last_price,
            bid_price1,
            bid_volume1,
            ask_price1,
            ask_volume1,
            volume
        FROM ctp.ctp_ticks
        WHERE symbol = '{symbol}'
        ORDER BY local_ts DESC
        LIMIT 1
    """
    rows = await run_clickhouse_query(sql)
    return rows[0] if rows else None


def _build_realtime_response(symbol: str, row: dict) -> CtpRealtimeResponse:
    local_ts = _parse_ts(row["local_ts"])
    exchange_ts = _parse_ts(row["exchange_ts"]) if row.get("exchange_ts") else None
    fetched_at = datetime.now(timezone.utc)
    latency = max(0.0, (fetched_at - local_ts).total_seconds())

    metadata = PricingMetadata(
        fetched_at=fetched_at,
        data_latency_seconds=latency,
        source_latency_seconds=None,
        notes="ClickHouse latest tick",
    )

    bid = QuoteLevel(price=float(row.get("bid_price1") or 0.0), volume=float(row.get("bid_volume1") or 0.0))
    ask = QuoteLevel(price=float(row.get("ask_price1") or 0.0), volume=float(row.get("ask_volume1") or 0.0))

    return CtpRealtimeResponse(
        symbol=symbol,
        local_timestamp=local_ts,
        exchange_timestamp=exchange_ts,
        update_time=str(row.get("update_time") or ""),
        update_millisec=int(row.get("update_millisec") or 0),
        last_price=float(row.get("last_price") or 0.0),
        bid=bid,
        ask=ask,
        volume=float(row.get("volume") or 0.0),
        metadata=metadata,
    )


@router.get(
    "/api/ctp/kline",
    response_model=CtpKlineResponse,
    summary="Aggregated CTP K-line bars sourced from ClickHouse",
)
async def get_ctp_kline(
    symbol: str = Query(..., description="CTP instrument identifier, e.g. CL2512-NYM"),
    interval: SupportedInterval = Query("1m", description="Bar interval"),
    count: int = Query(200, ge=1, le=1000, description="Number of bars to return"),
) -> CtpKlineResponse:
    normalized_symbol = _normalize_symbol(symbol)
    config = INTERVAL_CONFIG[interval]
    limit_factor = max(1, config["limit_factor"])
    base_limit = min(MAX_BASE_ROWS, max(count * limit_factor * 2, count))

    try:
        base_rows = await _fetch_base_rows(normalized_symbol, base_limit)
    except ClickHouseError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not base_rows:
        raise HTTPException(status_code=404, detail=f"No bars available for {normalized_symbol}")

    bars = _aggregate_rows(base_rows, config["minutes"], count)
    if not bars:
        raise HTTPException(status_code=404, detail=f"Insufficient data for interval {interval}")

    fetched_at = datetime.now(timezone.utc)
    latency = max(0.0, (fetched_at - bars[-1].timestamp).total_seconds())

    range_meta = RangeMetadata(start=bars[0].timestamp, end=bars[-1].timestamp, count=len(bars))
    metadata = PricingMetadata(
        fetched_at=fetched_at,
        data_latency_seconds=latency,
        source_latency_seconds=None,
        notes=f"ClickHouse interval={interval}",
    )

    return CtpKlineResponse(symbol=normalized_symbol, interval=interval, range=range_meta, bars=bars, metadata=metadata)


@router.get(
    "/api/ctp/realtime",
    response_model=CtpRealtimeResponse,
    summary="Latest CTP tick sourced from ClickHouse",
)
async def get_ctp_realtime(
    symbol: str = Query(..., description="CTP instrument identifier, e.g. CL2512-NYM"),
) -> CtpRealtimeResponse:
    normalized_symbol = _normalize_symbol(symbol)
    now_ts = time.time()
    cache_entry = _REALTIME_CACHE.get(normalized_symbol)

    if cache_entry and cache_entry["expires_at"] > now_ts:
        return cache_entry["payload"]

    if cache_entry and cache_entry["next_fetch_after"] > now_ts:
        return cache_entry["payload"]

    try:
        row = await _fetch_latest_tick(normalized_symbol)
    except ClickHouseError as exc:
        if cache_entry:
            return cache_entry["payload"]
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not row:
        if cache_entry:
            return cache_entry["payload"]
        raise HTTPException(status_code=404, detail=f"No tick available for {normalized_symbol}")

    payload = _build_realtime_response(normalized_symbol, row)
    _REALTIME_CACHE[normalized_symbol] = {
        "payload": payload,
        "expires_at": now_ts + REALTIME_CACHE_SECONDS,
        "next_fetch_after": now_ts + REALTIME_MIN_INTERVAL_SECONDS,
    }
    return payload


@router.get("/api/ctp/healthz", summary="ClickHouse connectivity and recency check")
async def get_ctp_health() -> Dict[str, object]:
    try:
        rows = await run_clickhouse_query(
            """
            SELECT
                max(local_ts) AS latest_ts,
                count() AS total_rows
            FROM ctp.ctp_ticks
            """
        )
    except ClickHouseError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    latest_raw = rows[0].get("latest_ts") if rows else None
    total_rows = int(rows[0].get("total_rows") or 0) if rows else 0
    latest_ts = _parse_ts(latest_raw) if latest_raw else None
    freshness_seconds = None
    if latest_ts:
        freshness_seconds = max(0.0, (datetime.now(timezone.utc) - latest_ts).total_seconds())

    status = "ok" if total_rows > 0 else "empty"
    return {
        "status": status,
        "rows": total_rows,
        "latest_timestamp": latest_ts.isoformat() if latest_ts else None,
        "freshness_seconds": freshness_seconds,
    }
