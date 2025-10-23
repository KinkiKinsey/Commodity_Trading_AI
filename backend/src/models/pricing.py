"""
Pydantic models for the `/api/pricing/kline` endpoint.

These models mirror the JSON schema stored under
`docs/api/schemas/pricing_kline.schema.json` and provide typing for the
FastAPI layer.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class PriceBar(BaseModel):
    timestamp: datetime = Field(..., description="UTC timestamp of the bar")
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None


class TimeInterval(BaseModel):
    start_date: date
    end_date: date
    trend: Literal["BULLISH", "BEARISH"]


class TimestampValue(BaseModel):
    timestamp: datetime
    value: float


class IntervalReference(BaseModel):
    start_date: date
    end_date: date


class TrendPoint(BaseModel):
    timestamp: datetime
    price: float
    trend: Literal["BULLISH", "BEARISH"]
    event_type: Literal["reversal", "continuation"]
    interval_ref: Optional[IntervalReference] = None


class MovingAverageParameters(BaseModel):
    window: int
    sigma: float
    mult: float


class MovingAveragePayload(BaseModel):
    summary: str
    time_intervals: List[TimeInterval]
    line: List[TimestampValue]
    upper_band: List[TimestampValue]
    lower_band: List[TimestampValue]
    trend_points: List[TrendPoint]
    parameters: MovingAverageParameters


class IndicatorSeriesPoint(BaseModel):
    timestamp: datetime
    value: float


class IndicatorPayload(BaseModel):
    name: str
    description: Optional[str] = None
    type: Optional[Literal["trend", "momentum", "volatility", "volume"]] = None
    summary: Optional[str] = None
    series: List[IndicatorSeriesPoint]


class SignalPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    signal_id: str = Field(..., alias="signal_id")
    signal_type: Literal["buy", "sell"]
    timestamp: datetime
    price: float
    trend: Literal["BULLISH", "BEARISH"]
    source: str
    interval_ref: Optional[IntervalReference] = None
    linked_news_ids: List[str] = Field(default_factory=list)


class SourceMetadata(BaseModel):
    exchange: str
    instrument_type: Literal["futures", "spot", "etf", "index"]
    currency: Optional[str] = None
    data_vendor: Optional[str] = None


class RangeMetadata(BaseModel):
    start: datetime
    end: datetime
    count: int


class PricingMetadata(BaseModel):
    fetched_at: datetime
    data_latency_seconds: float
    source_latency_seconds: Optional[float] = None
    notes: Optional[str] = None


class PricingKlineResponse(BaseModel):
    ticker: str
    display_name: str
    timezone: str
    range: RangeMetadata
    series: List[PriceBar]
    ml_moving_average: MovingAveragePayload
    signals: List[SignalPayload]
    indicators: List[IndicatorPayload]
    source: SourceMetadata
    metadata: PricingMetadata
    request_id: Optional[str] = None
    sector: Optional[str] = None
    errors: List[dict] = Field(default_factory=list)


class IndicatorResponse(BaseModel):
    ticker: str
    timezone: str
    range: RangeMetadata
    indicators: Dict[str, dict]
