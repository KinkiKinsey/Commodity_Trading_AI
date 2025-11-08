from __future__ import annotations

from datetime import datetime
from typing import Literal, List, Optional

from pydantic import BaseModel, Field

from .pricing import PriceBar, RangeMetadata, PricingMetadata, QuoteLevel


SupportedInterval = Literal["1m", "5m", "15m", "1h"]


class CtpKlineResponse(BaseModel):
    symbol: str = Field(..., description="CTP instrument identifier, e.g. CL2512-NYM")
    interval: SupportedInterval
    range: RangeMetadata
    bars: List[PriceBar]
    metadata: PricingMetadata


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
