from __future__ import annotations

import json
import logging
import os
import re
import time
import math
from collections import OrderedDict, deque
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Literal, Optional, TypedDict
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query

from src.core.clickhouse import ClickHouseError, run_clickhouse_query
from src.models.ctp import (
    CtpIndicatorDefinition,
    CtpIndicatorPoint,
    CtpIndicatorSeries,
    CtpKlineResponse,
    CtpRealtimeResponse,
    CtpSignal,
    SupportedInterval,
)
from src.models.pricing import PriceBar, PricingMetadata, QuoteLevel, RangeMetadata

router = APIRouter()
logger = logging.getLogger(__name__)

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
    """Fetch latest tick from ClickHouse (relay server disabled due to timeout issues)."""
    # Relay server disabled - directly use ClickHouse for better performance
    # Original relay URL: http://47.108.177.50:8080/md/tick/{symbol}
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


def _parse_indicator_metadata(raw_value: Any) -> Optional[Dict[str, Any]]:
    if not raw_value:
        return None
    if isinstance(raw_value, dict):
        return raw_value
    if isinstance(raw_value, str):
        try:
            parsed = json.loads(raw_value)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return None
    return None


def _coerce_updated_at(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    if value:
        try:
            return _parse_ts(str(value))
        except Exception:
            return datetime.now(timezone.utc)
    return datetime.now(timezone.utc)


async def _fetch_indicator_definitions() -> List[CtpIndicatorDefinition]:
    sql = """
        SELECT
            indicator_key,
            label,
            category,
            description,
            code,
            checksum,
            metadata_json,
            updated_at
        FROM ctp.ctp_indicators
        ORDER BY indicator_key
    """
    rows = await run_clickhouse_query(sql)
    definitions: List[CtpIndicatorDefinition] = []
    for row in rows:
        metadata = _parse_indicator_metadata(row.get("metadata_json"))
        try:
            definition = CtpIndicatorDefinition(
                key=str(row.get("indicator_key") or ""),
                label=str(row.get("label") or ""),
                category=str(row["category"]) if row.get("category") else None,
                description=str(row["description"]) if row.get("description") else None,
                code=str(row.get("code") or ""),
                checksum=str(row.get("checksum") or ""),
                metadata=metadata,
                updated_at=_coerce_updated_at(row.get("updated_at")),
            )
        except Exception as exc:
            logger.warning("Skipping invalid indicator row %s: %s", row.get("indicator_key"), exc)
            continue
        definitions.append(definition)
    return definitions


async def _fetch_indicator_series_from_table(symbol: str) -> List[CtpIndicatorSeries]:
    sql = f"""
        SELECT
            indicator_key,
            line_id,
            label,
            color,
            metadata_json,
            timestamp,
            value
        FROM ctp.ctp_indicator_series
        WHERE symbol = '{symbol}'
        ORDER BY indicator_key, line_id, timestamp
    """
    rows = await run_clickhouse_query(sql)
    grouped: Dict[tuple[str, str], Dict[str, Any]] = {}

    for row in rows:
        key = (str(row.get("indicator_key") or "").upper(), str(row.get("line_id") or ""))
        entry = grouped.get(key)
        metadata = _parse_indicator_metadata(row.get("metadata_json"))
        timestamp = _parse_ts(str(row.get("timestamp")))
        value = float(row.get("value") or 0.0)
        if entry is None:
            entry = {
                "indicator_key": key[0],
                "line_id": key[1],
                "label": str(row.get("label") or ""),
                "color": str(row.get("color") or ""),
                "metadata": metadata,
                "series": [],
            }
            grouped[key] = entry
        entry["series"].append(CtpIndicatorPoint(timestamp=timestamp, value=value))

    return [
        CtpIndicatorSeries(
            indicator_key=data["indicator_key"],
            line_id=data["line_id"],
            label=data["label"],
            color=data["color"],
            metadata=data["metadata"],
            series=data["series"],
        )
        for data in grouped.values()
        if data["series"]
    ]


def _series_from_points(
    indicator_key: str,
    line_id: str,
    label: str,
    color: str,
    points: List[tuple[datetime, float]],
) -> Optional[CtpIndicatorSeries]:
    if not points:
        return None
    return CtpIndicatorSeries(
        indicator_key=indicator_key,
        line_id=line_id,
        label=label,
        color=color,
        series=[CtpIndicatorPoint(timestamp=ts, value=float(f"{val:.5f}")) for ts, val in points],
    )


def _sma_points(bars: List[PriceBar], window: int) -> List[tuple[datetime, float]]:
    if window <= 1:
        return []
    buffer: deque[float] = deque()
    points: List[tuple[datetime, float]] = []
    running_sum = 0.0
    for bar in bars:
        buffer.append(bar.close)
        running_sum += bar.close
        if len(buffer) > window:
            running_sum -= buffer.popleft()
        if len(buffer) == window:
            points.append((bar.timestamp, running_sum / window))
    return points


def _bollinger_points(bars: List[PriceBar], window: int, multiplier: float) -> tuple[
    List[tuple[datetime, float]], List[tuple[datetime, float]]
]:
    if window <= 1:
        return ([], [])
    buffer: deque[float] = deque(maxlen=window)
    upper: List[tuple[datetime, float]] = []
    lower: List[tuple[datetime, float]] = []
    for bar in bars:
        buffer.append(bar.close)
        if len(buffer) < window:
            continue
        mean = sum(buffer) / window
        variance = sum((value - mean) ** 2 for value in buffer) / window
        std_dev = math.sqrt(max(variance, 0.0))
        upper.append((bar.timestamp, mean + multiplier * std_dev))
        lower.append((bar.timestamp, mean - multiplier * std_dev))
    return upper, lower


def _channel_points(bars: List[PriceBar], multiplier: float) -> tuple[
    List[tuple[datetime, float]], List[tuple[datetime, float]]
]:
    upper: List[tuple[datetime, float]] = []
    lower: List[tuple[datetime, float]] = []
    for bar in bars:
        range_size = max(bar.high - bar.low, 0.01)
        upper.append((bar.timestamp, bar.high + range_size * multiplier))
        lower.append((bar.timestamp, bar.low - range_size * multiplier))
    return upper, lower


IndicatorBuilder = Callable[[List[PriceBar], str], List[CtpIndicatorSeries]]


def _build_mlma_series(bars: List[PriceBar], indicator_key: str) -> List[CtpIndicatorSeries]:
    points = _sma_points(bars, window=12)
    series = _series_from_points(indicator_key, "mlma", "ML Moving Avg (12)", "#0ea5e9", points)
    return [series] if series else []


def _build_longterm_series(bars: List[PriceBar], indicator_key: str) -> List[CtpIndicatorSeries]:
    points = _sma_points(bars, window=26)
    series = _series_from_points(indicator_key, "longterm", "Long-term SMA (26)", "#f97316", points)
    return [series] if series else []


def _build_bband_series(bars: List[PriceBar], indicator_key: str) -> List[CtpIndicatorSeries]:
    upper_points, lower_points = _bollinger_points(bars, window=20, multiplier=2.0)
    upper = _series_from_points(indicator_key, "bband_upper", "Bollinger Upper", "#38bdf8", upper_points)
    lower = _series_from_points(indicator_key, "bband_lower", "Bollinger Lower", "#38bdf8", lower_points)
    return [series for series in (upper, lower) if series]


def _build_bsside_series(bars: List[PriceBar], indicator_key: str) -> List[CtpIndicatorSeries]:
    upper_points, lower_points = _channel_points(bars, multiplier=0.35)
    upper = _series_from_points(indicator_key, "bsside_upper", "Liquidity Upper", "#f97316", upper_points)
    lower = _series_from_points(indicator_key, "bsside_lower", "Liquidity Lower", "#f97316", lower_points)
    return [series for series in (upper, lower) if series]


def _build_smc_series(bars: List[PriceBar], indicator_key: str) -> List[CtpIndicatorSeries]:
    upper_points, lower_points = _channel_points(bars, multiplier=0.18)
    upper = _series_from_points(indicator_key, "smc_upper", "SMC Supply", "#22c55e", upper_points)
    lower = _series_from_points(indicator_key, "smc_lower", "SMC Demand", "#22c55e", lower_points)
    return [series for series in (upper, lower) if series]


INDICATOR_BUILDERS: Dict[str, IndicatorBuilder] = {
    "MLMA": _build_mlma_series,
    "LONGTERM": _build_longterm_series,
    "BBAND": _build_bband_series,
    "BSSIDE": _build_bsside_series,
    "SMC": _build_smc_series,
}


def _build_indicator_series(
    definitions: List[CtpIndicatorDefinition],
    bars: List[PriceBar],
) -> List[CtpIndicatorSeries]:
    if not bars:
        return []

    keys = [definition.key.upper() for definition in definitions] or list(INDICATOR_BUILDERS.keys())
    seen: set[str] = set()
    series: List[CtpIndicatorSeries] = []

    for key in keys:
        normalized = key.upper()
        if normalized in seen:
            continue
        builder = INDICATOR_BUILDERS.get(normalized)
        if not builder:
            continue
        seen.add(normalized)
        series.extend(builder(bars, normalized))
    return series


def _build_signals(symbol: str, bars: List[PriceBar], indicator_series: List[CtpIndicatorSeries]) -> List[CtpSignal]:
    if not bars:
        return []
    mlma_series = next(
        (series for series in indicator_series if series.indicator_key.upper() == "MLMA" and series.series),
        None,
    )
    if not mlma_series:
        return []

    ma_values = {point.timestamp: point.value for point in mlma_series.series}
    prev_diff: Optional[float] = None
    signals: List[CtpSignal] = []

    def build_signal(bar: PriceBar, signal_type: Literal["buy", "sell"], description: str) -> CtpSignal:
        trend = "bullish" if signal_type == "buy" else "bearish"
        return CtpSignal(
            signal_id=f"{symbol}-{int(bar.timestamp.timestamp())}-{signal_type}-{uuid4().hex[:6]}",
            signal_type=signal_type,
            timestamp=bar.timestamp,
            price=bar.close,
            trend=trend,
            source="CTP derived",
            description=description,
            confidence=0.6,
        )

    for bar in bars:
        ma_value = ma_values.get(bar.timestamp)
        if ma_value is None:
            continue
        diff = bar.close - ma_value
        if prev_diff is not None:
            if diff >= 0 and prev_diff < 0:
                signals.append(build_signal(bar, "buy", "价格上穿 MLMA"))
            elif diff <= 0 and prev_diff > 0:
                signals.append(build_signal(bar, "sell", "价格下穿 MLMA"))
        prev_diff = diff

    return signals[-8:]


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

    indicators: List[CtpIndicatorDefinition] = []
    try:
        indicators = await _fetch_indicator_definitions()
    except ClickHouseError as exc:
        logger.warning("Failed to load indicator definitions: %s", exc)

    indicator_series = await _fetch_indicator_series_from_table(normalized_symbol)
    if not indicator_series:
        indicator_series = _build_indicator_series(indicators, bars)
    signals = _build_signals(normalized_symbol, bars, indicator_series)

    return CtpKlineResponse(
        symbol=normalized_symbol,
        interval=interval,
        range=range_meta,
        bars=bars,
        metadata=metadata,
        indicators=indicators,
        indicator_series=indicator_series,
        signals=signals,
    )


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
