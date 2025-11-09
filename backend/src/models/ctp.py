from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from .pricing import PriceBar, PricingMetadata, QuoteLevel, RangeMetadata


SupportedInterval = Literal["1m", "5m", "15m", "1h"]


class CtpIndicatorDefinition(BaseModel):
    key: str = Field(..., alias="indicator_key", description="Stable slug for the indicator")
    label: str
    category: Optional[str] = None
    description: Optional[str] = None
    code: str
    checksum: str
    metadata: Optional[Dict[str, Any]] = None
    updated_at: datetime


class CtpIndicatorPoint(BaseModel):
    timestamp: datetime
    value: float


class CtpIndicatorSeries(BaseModel):
    indicator_key: str
    line_id: str
    label: str
    color: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    series: List[CtpIndicatorPoint]


class CtpSignal(BaseModel):
    signal_id: str
    signal_type: Literal["buy", "sell"]
    timestamp: datetime
    price: float
    trend: Literal["bullish", "bearish"]
    source: str
    description: Optional[str] = None
    confidence: Optional[float] = None


class CtpKlineResponse(BaseModel):
    symbol: str = Field(..., description="CTP instrument identifier, e.g. CL2512-NYM")
    interval: SupportedInterval
    range: RangeMetadata
    bars: List[PriceBar]
    metadata: PricingMetadata
    indicators: List[CtpIndicatorDefinition] = Field(default_factory=list)
    indicator_series: List[CtpIndicatorSeries] = Field(default_factory=list)
    signals: List[CtpSignal] = Field(default_factory=list)


class CtpRealtimeResponse(BaseModel):
    symbol: str
    local_timestamp: datetime
    exchange_timestamp: Optional[datetime] = None
    update_time: str
    update_millisec: int
    last_price: float
    bid: QuoteLevel
    ask: QuoteLevel
    volume: float
    metadata: PricingMetadata
