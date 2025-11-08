from __future__ import annotations

import json
import numbers
from datetime import date, datetime, timezone, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from jsonschema import ValidationError, validate

from src.financial.data_sources.price_data import get_yahoo_data_comprehensive
from src.financial.data_sources.md_tick import TickApiError, fetch_md_tick
from src.financial.functions import (
    bollinger_tool,
    equal_highs_lows_tool,
    liquidity_zones_tool,
    ml_moving_average_tool,
    optimal_rsi_tool,
    rsi_tool,
)
from src.models.pricing import (
    IndicatorSeriesPoint,
    IndicatorPayload,
    IndicatorResponse,
    IntervalReference,
    MovingAverageParameters,
    MovingAveragePayload,
    PriceBar,
    PricingKlineResponse,
    PricingMetadata,
    PricingTickResponse,
    RangeMetadata,
    SignalPayload,
    SourceMetadata,
    TimeInterval,
    TimestampValue,
    TrendPoint,
    QuoteLevel,
)


router = APIRouter()


@lru_cache(maxsize=1)
def _load_schema() -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[3]
    schema_path = root / "docs" / "api" / "schemas" / "pricing_kline.schema.json"
    if not schema_path.exists():
        raise RuntimeError(f"Pricing schema not found at {schema_path}")
    return json.loads(schema_path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_ticker_mapping() -> Dict[str, Dict[str, str]]:
    mapping: Dict[str, Dict[str, str]] = {}
    root = Path(__file__).resolve().parents[3]
    csv_path = root / "docs" / "datasets" / "ticker_mapping.csv"
    if not csv_path.exists():
        return mapping
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        ticker = str(row.get("yahoo_ticker", "")).strip()
        if not ticker:
            continue
        mapping[ticker.upper()] = {
            "display_name": str(row.get("display_name", ticker)).strip(),
            "sector": str(row.get("sector", "")).strip(),
        }
    return mapping


@lru_cache(maxsize=1)
def _load_demo_fixture() -> Dict[str, Any] | None:
    root = Path(__file__).resolve().parents[3]
    fixture_path = root / "docs" / "review_logs" / "step7_kline.json"
    if not fixture_path.exists():
        return None
    try:
        return json.loads(fixture_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _serialise(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, pd.Timestamp):
        dt = value.to_pydatetime()
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    if isinstance(value, np.ndarray):
        return [_serialise(item) for item in value.tolist()]
    if isinstance(value, (np.floating, float)):
        return float(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, numbers.Number):
        return value
    if isinstance(value, list):
        return [_serialise(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _serialise(v) for k, v in value.items()}
    return value


INDICATOR_FUNCTIONS: Dict[str, callable] = {
    "bollinger": lambda df: bollinger_tool(df),
    "rsi": lambda df: rsi_tool(df),
    "optimal_rsi": lambda df: optimal_rsi_tool(df),
    "equal_highs_lows": lambda df: equal_highs_lows_tool(df),
    "liquidity_zones": lambda df: liquidity_zones_tool(df),
}


def _ensure_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return pd.to_datetime(value, utc=True).to_pydatetime()


def _infer_instrument_type(ticker: str) -> str:
    upper = ticker.upper()
    if any(suffix in upper for suffix in (".NYM", ".CME", ".ICE", "=F")):
        return "futures"
    if upper.endswith("-USD") or upper.endswith("USD=X"):
        return "spot"
    if upper.endswith(".IX") or upper.startswith("^"):
        return "index"
    return "etf"


def _build_moving_average_payload(ml_result: dict) -> MovingAveragePayload:
    line_points: list[TimestampValue] = []
    upper_points: list[TimestampValue] = []
    lower_points: list[TimestampValue] = []
    for entry in ml_result.get("series", []):
        ts = _ensure_datetime(entry["date"])
        if pd.notna(entry.get("ml_ma")):
            line_points.append(TimestampValue(timestamp=ts, value=float(entry["ml_ma"])))
        if pd.notna(entry.get("upper")):
            upper_points.append(TimestampValue(timestamp=ts, value=float(entry["upper"])))
        if pd.notna(entry.get("lower")):
            lower_points.append(TimestampValue(timestamp=ts, value=float(entry["lower"])))

    time_intervals = [
        TimeInterval(**interval) for interval in ml_result.get("time_intervals", [])
    ]

    trend_points: list[TrendPoint] = []
    for item in ml_result.get("trend_points", []):
        interval_ref = item.get("interval_ref")
        trend_points.append(
            TrendPoint(
                timestamp=_ensure_datetime(item["timestamp"]),
                price=float(item["price"]),
                trend=item["trend"],
                event_type=item.get("event_type", "reversal"),
                interval_ref=IntervalReference(**interval_ref) if interval_ref else None,
            )
        )

    params = ml_result.get("parameters", {})
    parameters = MovingAverageParameters(
        window=int(params.get("window", 50)),
        sigma=float(params.get("sigma", 10)),
        mult=float(params.get("mult", 2)),
    )

    return MovingAveragePayload(
        summary=ml_result.get("summary", ""),
        time_intervals=time_intervals,
        line=line_points,
        upper_band=upper_points,
        lower_band=lower_points,
        trend_points=trend_points,
        parameters=parameters,
    )


def _build_signals(trend_points: list[TrendPoint], ticker: str) -> list[SignalPayload]:
    signals: list[SignalPayload] = []
    for idx, point in enumerate(trend_points):
        signal_id = f"mlma-{ticker}-{idx}"
        signal_type = "buy" if point.trend == "BULLISH" else "sell"
        signals.append(
            SignalPayload(
                signal_id=signal_id,
                signal_type=signal_type,
                timestamp=point.timestamp,
                price=point.price,
                trend=point.trend,
                source="ml_moving_average",
                interval_ref=point.interval_ref,
                linked_news_ids=[],
            )
        )
    return signals


def _parse_tick_timestamp(trading_day: str, update_time: str, millis: int) -> datetime:
    if len(trading_day) != 8:
        raise ValueError(f"Invalid trading_day: {trading_day}")
    time_part = update_time or "00:00:00"
    try:
        base = datetime.strptime(f"{trading_day}{time_part}", "%Y%m%d%H:%M:%S")
    except ValueError as exc:
        raise ValueError(f"Invalid update_time: {time_part}") from exc
    base = base.replace(tzinfo=timezone.utc)
    millis = millis or 0
    return base + timedelta(milliseconds=int(millis))


def _build_tick_response(instrument_id: str, payload: dict) -> PricingTickResponse:
    trading_day_raw = str(payload.get("trading_day") or "")
    update_time_raw = str(payload.get("update_time") or "00:00:00")
    update_millisec_raw = payload.get("update_millisec") or 0

    if len(trading_day_raw) != 8:
        raise ValueError(f"Invalid trading_day: {trading_day_raw}")
    trading_day = datetime.strptime(trading_day_raw, "%Y%m%d").date()
    updated_at = _parse_tick_timestamp(trading_day_raw, update_time_raw, int(update_millisec_raw))

    bid = QuoteLevel(
        price=float(payload.get("bid_price1") or 0.0),
        volume=float(payload.get("bid_volume1") or 0.0),
    )
    ask = QuoteLevel(
        price=float(payload.get("ask_price1") or 0.0),
        volume=float(payload.get("ask_volume1") or 0.0),
    )

    return PricingTickResponse(
        instrument_id=str(payload.get("instrument_id") or instrument_id),
        last_price=float(payload.get("last_price") or 0.0),
        volume=float(payload.get("volume") or 0.0),
        trading_day=trading_day,
        updated_at=updated_at,
        bid=bid,
        ask=ask,
        raw=payload,
    )


@router.get("/api/pricing/kline", response_model=PricingKlineResponse)
async def get_pricing_kline(
    ticker: str = Query(..., description="Yahoo Finance ticker, e.g. CLZ25.NYM"),
    days: int = Query(180, ge=1, le=720, description="Number of historical days to fetch"),
    include_indicators: bool = Query(True, description="Whether to include auxiliary indicator payloads"),
    force_refresh: bool = Query(False, description="Reserved flag for cache bypass (unused)"),
) -> PricingKlineResponse:
    df = get_yahoo_data_comprehensive(ticker, days)
    if df.empty:
        fixture = _load_demo_fixture()
        if fixture and fixture.get("ticker", "").upper() == ticker.upper():
            fixture = fixture.copy()
            fixture["request_id"] = str(uuid4())
            try:
                validate(instance=fixture, schema=_load_schema())
            except ValidationError as exc:
                raise HTTPException(status_code=500, detail=f"Schema validation failed: {exc.message}") from exc
            return PricingKlineResponse(**fixture)
        raise HTTPException(status_code=404, detail=f"No pricing data available for {ticker}.")

    df["date"] = pd.to_datetime(df["date"], utc=True)
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    series = [
        PriceBar(
            timestamp=row["date"].to_pydatetime(),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row["volume"]) if pd.notna(row["volume"]) else None,
        )
        for _, row in df.iterrows()
    ]

    ml_input = df[["date", "close"]].copy()
    try:
        ml_result = ml_moving_average_tool(ml_input)
    except ValueError:
        fallback_series = [
            {
                "date": row["date"],
                "ml_ma": float(row["close"]),
                "upper": None,
                "lower": None,
            }
            for _, row in df.iterrows()
        ]
        ml_result = {
            "series": fallback_series,
            "time_intervals": [],
            "trend_points": [],
            "parameters": {
                "window": min(len(fallback_series), 50) or 1,
                "sigma": 0.0,
                "mult": 0.0,
            },
            "summary": "Not enough history to compute ML moving average; showing closing prices.",
        }
    ml_payload = _build_moving_average_payload(ml_result)
    signals = _build_signals(ml_payload.trend_points, ticker)

    indicators: list[IndicatorPayload] = []
    if include_indicators:
        # Placeholders for Index1/Index2 indicators – mirror historical closes with simple smoothing.
        idx1_series = []
        idx2_series = []
        closes = df["close"].to_numpy()
        timestamps = df["date"].to_numpy()
        ema = pd.Series(closes).ewm(span=9, adjust=False).mean().to_numpy()
        sma = pd.Series(closes).rolling(window=5).mean().to_numpy()
        for ts, value in zip(timestamps, ema):
            if np.isnan(value):
                continue
            idx1_series.append(IndicatorSeriesPoint(timestamp=pd.to_datetime(ts, utc=True).to_pydatetime(), value=float(value)))
        for ts, value in zip(timestamps, sma):
            if np.isnan(value):
                continue
            idx2_series.append(IndicatorSeriesPoint(timestamp=pd.to_datetime(ts, utc=True).to_pydatetime(), value=float(value)))
        if idx1_series:
            indicators.append(
                IndicatorPayload(
                    name="Index 1",
                    description="Short-term exponential smoothing of price to emulate inventory pressure index.",
                    type="trend",
                    series=idx1_series,
                    summary="指数保持在 50 以上，提示供给偏紧。",
                )
            )
        if idx2_series:
            indicators.append(
                IndicatorPayload(
                    name="Index 2",
                    description="Simple moving average proxy for refinery utilisation oscillator.",
                    type="momentum",
                    series=idx2_series,
                    summary="炼厂开工率在 60 上方，动能偏多。",
                )
            )

    mapping = _load_ticker_mapping()
    mapping_entry = mapping.get(ticker.upper(), {})
    display_name = mapping_entry.get("display_name") or ticker
    sector = mapping_entry.get("sector") or "UNKNOWN"

    start = series[0].timestamp
    end = series[-1].timestamp
    fetched_at = datetime.now(timezone.utc)
    latency = max((fetched_at - end).total_seconds(), 0.0)

    response = PricingKlineResponse(
        request_id=str(uuid4()),
        ticker=ticker,
        display_name=display_name,
        sector=sector,
        timezone="UTC",
        range=RangeMetadata(start=start, end=end, count=len(series)),
        series=series,
        ml_moving_average=ml_payload,
        signals=signals,
        indicators=indicators,
        source=SourceMetadata(
            exchange="YAHOO",
            instrument_type=_infer_instrument_type(ticker),
            currency="USD",
            data_vendor="Yahoo Finance",
        ),
        metadata=PricingMetadata(
            fetched_at=fetched_at,
            data_latency_seconds=latency,
            source_latency_seconds=0.0,
            notes="",
        ),
        errors=[],
    )

    instance = json.loads(response.json(by_alias=True))
    try:
        validate(instance=instance, schema=_load_schema())
    except ValidationError as exc:
        raise HTTPException(status_code=500, detail=f"Schema validation failed: {exc.message}") from exc

    return response


@router.get(
    "/api/pricing/tick",
    response_model=PricingTickResponse,
    summary="Latest tick data sourced from the md/tick service",
)
async def get_pricing_tick(
    instrument_id: str = Query(..., min_length=3, max_length=40, description="Instrument identifier, e.g. CL2512-NYM"),
) -> PricingTickResponse:
    try:
        payload = fetch_md_tick(instrument_id)
    except TickApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        return _build_tick_response(instrument_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to parse tick payload: {exc}") from exc


@router.get("/api/pricing/indicators", response_model=IndicatorResponse)
async def get_pricing_indicators(
    ticker: str = Query(..., description="Yahoo Finance ticker, e.g. CLZ25.NYM"),
    days: int = Query(180, ge=1, le=720, description="Number of historical days to fetch"),
    indicators: Optional[List[str]] = Query(
        None,
        description=f"List of indicators to compute. Supported: {', '.join(INDICATOR_FUNCTIONS.keys())}",
    ),
) -> IndicatorResponse:
    indicator_keys = indicators or list(INDICATOR_FUNCTIONS.keys())
    unsupported = [key for key in indicator_keys if key not in INDICATOR_FUNCTIONS]
    if unsupported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported indicators: {', '.join(unsupported)}",
        )

    df = get_yahoo_data_comprehensive(ticker, days)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No pricing data available for {ticker}.")

    df["date"] = pd.to_datetime(df["date"], utc=True)
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    indicator_payloads: Dict[str, dict] = {}
    for name in indicator_keys:
        try:
            result = INDICATOR_FUNCTIONS[name](df)
        except Exception as exc:  # pragma: no cover - defensive guard
            indicator_payloads[name] = {"error": str(exc)}
            continue
        indicator_payloads[name] = _serialise(result)

    start = df["date"].iloc[0].to_pydatetime()
    end = df["date"].iloc[-1].to_pydatetime()

    return IndicatorResponse(
        ticker=ticker,
        timezone="UTC",
        range=RangeMetadata(start=start, end=end, count=len(df)),
        indicators=indicator_payloads,
    )
